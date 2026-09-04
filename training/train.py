"""Reproducible training entrypoint for EXP-001 baseline MLP."""
from __future__ import annotations
import argparse, json, os, random
from pathlib import Path
import joblib, mlflow, numpy as np, pandas as pd, torch
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset
from data.dataset import validate_dataset
from evaluation.metrics import evaluate_predictions
from model.encoder import JOURNEY, build_preprocessor, customer_split, targets
from model.losses import baseline_loss
from model.world_model import BaselineMLP
from .config import TrainingConfig

def seed_everything(seed: int):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.use_deterministic_algorithms(True, warn_only=True)

def _tensor_data(features, numeric, journey, reward):
    return TensorDataset(torch.tensor(features, dtype=torch.float32), torch.tensor(numeric, dtype=torch.float32), torch.tensor(journey, dtype=torch.long), torch.tensor(reward, dtype=torch.float32))

def train(dataset: str = "artifacts/insurance_trajectories.parquet", artifact_dir: str = "artifacts/exp-001", config: TrainingConfig = TrainingConfig()) -> dict:
    seed_everything(config.seed); artifact = Path(artifact_dir); artifact.mkdir(parents=True, exist_ok=True)
    frame = pd.read_parquet(dataset); validate_dataset(frame)
    # Guardrail: public training data must never contain simulator-only latent columns.
    if any("price_sensitivity" in c or "insurance_affinity" in c or c.endswith("_trust") for c in frame.columns): raise ValueError("Oracle/latent columns are prohibited in baseline training")
    train_frame, valid_frame, test_frame = customer_split(frame, config.seed)
    preprocessor = build_preprocessor(); x_train = preprocessor.fit_transform(train_frame).astype("float32"); x_valid = preprocessor.transform(valid_frame).astype("float32")
    y_train_num, y_train_journey, y_train_reward = targets(train_frame); y_valid_num, y_valid_journey, y_valid_reward = targets(valid_frame)
    numeric_scaler, reward_scaler = StandardScaler().fit(y_train_num), StandardScaler().fit(y_train_reward.reshape(-1, 1))
    train_loader = DataLoader(_tensor_data(x_train, numeric_scaler.transform(y_train_num), y_train_journey, reward_scaler.transform(y_train_reward.reshape(-1, 1)).ravel()), batch_size=config.batch_size, shuffle=True)
    model = BaselineMLP(x_train.shape[1], y_train_num.shape[1], len(JOURNEY), config.hidden_dim); optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    # SQLite keeps local tracking self-contained and avoids the deprecated file-store backend.
    mlflow.set_tracking_uri(f"sqlite:///{(artifact / 'mlflow.db').resolve().as_posix()}")
    experiment_name = "insurance-world-model"
    if mlflow.get_experiment_by_name(experiment_name) is None:
        mlflow.create_experiment(experiment_name, artifact_location=(artifact / "mlflow_artifacts").resolve().as_uri())
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=config.experiment_id):
        mlflow.log_params({**config.__dict__, "dataset": str(dataset), "train_customers": train_frame.customer_id.nunique(), "valid_customers": valid_frame.customer_id.nunique(), "test_customers": test_frame.customer_id.nunique()})
        for epoch in range(config.epochs):
            model.train(); losses = []
            for x, y_num, y_journey, y_reward in train_loader:
                optimizer.zero_grad(); loss = baseline_loss(model(x), y_num, y_journey, y_reward); loss.backward(); optimizer.step(); losses.append(loss.item())
            model.eval()
            with torch.no_grad(): valid_pred = model(torch.tensor(x_valid)); valid_loss = baseline_loss(valid_pred, torch.tensor(numeric_scaler.transform(y_valid_num), dtype=torch.float32), torch.tensor(y_valid_journey), torch.tensor(reward_scaler.transform(y_valid_reward.reshape(-1,1)).ravel(), dtype=torch.float32)).item()
            mlflow.log_metrics({"train_loss": float(np.mean(losses)), "validation_loss": valid_loss}, step=epoch)
        torch.save({"state_dict": model.state_dict(), "hidden_dim": config.hidden_dim}, artifact / "baseline_mlp.pt")
        joblib.dump({"feature_preprocessor": preprocessor, "numeric_scaler": numeric_scaler, "reward_scaler": reward_scaler, "seed": config.seed}, artifact / "preprocessing.joblib")
        pred_num = numeric_scaler.inverse_transform(valid_pred["next_numeric"].numpy()); pred_reward = reward_scaler.inverse_transform(valid_pred["reward"].numpy()).ravel()
        metrics = evaluate_predictions(y_valid_num, pred_num, y_valid_journey, valid_pred["next_journey"].argmax(1).numpy(), y_valid_reward, pred_reward)
        mlflow.log_metrics({f"validation_{key}": value for key, value in metrics.items()})
        mlflow.log_artifact(str(artifact / "baseline_mlp.pt")); mlflow.log_artifact(str(artifact / "preprocessing.joblib"))
    metadata = {"experiment_id": config.experiment_id, "dataset_version": config.dataset_version, "environment_version": config.environment_version, "model_version": "baseline-mlp-v1", "seed": config.seed, "rows": len(frame), "metrics": metrics}
    (artifact / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--dataset", default="artifacts/insurance_trajectories.parquet"); parser.add_argument("--artifact-dir", default="artifacts/exp-001"); parser.add_argument("--epochs", type=int, default=8)
    args = parser.parse_args(); cfg = TrainingConfig(epochs=args.epochs); print(json.dumps(train(args.dataset, args.artifact_dir, cfg), indent=2))
if __name__ == "__main__": main()
