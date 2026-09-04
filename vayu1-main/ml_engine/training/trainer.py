from typing import Dict, List, Optional
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from ml_engine.architectures.classifier import IntensityClassifier
from .global_dataset import GlobalCycloneDataset
from .ibtracs_loader import IBTrACSLoader, StormRecord


class CycloneModelTrainer:

  def __init__(
      self,
      model: Optional[IntensityClassifier] = None,
      device: Optional[torch.device] = None,
  ):
    self.device = device or torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )
    self.model = (model or IntensityClassifier()).to(self.device)
    self.msw_criterion = nn.MSELoss()
    self.cat_criterion = nn.CrossEntropyLoss()

  def train_epoch(
      self,
      dataloader: DataLoader,
      optimizer: torch.optim.Optimizer,
  ) -> Dict[str, float]:
    self.model.train()
    total_loss = 0.0
    total_msw_loss = 0.0
    total_cat_loss = 0.0
    num_batches = len(dataloader)

    for img, msw_target, cat_target, env_features in dataloader:
      img = img.to(self.device)
      msw_target = msw_target.to(self.device)
      cat_target = cat_target.to(self.device)
      env_features = env_features.to(self.device)

      optimizer.zero_grad()
      msw_pred, cat_logits = self.model(img, env_features)

      loss_msw = self.msw_criterion(msw_pred, msw_target)
      loss_cat = self.cat_criterion(cat_logits, cat_target)
      loss = loss_msw + loss_cat

      loss.backward()
      optimizer.step()

      total_loss += loss.item()
      total_msw_loss += loss_msw.item()
      total_cat_loss += loss_cat.item()

    return {
        "loss": total_loss / max(1, num_batches),
        "msw_loss": total_msw_loss / max(1, num_batches),
        "cat_loss": total_cat_loss / max(1, num_batches),
    }

  def run_two_stage_training(
      self,
      global_records: List[StormRecord],
      regional_records: List[StormRecord],
      pretrain_epochs: int = 2,
      finetune_epochs: int = 2,
      batch_size: int = 4,
      lr: float = 1e-3,
  ) -> Dict[str, List[Dict[str, float]]]:
    pretrain_ds = GlobalCycloneDataset(
        global_records, target_wind_standard="3min"
    )
    pretrain_loader = DataLoader(
        pretrain_ds, batch_size=batch_size, shuffle=True
    )
    optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)

    pretrain_history = []
    for _ in range(pretrain_epochs):
      metrics = self.train_epoch(pretrain_loader, optimizer)
      pretrain_history.append(metrics)

    finetune_ds = GlobalCycloneDataset(
        regional_records, target_wind_standard="3min"
    )
    finetune_loader = DataLoader(
        finetune_ds, batch_size=batch_size, shuffle=True
    )
    finetune_optimizer = torch.optim.Adam(
        self.model.parameters(), lr=lr * 0.1
    )

    finetune_history = []
    for _ in range(finetune_epochs):
      metrics = self.train_epoch(finetune_loader, finetune_optimizer)
      finetune_history.append(metrics)

    return {
        "pretraining": pretrain_history,
        "finetuning": finetune_history,
    }
