from django.db import models

class Camera(models.Model):
    name = models.CharField(max_length=100)
    source = models.CharField(max_length=300, help_text="0 for webcam, a video path, or rtsp://...")
    location = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(); longitude = models.FloatField()
    active = models.BooleanField(default=True)
    def __str__(self): return self.name

class Facility(models.Model):
    KINDS = [("fire", "Fire Station"), ("ambulance", "Ambulance"), ("hospital", "Hospital")]
    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=20, choices=KINDS)
    email = models.EmailField(blank=True); phone = models.CharField(max_length=30, blank=True)
    latitude = models.FloatField(); longitude = models.FloatField()
    class Meta: verbose_name_plural = "facilities"
    def __str__(self): return f"{self.name} ({self.kind})"

class Incident(models.Model):
    STATUS = [("confirmed", "Confirmed"), ("escalated", "Escalated"), ("resolved", "Resolved")]
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name="incidents")
    detected_at = models.DateTimeField(auto_now_add=True)
    label = models.CharField(max_length=20, default="fire")
    confidence = models.FloatField()
    snapshot = models.ImageField(upload_to="snapshots/", blank=True)
    clip = models.FileField(upload_to="clips/", blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="confirmed")
    class Meta: ordering = ["-detected_at"]

class Notification(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="notifications")
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)
    ok = models.BooleanField(default=False)
    distance_km = models.FloatField(default=0)
