import os
import re
import sys
import threading
import time
 
os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")   # steadier RTSP streams
import cv2
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
 
from core.detector import FireDetector, TemporalVerifier
from core.emergency import escalate
from core.models import Camera, Incident
 
 
def local_alarm():
    """Siren on the machine running the detector (Windows beep; terminal bell elsewhere)."""
    if sys.platform == "win32":
        import winsound
        for _ in range(8):
            winsound.Beep(880, 300)
            winsound.Beep(660, 300)
    else:
        print("\a" * 5)
 
 
def is_live(src):
    return isinstance(src, int) or str(src).lower().startswith(("rtsp://", "rtmp://", "http://", "https://"))
 
 
def hide_password(text):
    return re.sub(r"://[^/@]*@", "://***@", str(text))
 
 
class Command(BaseCommand):
    help = "Watch a camera / video and raise incidents when fire is confirmed."
 
    def add_arguments(self, p):
        p.add_argument("camera_id", type=int)
        p.add_argument("--weights", default="best_ckpt.pth")
        p.add_argument("--source", help="override the camera Source for this run only: video path, 0 (webcam) or rtsp://...")
        p.add_argument("--show", action="store_true", help="show a window with boxes (press q to quit)")
        p.add_argument("--loop", action="store_true", help="repeat a video file forever (default: stop at the end)")
        p.add_argument("--fps", type=float, default=None,
                       help="max frames per second to analyse (default: 3 for live streams, every frame for files)")
 
    def handle(self, *a, **o):
        try:
            cam = Camera.objects.get(pk=o["camera_id"])
        except Camera.DoesNotExist:
            raise CommandError(f"Camera {o['camera_id']} does not exist (check the ID in admin).")
        raw = (o["source"] or cam.source).strip().strip('"')
        src = int(raw) if raw.isdigit() else raw
        live = is_live(src)
        if not live and not os.path.exists(src):
            raise CommandError(f"Video file not found: {src}")
        fps = o["fps"] if o["fps"] is not None else (3.0 if live else 0.0)
        interval = 1.0 / fps if fps else 0.0
 
        cap = cv2.VideoCapture(src)
        if not cap.isOpened() and not live:
            raise CommandError(f"Cannot open video: {src}")
        det, ver = FireDetector(o["weights"]), TemporalVerifier()
        layer = get_channel_layer()
        self.stdout.write(f"Watching '{cam.name}' [{'LIVE' if live else 'FILE'}] source={hide_password(raw)}  (Ctrl+C to stop)")
 
        last_incident = last_infer = last_beat = 0.0
        analysed = 0
        got_any = False
        try:
            while True:
                if not cap.grab():
                    if live:                                    # stream dropped -> reconnect
                        self.stdout.write("Stream lost, reconnecting in 2s...")
                        cap.release(); time.sleep(2); cap = cv2.VideoCapture(src); continue
                    if o["loop"] and got_any:                   # repeat the file
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0); ver = TemporalVerifier(); continue
                    self.stdout.write("Video finished."); break
                got_any = True
                now = time.time()
                if interval and now - last_infer < interval:
                    continue                                    # skip frame (keeps live streams real-time on CPU)
                ok, frame = cap.retrieve()
                if not ok:
                    continue
                last_infer = now
                dets = det.detect(frame)
                analysed += 1
                for label, score, (x1, y1, x2, y2) in dets:
                    colour = (0, 0, 255) if label == "fire" else (200, 200, 200)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), colour, 2)
                    cv2.putText(frame, f"{label} {score:.2f}", (x1, max(y1 - 6, 12)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, colour, 2)
 
                if ver.update(dets) and now - last_incident > settings.FIRE_COOLDOWN_SEC:
                    last_incident = now
                    fires = [d for d in dets if d[0] == "fire"]
                    conf = max(d[1] for d in fires) if fires else 0.0
                    inc = Incident(camera=cam, confidence=conf)
                    inc.snapshot.save(f"cam{cam.id}_{int(now)}.jpg",
                                      ContentFile(cv2.imencode(".jpg", frame)[1].tobytes()), save=True)
                    threading.Thread(target=local_alarm, daemon=True).start()
                    escalate(inc)
                    async_to_sync(layer.group_send)("alerts", {"type": "alert", "data": {
                        "id": inc.id, "camera": cam.name, "confidence": round(conf, 2)}})
                    self.stdout.write(self.style.ERROR(f"FIRE CONFIRMED incident {inc.id}"))
 
                if now - last_beat > 30:                        # heartbeat so you know it is alive
                    last_beat = now
                    self.stdout.write(f"[{time.strftime('%H:%M:%S')}] running - {analysed} frames analysed, "
                                      f"fire hits in window: {sum(ver.hist)}/{ver.hist.maxlen}")
                if o["show"]:
                    cv2.imshow("FireWatch (q to quit)", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
        except KeyboardInterrupt:
            self.stdout.write("Stopped.")
        finally:
            cap.release()
            cv2.destroyAllWindows()
 