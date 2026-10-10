from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
router = DefaultRouter(); router.register("incidents", views.IncidentViewSet)
urlpatterns = [path("", views.dashboard, name="dashboard"), path("stats/", views.stats),
               path("api/", include(router.urls))]
