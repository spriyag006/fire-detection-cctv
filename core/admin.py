from django.contrib import admin
from .models import *
for m in (Camera, Facility, Incident, Notification): admin.site.register(m)
