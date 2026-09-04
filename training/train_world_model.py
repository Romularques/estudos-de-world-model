"""Training entrypoint for EXP-002, the one-step Insurance World Model v1."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import joblib, mlflow, numpy as np, pandas as pd, torch
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset
from data.dataset import validate_dataset
from evaluation.metrics import evaluate_predictions, event_metrics
from model.encoder import JOURNEY, build_action_preprocessor, build_state_preprocessor, customer_split, event_targets, targets
from model.losses import baseline_loss
from model.world_model import InsuranceWorldModel
from .config import TrainingConfig
from .train import seed_everything

def _dataset(state, action, numeric, journey, reward, purchased, cancelled):
    return TensorDataset(torch.tensor(state, dtype=torch.float32), torch.tensor(action, dtype=torch.float32), torch.tensor(numeric, dtype=torch.float32), torch.tensor(journey, dtype=torch.long), torch.tensor(reward, dtype=torch.float32), torch.tensor(purchased, dtype=torch.float32), torch.tensor(cancelled, dtype=torch.float32))

def train_world_model(dataset: str = "artifacts/insurance_trajectories.parquet", artifact_dir: str = "artifacts/exp-002", config: TrainingConfig = TrainingConfig(experiment_id="EXP-002")) -> dict:
    seed_everything(config.seed); artifact = Path(artifact_dir); artifact.mkdir(parents=True, exist_ok=True)
    frame = pd.read_parquet(dataset); validate_dataset(frame)
    if any("price_sensitivity" in c or "insurance_affinity" in c or c.endswith("_trust") for c in frame.columns): raise ValueError("Oracle/latent columns are prohibited in World Model training")
    train_frame, valid_frame, test_frame = customer_split(frame, config.seed)
    state_encoder, action_encoder = build_state_preprocessor(), build_action_preprocessor()
    state_train, action_train = state_encoder.fit_transform(train_frame).astype("float32"), action_encoder.fit_transform(train_frame).astype("float32")
    state_valid, action_valid = state_encoder.transform(valid_frame).astype("float32"), action_encoder.transform(valid_frame).astype("float32")
    num_train, journey_train, reward_train = targets(train_frame); num_valid, journey_valid, reward_valid = targets(valid_frame)
    purchase_train, cancel_train = event_targets(train_frame); purchase_valid, cancel_valid = event_targets(valid_frame)
    num_scaler, reward_scaler = StandardScaler().fit(num_train), StandardScaler().fit(reward_train.reshape(-1, 1))
    loader = DataLoader(_dataset(state_train, action_train, num_scaler.transform(num_train), journey_train, reward_scaler.transform(reward_train.reshape(-1,1)).ravel(), purchase_train, cancel_train), batch_size=config.batch_size, shuffle=True)
    model = InsuranceWorldModel(state_train.shape[1], action_train.shape[1], num_train.shape[1], len(JOURNEY), latent_dim=config.latent_dim, hidden_dim=config.hidden_dim, residual_numeric=config.residual_numeric, event_heads=config.event_heads)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=config.scheduler_step_size, gamma=config.scheduler_gamma)
    mlflow.set_tracking_uri(f"sqlite:///{(artifact / 'mlflow.db').resolve().as_posix()}"); name = "insurance-world-model"
    if mlflow.get_experiment_by_name(name) is None: mlflow.create_experiment(name, artifact_location=(artifact / "mlflow_artifacts").resolve().as_uri())
    mlflow.set_experiment(name)
    with mlflow.start_run(run_name=config.experiment_id):
        mlflow.log_params({**config.__dict__, "model_version": "world-model-v1", "dataset": str(dataset), "state_feature_dim": state_train.shape[1], "action_feature_dim": action_train.shape[1]})
        for epoch in range(config.epochs):
            model.train(); losses = []
            for state, action, numeric, journey, reward, purchased, cancelled in loader:
                optimizer.zero_grad(); loss = baseline_loss(model(state, action), numeric, journey, reward, config.state_loss_weight, config.journey_loss_weight, config.reward_loss_weight, config.reward_loss, purchased, cancelled, config.purchase_loss_weight, config.cancellation_loss_weight); loss.backward(); optimizer.step(); losses.append(loss.item())
            model.eval()
            with torch.no_grad(): prediction = model(torch.tensor(state_valid), torch.tensor(action_valid)); val_loss = baseline_loss(prediction, torch.tensor(num_scaler.transform(num_valid), dtype=torch.float32), torch.tensor(journey_valid), torch.tensor(reward_scaler.transform(reward_valid.reshape(-1,1)).ravel(), dtype=torch.float32), config.state_loss_weight, config.journey_loss_weight, config.reward_loss_weight, config.reward_loss, torch.tensor(purchase_valid), torch.tensor(cancel_valid), config.purchase_loss_weight, config.cancellation_loss_weight).item()
            mlflow.log_metrics({"train_loss": float(np.mean(losses)), "validation_loss": val_loss, "learning_rate": optimizer.param_groups[0]["lr"]}, step=epoch); scheduler.step()
        torch.save({"state_dict": model.state_dict(), "state_dim": state_train.shape[1], "action_dim": action_train.shape[1], "latent_dim": config.latent_dim, "hidden_dim": config.hidden_dim, "residual_numeric": config.residual_numeric, "event_heads": config.event_heads}, artifact / "world_model_v1.pt")
        joblib.dump({"state_preprocessor": state_encoder, "action_preprocessor": action_encoder, "numeric_scaler": num_scaler, "reward_scaler": reward_scaler, "seed": config.seed}, artifact / "preprocessing.joblib")
        pred_num = num_scaler.inverse_transform(prediction["next_numeric"].numpy()); pred_reward = reward_scaler.inverse_transform(prediction["reward"].numpy()).ravel()
        metrics = evaluate_predictions(num_valid, pred_num, journey_valid, prediction["next_journey"].argmax(1).numpy(), reward_valid, pred_reward)
        if config.event_heads:
            metrics.update(event_metrics(purchase_valid, torch.sigmoid(prediction["purchase_logit"]).numpy(), "purchase"))
            metrics.update(event_metrics(cancel_valid, torch.sigmoid(prediction["cancellation_logit"]).numpy(), "cancellation"))
        mlflow.log_metrics({f"validation_{key}": value for key, value in metrics.items()}); mlflow.log_artifact(str(artifact / "world_model_v1.pt")); mlflow.log_artifact(str(artifact / "preprocessing.joblib"))
    metadata = {"experiment_id": config.experiment_id, "dataset_version": config.dataset_version, "environment_version": config.environment_version, "model_version": "world-model-v1", "seed": config.seed, "rows": len(frame), "metrics": metrics}
    (artifact / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8"); return metadata

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--dataset", default="artifacts/insurance_trajectories.parquet"); parser.add_argument("--artifact-dir", default="artifacts/exp-002"); parser.add_argument("--experiment-id", default="EXP-002"); parser.add_argument("--epochs", type=int, default=8); parser.add_argument("--latent-dim", type=int, default=32); parser.add_argument("--state-loss-weight", type=float, default=1.0); parser.add_argument("--journey-loss-weight", type=float, default=1.0); parser.add_argument("--reward-loss-weight", type=float, default=1.0); parser.add_argument("--reward-loss", choices=("mse", "huber"), default="mse"); parser.add_argument("--residual-numeric", action="store_true"); parser.add_argument("--event-heads", action="store_true"); parser.add_argument("--purchase-loss-weight", type=float, default=0.0); parser.add_argument("--cancellation-loss-weight", type=float, default=0.0)
    args = parser.parse_args(); cfg = TrainingConfig(epochs=args.epochs, experiment_id=args.experiment_id, latent_dim=args.latent_dim, state_loss_weight=args.state_loss_weight, journey_loss_weight=args.journey_loss_weight, reward_loss_weight=args.reward_loss_weight, reward_loss=args.reward_loss, residual_numeric=args.residual_numeric, event_heads=args.event_heads, purchase_loss_weight=args.purchase_loss_weight, cancellation_loss_weight=args.cancellation_loss_weight); print(json.dumps(train_world_model(args.dataset, args.artifact_dir, cfg), indent=2))
if __name__ == "__main__": main()
