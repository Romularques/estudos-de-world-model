"""Sprint 3 baseline only: direct MLP, not the latent-state World Model."""
import torch
from torch import nn

class BaselineMLP(nn.Module):
    def __init__(self, input_dim: int, numeric_outputs: int, journey_classes: int, hidden_dim: int = 64):
        super().__init__()
        self.backbone = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, hidden_dim), nn.ReLU())
        self.next_numeric = nn.Linear(hidden_dim, numeric_outputs)
        self.next_journey = nn.Linear(hidden_dim, journey_classes)
        self.reward = nn.Linear(hidden_dim, 1)

    def forward(self, features):
        hidden = self.backbone(features)
        return {"next_numeric": self.next_numeric(hidden), "next_journey": self.next_journey(hidden), "reward": self.reward(hidden)}


class InsuranceWorldModel(nn.Module):
    """Small, explicit state/action/transition architecture for one-step dynamics."""
    def __init__(self, state_dim: int, action_dim: int, numeric_outputs: int, journey_classes: int, latent_dim: int = 32, hidden_dim: int = 64, residual_numeric: bool = False, event_heads: bool = False):
        super().__init__()
        self.state_encoder = nn.Sequential(nn.Linear(state_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, latent_dim))
        self.action_encoder = nn.Sequential(nn.Linear(action_dim, hidden_dim // 2), nn.ReLU(), nn.Linear(hidden_dim // 2, latent_dim // 2))
        self.dynamics = nn.Sequential(nn.Linear(latent_dim + latent_dim // 2, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, latent_dim), nn.ReLU())
        self.numeric_decoder = nn.Linear(latent_dim, numeric_outputs)
        self.state_skip = nn.Linear(state_dim, numeric_outputs, bias=False) if residual_numeric else None
        self.journey_decoder = nn.Linear(latent_dim, journey_classes)
        self.reward_head = nn.Linear(latent_dim, 1)
        self.purchase_head = nn.Linear(latent_dim, 1) if event_heads else None
        self.cancellation_head = nn.Linear(latent_dim, 1) if event_heads else None

    def forward(self, state_features, action_features):
        state_latent = self.state_encoder(state_features)
        action_latent = self.action_encoder(action_features)
        next_latent = self.dynamics(torch.cat([state_latent, action_latent], dim=1))
        next_numeric = self.numeric_decoder(next_latent)
        if self.state_skip is not None:
            next_numeric = next_numeric + self.state_skip(state_features)
        output = {"next_numeric": next_numeric, "next_journey": self.journey_decoder(next_latent), "reward": self.reward_head(next_latent), "latent_state": state_latent, "predicted_latent_state": next_latent}
        if self.purchase_head is not None:
            output["purchase_logit"] = self.purchase_head(next_latent).squeeze(1)
            output["cancellation_logit"] = self.cancellation_head(next_latent).squeeze(1)
        return output
