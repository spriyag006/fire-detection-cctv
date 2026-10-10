import math
from django.conf import settings
from django.core.mail import send_mail
from .models import Facility, Notification

def haversine(a, b, c, d):
    p = math.pi / 180
    x = math.sin((c-a)*p/2)**2 + math.cos(a*p)*math.cos(c*p)*math.sin((d-b)*p/2)**2
    return 12742 * math.asin(math.sqrt(x))

def escalate(incident):
    """Notify the nearest facility of each kind within radius."""
    cam = incident.camera
    for kind, _ in Facility.KINDS:
        cands = [(haversine(cam.latitude, cam.longitude, f.latitude, f.longitude), f)
                 for f in Facility.objects.filter(kind=kind)]
        cands = [c for c in cands if c[0] <= settings.FACILITY_RADIUS_KM]
        if not cands: continue
        dist, f = min(cands, key=lambda c: c[0])
        ok = False
        if f.email:
            try:
                ok = bool(send_mail(f"FIRE ALERT: {cam.name}",
                    f"Fire confirmed at {cam.name} ({cam.location}). Confidence {incident.confidence:.0%}.\n"
                    f"Coordinates: {cam.latitude}, {cam.longitude}\n"
                    f"Map: https://www.google.com/maps?q={cam.latitude},{cam.longitude}",
                    None, [f.email], fail_silently=False))
            except Exception as e:                     # show SMTP problems instead of hiding them
                print(f"EMAIL FAILED for {f.name}: {e}")
        Notification.objects.create(incident=incident, facility=f, ok=ok, distance_km=round(dist, 2))
    incident.status = "escalated"; incident.save(update_fields=["status"])
