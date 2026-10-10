from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import serializers, viewsets
from .models import Camera, Facility, Incident

class IncidentSerializer(serializers.ModelSerializer):
    camera_name = serializers.CharField(source="camera.name", read_only=True)
    class Meta: model = Incident; fields = "__all__"

class IncidentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Incident.objects.select_related("camera"); serializer_class = IncidentSerializer

@login_required
def dashboard(request):
    map_data = {
        "cameras": list(Camera.objects.values("name", "location", "latitude", "longitude")),
        "facilities": list(Facility.objects.values("name", "kind", "latitude", "longitude")),
        "incidents": [{"id": i.id, "camera": i.camera.name, "lat": i.camera.latitude, "lon": i.camera.longitude,
                       "conf": round(i.confidence, 2)} for i in Incident.objects.select_related("camera")[:50]],
    }
    return render(request, "core/dashboard.html",
                  {"incidents": Incident.objects.select_related("camera")[:50], "map_data": map_data})

@login_required
def stats(request):
    per_day = Incident.objects.annotate(d=TruncDate("detected_at")).values("d").annotate(n=Count("id")).order_by("d")
    return JsonResponse({"labels": [str(r["d"]) for r in per_day], "counts": [r["n"] for r in per_day]})
