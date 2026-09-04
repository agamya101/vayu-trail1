from __future__ import annotations

from typing import Any


class Postprocessor:

  @staticmethod
  def validate_and_enrich(result: dict[str, Any]) -> dict[str, Any]:
    out = dict(result)

    for key in ("msw", "msw_3min", "msw_10min", "msw_1min"):
      if key in out:
        out[key] = max(17.0, min(float(out[key]), 250.0))

    if "central_pressure_hpa" in out:
      out["central_pressure_hpa"] = max(
          870.0, min(float(out["central_pressure_hpa"]), 1013.0)
      )

    if "eye_confidence" in out:
      out["eye_confidence"] = max(0.0, min(float(out["eye_confidence"]), 1.0))

    out["alert_colour"] = Postprocessor._alert_colour(out.get("imd_category", ""))

    return out

  @staticmethod
  def _alert_colour(imd_category: str) -> str:
    mapping = {
        "Depression": "YELLOW",
        "Deep Depression": "YELLOW",
        "Cyclonic Storm": "ORANGE",
        "Severe Cyclonic Storm": "ORANGE",
        "Very Severe Cyclonic Storm": "RED",
        "Extremely Severe Cyclonic Storm": "RED",
        "Super Cyclonic Storm": "RED",
    }
    return mapping.get(imd_category, "GREEN")