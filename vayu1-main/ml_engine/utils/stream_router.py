from typing import Tuple
import numpy as np
from .cds_client import CDSClient
from .mosdac_client import MOSDACClient


class SatelliteStreamRouter:

  def __init__(self):
    self.mosdac = MOSDACClient()
    self.cds = CDSClient()

  def get_stream(
      self, basin: str = "BOB"
  ) -> Tuple[np.ndarray, str, bool]:
    frame = self.mosdac.fetch_latest_tir1_array()
    satellite_name = "INSAT-3D/3DS Imager"
    is_southern_hemisphere = False

    return frame, satellite_name, is_southern_hemisphere

  def get_environmental_physics(
      self, lat: float, lon: float
  ) -> np.ndarray:
    return self.cds.fetch_latest_environmental_physics(lat, lon)
