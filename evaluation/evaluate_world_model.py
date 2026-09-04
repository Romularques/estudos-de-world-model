"""One-step test evaluation for EXP-002."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import joblib, pandas as pd, torch
from model.encoder import JOURNEY, customer_split, event_targets, targets
from model.world_model import InsuranceWorldModel
from .metrics import evaluate_predictions

def evaluate_world_model(dataset="artifacts/insurance_trajectories.parquet", artifact_dir="artifacts/exp-002"):
    artifact = Path(artifact_dir); bundle = joblib.load(artifact / "preprocessing.joblib"); _, _, test = customer_split(pd.read_parquet(dataset), bundle["seed"])
    state = bundle["state_preprocessor"].transform(test).astype("float32"); action = bundle["action_preprocessor"].transform(test).astype("float32"); numeric, journey, reward = targets(test)
    checkpoint = torch.load(artifact / "world_model_v1.pt", map_location="cpu", weights_only=True)
    model = InsuranceWorldModel(checkpoint["state_dim"], checkpoint["action_dim"], numeric.shape[1], len(JOURNEY), latent_dim=checkpoint.get("latent_dim", 32), hidden_dim=checkpoint["hidden_dim"], residual_numeric=checkpoint.get("residual_numeric", False), event_heads=checkpoint.get("event_heads", False)); model.load_state_dict(checkpoint["state_dict"]); model.eval()
    with torch.no_grad(): prediction = model(torch.tensor(state), torch.tensor(action))
    result = evaluate_predictions(numeric, bundle["numeric_scaler"].inverse_transform(prediction["next_numeric"].numpy()), journey, prediction["next_journey"].argmax(1).numpy(), reward, bundle["reward_scaler"].inverse_transform(prediction["reward"].numpy()).ravel())
    if "purchase_logit" in prediction:
        from .metrics import event_metrics
        purchased, cancelled = event_targets(test)
        result.update(event_metrics(purchased, torch.sigmoid(prediction["purchase_logit"]).numpy(), "purchase"))
        result.update(event_metrics(cancelled, torch.sigmoid(prediction["cancellation_logit"]).numpy(), "cancellation"))
    (artifact / "test_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8"); return result

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--dataset", default="artifacts/insurance_trajectories.parquet"); parser.add_argument("--artifact-dir", default="artifacts/exp-002")
    print(json.dumps(evaluate_world_model(**vars(parser.parse_args())), indent=2))
if __name__ == "__main__": main()
