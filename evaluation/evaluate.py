"""Evaluate a saved EXP-001 model on the held-out customer partition."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import joblib, numpy as np, pandas as pd, torch
from model.encoder import JOURNEY, customer_split, targets
from model.world_model import BaselineMLP
from .metrics import evaluate_predictions

def evaluate(dataset: str, artifact_dir: str) -> dict:
    artifact = Path(artifact_dir); bundle = joblib.load(artifact / "preprocessing.joblib")
    _, _, test = customer_split(pd.read_parquet(dataset), bundle["seed"])
    x = bundle["feature_preprocessor"].transform(test).astype("float32")
    y_num, y_journey, y_reward = targets(test)
    checkpoint = torch.load(artifact / "baseline_mlp.pt", map_location="cpu", weights_only=True)
    model = BaselineMLP(x.shape[1], y_num.shape[1], len(JOURNEY), checkpoint["hidden_dim"]); model.load_state_dict(checkpoint["state_dict"]); model.eval()
    with torch.no_grad(): prediction = model(torch.tensor(x))
    pred_numeric = bundle["numeric_scaler"].inverse_transform(prediction["next_numeric"].numpy())
    pred_reward = bundle["reward_scaler"].inverse_transform(prediction["reward"].numpy()).ravel()
    metrics = evaluate_predictions(y_num, pred_numeric, y_journey, prediction["next_journey"].argmax(1).numpy(), y_reward, pred_reward)
    (artifact / "test_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--dataset", default="artifacts/insurance_trajectories.parquet"); parser.add_argument("--artifact-dir", default="artifacts/exp-001")
    print(json.dumps(evaluate(**vars(parser.parse_args())), indent=2))
if __name__ == "__main__": main()
