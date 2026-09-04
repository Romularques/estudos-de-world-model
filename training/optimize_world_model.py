"""Controlled EXP-003 tuning: screen candidates on validation, test only the winner."""
from __future__ import annotations
import argparse, json
from dataclasses import replace
from pathlib import Path
from .config import TrainingConfig
from .train_world_model import train_world_model
from evaluation.evaluate_world_model import evaluate_world_model

CANDIDATES = (
    {"name": "control-l32-equal", "latent_dim": 32, "state_loss_weight": 1.0, "journey_loss_weight": 1.0, "reward_loss_weight": 1.0},
    {"name": "latent64-equal", "latent_dim": 64, "state_loss_weight": 1.0, "journey_loss_weight": 1.0, "reward_loss_weight": 1.0},
    {"name": "latent64-state2", "latent_dim": 64, "state_loss_weight": 2.0, "journey_loss_weight": 1.0, "reward_loss_weight": 1.0},
    {"name": "latent64-reward2", "latent_dim": 64, "state_loss_weight": 1.0, "journey_loss_weight": 1.0, "reward_loss_weight": 2.0},
)

def _ranked(candidates: list[dict]) -> list[dict]:
    """Equal-weight rank aggregation avoids combining metrics with incompatible units."""
    for key, reverse in (("journey_accuracy", True), ("reward_mae", False), ("next_state_rmse", False)):
        ordered = sorted(candidates, key=lambda item: item["validation_metrics"][key], reverse=reverse)
        for rank, item in enumerate(ordered, 1): item["rank_score"] = item.get("rank_score", 0) + rank
    return sorted(candidates, key=lambda item: item["rank_score"])

def optimize(dataset="artifacts/insurance_trajectories.parquet", output_dir="artifacts/exp-003", screening_epochs: int = 4, final_epochs: int = 8):
    root = Path(output_dir); root.mkdir(parents=True, exist_ok=True); screened = []
    for candidate in CANDIDATES:
        config = TrainingConfig(epochs=screening_epochs, experiment_id=f"EXP-003-{candidate['name']}", **{key: value for key, value in candidate.items() if key != "name"})
        result = train_world_model(dataset, root / candidate["name"], config)
        screened.append({**candidate, "validation_metrics": result["metrics"]})
    ranked = _ranked(screened); winner = ranked[0]
    final_config = TrainingConfig(epochs=final_epochs, experiment_id="EXP-003-winner", **{key: winner[key] for key in ("latent_dim", "state_loss_weight", "journey_loss_weight", "reward_loss_weight")})
    final_dir = root / "winner"; final_result = train_world_model(dataset, final_dir, final_config)
    test_metrics = evaluate_world_model(dataset, final_dir)
    report = {"selection_rule": "equal rank across validation journey accuracy, reward MAE, and next-state RMSE", "screening_epochs": screening_epochs, "final_epochs": final_epochs, "candidates": ranked, "winner": winner["name"], "winner_validation_metrics": final_result["metrics"], "winner_test_metrics": test_metrics}
    (root / "optimization_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8"); return report

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--dataset", default="artifacts/insurance_trajectories.parquet"); parser.add_argument("--output-dir", default="artifacts/exp-003"); parser.add_argument("--screening-epochs", type=int, default=4); parser.add_argument("--final-epochs", type=int, default=8)
    print(json.dumps(optimize(**vars(parser.parse_args())), indent=2))
if __name__ == "__main__": main()
