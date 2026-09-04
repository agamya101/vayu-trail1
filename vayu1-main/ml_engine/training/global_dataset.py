from typing import List, Optional, Tuple
import numpy as np
import torch
from torch.utils.data import Dataset
from .ibtracs_loader import StormRecord
from .wind_standards import convert_wind_speed


def normalize_cyclone_patch(
    patch: np.ndarray,
    is_southern_hemisphere: bool = False,
    min_temp: float = 180.0,
    max_temp: float = 320.0,
) -> np.ndarray:
  norm_patch = np.clip((patch - min_temp) / (max_temp - min_temp), 0.0, 1.0)
  if is_southern_hemisphere:
    norm_patch = np.fliplr(norm_patch)
  return norm_patch.astype(np.float32)


class GlobalCycloneDataset(Dataset):

  def __init__(
      self,
      records: List[StormRecord],
      patch_size: int = 128,
      target_wind_standard: str = "3min",
  ):
    self.records = records
    self.patch_size = patch_size
    self.target_wind_standard = target_wind_standard

  def __len__(self) -> int:
    return len(self.records)

  def __getitem__(
      self, idx: int
  ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    record = self.records[idx]

    simulated_temp = np.random.uniform(
        190.0, 310.0, (self.patch_size, self.patch_size)
    ).astype(np.float32)
    normalized = normalize_cyclone_patch(
        simulated_temp,
        is_southern_hemisphere=record.is_southern_hemisphere,
    )
    img_tensor = torch.from_numpy(normalized).unsqueeze(0).float()

    converted_msw = convert_wind_speed(
        record.msw_knots,
        from_standard="1min",
        to_standard=self.target_wind_standard,
    )
    msw_target = torch.tensor([converted_msw / 100.0], dtype=torch.float32)

    cat_idx = min(6, max(0, int(converted_msw // 20)))
    cat_target = torch.tensor(cat_idx, dtype=torch.long)

    env_features = torch.tensor(
        [
            0.0,
            0.0,
            0.0,
            0.0,
            record.pressure_hpa,
        ],
        dtype=torch.float32,
    )

    return img_tensor, msw_target, cat_target, env_features
