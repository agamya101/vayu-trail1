import numpy as np
from ml_engine.training.global_dataset import normalize_cyclone_patch


class Preprocessor:

  @staticmethod
  def crop_storm_patch(
      full_disk: np.ndarray,
      center_y: int = 256,
      center_x: int = 256,
      size: int = 128,
      is_southern_hemisphere: bool = False,
  ) -> np.ndarray:
    h, w = full_disk.shape
    y1, y2 = max(0, center_y - size // 2), min(h, center_y + size // 2)
    x1, x2 = max(0, center_x - size // 2), min(w, center_x + size // 2)
    patch = full_disk[y1:y2, x1:x2]

    if patch.shape[0] != size or patch.shape[1] != size:
      padded = np.full((size, size), 290.0, dtype=np.float32)
      ph, pw = patch.shape
      padded[:ph, :pw] = patch
      patch = padded

    return normalize_cyclone_patch(patch, is_southern_hemisphere=is_southern_hemisphere)