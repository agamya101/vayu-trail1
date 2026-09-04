from ml_engine.architectures.classifier import IntensityClassifier
from ml_engine.architectures.detector import SimpleVortexDetector
from ml_engine.architectures.tracker import MultimodalTrackPredictor
from ml_engine.pipelines.postprocessor import Postprocessor
from ml_engine.pipelines.preprocessor import Preprocessor
from ml_engine.pipelines.rainfall_estimator import RainfallEstimator
from ml_engine.training.wind_standards import (
    convert_wind_speed,
    get_imd_category,
    get_south_pacific_category,
    get_basin_category,
)
from ml_engine.utils.stream_router import SatelliteStreamRouter
import torch

_SUPPORTED_BASINS = frozenset({"BOB", "AS"})
_HORIZONS = MultimodalTrackPredictor.HORIZONS


class CyclonePipeline:

  _instance = None

  def __init__(self):
    self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    self.detector = SimpleVortexDetector().to(self.device).eval()
    self.classifier = IntensityClassifier().to(self.device).eval()
    self.tracker = MultimodalTrackPredictor().to(self.device).eval()
    self.router = SatelliteStreamRouter()
    self.rainfall = RainfallEstimator()

  @classmethod
  def get_instance(cls):
    if cls._instance is None:
      cls._instance = cls()
    return cls._instance

  def _get_base_coordinates(self, basin: str) -> tuple[float, float]:
    if basin.upper() == "AS":
      return 15.5, 66.5
    return 14.5, 86.2

  @staticmethod
  def _get_eye_label(confidence: float) -> str:
    if confidence < 0.35:
      return "No Organised Circulation"
    elif confidence < 0.60:
      return "Partial Circulation / Weak Eye"
    elif confidence < 0.80:
      return "Developing Eye"
    else:
      return "Well-Defined Eye"

  def run_full_inference(self, basin: str = "BOB") -> dict:
    basin_upper = basin.upper()
    if basin_upper not in _SUPPORTED_BASINS:
      raise ValueError(
          f"Basin '{basin_upper}' is not supported for live monitoring. "
          f"Supported: {sorted(_SUPPORTED_BASINS)}."
      )

    full_disk, satellite_name, is_southern = self.router.get_stream(basin_upper)

    in_tensor = (
        torch.from_numpy(full_disk).unsqueeze(0).unsqueeze(0).float().to(self.device)
    )

    with torch.no_grad():
      box, confidence_t = self.detector(in_tensor)
      box = box.cpu().numpy()[0]
      eye_confidence = float(confidence_t.cpu().item())

    base_lat, base_lon = self._get_base_coordinates(basin_upper)
    center_lat = base_lat + float(box[0])
    center_lon = base_lon + float(box[1])

    patch = Preprocessor.crop_storm_patch(full_disk, is_southern_hemisphere=is_southern)
    patch_tensor = (
        torch.from_numpy(patch).unsqueeze(0).unsqueeze(0).float().to(self.device)
    )

    env_vector = self.router.get_environmental_physics(center_lat, center_lon)
    env_tensor = torch.from_numpy(env_vector).unsqueeze(0).float().to(self.device)

    with torch.no_grad():
      msw_pred, cat_logits = self.classifier(patch_tensor, env_tensor)
      future_tracks = self.tracker(patch_tensor, env_tensor)

    estimated_msw_3min = max(17.0, float(msw_pred.item() * 100.0))
    estimated_msw_10min = convert_wind_speed(estimated_msw_3min, "3min", "10min")
    estimated_msw_1min = convert_wind_speed(estimated_msw_3min, "3min", "1min")

    imd_cat = get_imd_category(estimated_msw_3min, standard="3min")
    sp_cat = get_south_pacific_category(estimated_msw_10min, standard="10min")
    primary_category = get_basin_category(estimated_msw_3min, basin_upper, input_standard="3min")

    offsets = future_tracks.cpu().numpy()[0]
    forecast_timeline = []
    for step, horizon_h in enumerate(_HORIZONS):
      lat_delta = float(offsets[step][0])
      lon_delta = float(offsets[step][1])
      if is_southern:
        lat_delta = -abs(lat_delta)
      step_lat = round(center_lat + lat_delta, 4)
      step_lon = round(center_lon + lon_delta, 4)

      decay = 1.0 - (horizon_h / 72.0) * 0.15
      step_msw = round(estimated_msw_3min * decay, 2)
      step_category = get_imd_category(step_msw, standard="3min")

      step_grid = self.rainfall.generate_grid(step_lat, step_lon, radius_km=200, step_deg=0.5)
      step_rainfall = self.rainfall.estimate_parametric(
          msw_kt=step_msw,
          center_lat=step_lat,
          center_lon=step_lon,
          grid_points=step_grid,
          duration_h=float(horizon_h),
      )
      step_max_rain = max((p["rainfall_mm"] for p in step_rainfall), default=0.0)

      forecast_timeline.append({
          "forecast_hour": horizon_h,
          "lat": step_lat,
          "lon": step_lon,
          "msw_kt": step_msw,
          "imd_category": step_category,
          "max_rainfall_mm": round(step_max_rain, 1),
          "rainfall_grid": step_rainfall,
      })

    central_pressure_hpa = float(env_vector[4]) if len(env_vector) >= 5 else 1013.0

    result = {
        "basin": basin_upper,
        "satellite_source": satellite_name,
        "is_southern_hemisphere": is_southern,
        "center_lon": round(center_lon, 4),
        "center_lat": round(center_lat, 4),
        "msw": round(estimated_msw_3min, 2),
        "msw_3min": round(estimated_msw_3min, 2),
        "msw_10min": round(estimated_msw_10min, 2),
        "msw_1min": round(estimated_msw_1min, 2),
        "category": primary_category,
        "imd_category": imd_cat,
        "south_pacific_category": sp_cat,
        "central_pressure_hpa": round(central_pressure_hpa, 1),
        "eye_confidence": round(eye_confidence, 3),
        "eye_confidence_label": self._get_eye_label(eye_confidence),
        "forecast_timeline": forecast_timeline,
    }
    return Postprocessor.validate_and_enrich(result)