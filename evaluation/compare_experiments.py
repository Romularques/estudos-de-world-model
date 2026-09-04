"""Compare held-out one-step metrics without mixing train/validation results."""
import argparse, json
from pathlib import Path

KEYS = ("next_state_rmse", "journey_accuracy", "reward_mae", "reward_rmse")

def compare(baseline_dir="artifacts/exp-001", world_model_dir="artifacts/exp-002"):
    baseline = json.loads((Path(baseline_dir) / "test_metrics.json").read_text(encoding="utf-8"))
    world_model = json.loads((Path(world_model_dir) / "test_metrics.json").read_text(encoding="utf-8"))
    result = {key: {"baseline": baseline[key], "world_model_v1": world_model[key], "delta": world_model[key] - baseline[key]} for key in KEYS}
    (Path(world_model_dir) / "comparison_to_baseline.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--baseline-dir", default="artifacts/exp-001"); parser.add_argument("--world-model-dir", default="artifacts/exp-002")
    print(json.dumps(compare(**vars(parser.parse_args())), indent=2))
if __name__ == "__main__": main()
