from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/cyclones/", include("apps.cyclones.urls")),
    path("api/predictions/", include("apps.predictions.urls")),
]