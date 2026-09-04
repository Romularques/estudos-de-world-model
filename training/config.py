from dataclasses import dataclass

@dataclass(frozen=True)
class TrainingConfig:
    seed: int = 42
    epochs: int = 8
    batch_size: int = 1024
    learning_rate: float = 1e-3
    hidden_dim: int = 64
    latent_dim: int = 32
    state_loss_weight: float = 1.0
    journey_loss_weight: float = 1.0
    reward_loss_weight: float = 1.0
    reward_loss: str = "mse"
    residual_numeric: bool = False
    scheduler_step_size: int = 4
    scheduler_gamma: float = 0.5
    event_heads: bool = False
    purchase_loss_weight: float = 0.0
    cancellation_loss_weight: float = 0.0
    experiment_id: str = "EXP-001"
    dataset_version: str = "v0.1"
    environment_version: str = "v0.1"
