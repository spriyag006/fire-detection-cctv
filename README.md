# FireWatch - Fire & Smoke Detection in CCTV Footage

A mini project (B.Tech AI & Data Science) that watches a CCTV stream, webcam or recorded video, detects **fire / smoke** with a **YOLOX-s** model, confirms it over several frames, and raises an incident with an email alert, a local alarm and a live dashboard.



## Features
- **Video input:** recorded files, webcam, phone camera (IP Webcam) or RTSP CCTV, read with OpenCV; live streams auto-reconnect.
- **Detection:** YOLOX-s, two classes (`smoke`, `fire`), trained on a COCO-format dataset (Google Colab GPU).
- **Temporal verification:** a fire is confirmed only when at least 6 of the last 10 analysed frames contain a fire box with confidence >= 0.5; a 120 s cooldown avoids duplicate alerts.
- **Incident logging:** Django models `Camera`, `Facility`, `Incident` (with snapshot) and `Notification`.
- **Alerts:** email via Gmail SMTP to the nearest fire station / ambulance / hospital within 15 km (haversine distance), local alarm sound, and a WebSocket push to the dashboard.
- **Dashboard:** incident table, Leaflet / OpenStreetMap map, incidents-per-day chart (Chart.js), siren in the browser, Django admin for configuration.

## Tech stack
Python, PyTorch, YOLOX, OpenCV, Django, Django REST Framework, Channels (Daphne), SQLite (default) / PostgreSQL, Bootstrap, Leaflet, Chart.js.

## Setup
```bash
git clone https://github.com/spriyag006/fire-detection-cctv.git
cd fire-detection-cctv
pip install -r requirements.txt
```
YOLOX and PyTorch are installed separately (see the [YOLOX repo](https://github.com/Megvii-BaseDetection/YOLOX)). In `firewatch/settings.py` set `YOLOX_EXP` to your experiment file (`fire_yolox_s.py`).

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver        # HTTP + WebSocket (Daphne)
```
Open `/admin/`, add a **Camera** (source `0`, a video path or an `rtsp://` URL) and one or more **Facilities** (kind, latitude, longitude, email). The dashboard is at `/`.

### Email alerts (optional)
Credentials are read from environment variables, never from code (see `settings_email_snippet.txt`):
```powershell
$env:EMAIL_HOST_USER = "you@gmail.com"
$env:EMAIL_HOST_PASSWORD = "your-16-letter-app-password"
```
Without them, emails are printed to the console.

## Run the detector
Model weights (`best_ckpt.pth`) are **not** stored in this repository (see Weights).
```bash
# stored video
python manage.py run_detector 1 --weights best_ckpt.pth --source path/to/video.mp4 --show
# laptop webcam
python manage.py run_detector 1 --weights best_ckpt.pth --source 0 --show
# phone as camera (IP Webcam app, same WiFi)
python manage.py run_detector 1 --weights best_ckpt.pth --source http://PHONE_IP:8080/video
# RTSP CCTV
python manage.py run_detector 1 --weights best_ckpt.pth --source "rtsp://user:pass@CAM_IP:554/stream"
```
Options: `--show` (preview window, `q` to quit), `--loop` (repeat a file), `--fps` (max frames analysed per second; default 3 for live streams).

## Project structure
```
core/            models, views, detector (YOLOX + temporal verifier), emergency (nearest facility + email), WebSocket consumer
core/management/commands/run_detector.py
core/templates/core/dashboard.html
firewatch/       Django settings and URLs
```

## Weights
The trained `best_ckpt.pth` is too large for the repository. Add a download link here: `<link to your Drive / GitHub Release>`.

## Limitations
- Trained on a limited dataset; it can miss fire in daytime footage or scenes unlike the training data, and may also produce false detections. Test on your own cameras before relying on it.
- On CPU only about 2-3 frames per second are analysed.
- It assists a human operator and is **not** a replacement for certified fire-alarm systems.

## Future work
More diverse training data, GPU / edge deployment, Redis channel layer, SMS / call alerts, multi-camera scaling.

## Team
Sangeetha Priya G, Sanjana K.S, C. Santhosh - Department of AI & DS, Prathyusha Engineering College. Guide: Ms. R. Anitha, M.E., (Ph.D).
