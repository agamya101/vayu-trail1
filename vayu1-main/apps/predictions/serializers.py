from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework import serializers
from .models import ForecastTrack, RainfallForecast


class ForecastTrackSerializer(GeoFeatureModelSerializer):

  class Meta:
    model = ForecastTrack
    geo_field = "current_point"
    fields = (
        "id",
        "storm",
        "basin",
        "generated_at",
        "current_point",
        "msw_knots",
        "msw_10min",
        "msw_1min",
        "primary_category",
        "imd_category",
        "south_pacific_category",
        "satellite_source",
        "forecast_timeline",
        "is_active",
        "central_pressure_hpa",
        "eye_confidence",
        "eye_confidence_label",
    )


class RainfallForecastSerializer(serializers.ModelSerializer):

  class Meta:
    model = RainfallForecast
    fields = (
        "id",
        "storm",
        "forecast_track",
        "generated_at",
        "forecast_hour",
        "rainfall_grid",
        "max_rainfall_mm",
        "model_tier",
    )
