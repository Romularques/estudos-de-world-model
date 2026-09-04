"""Generate the Phase 1 diagnostic charts from a trajectory dataset."""
from pathlib import Path
import os
os.environ.setdefault("MPLCONFIGDIR", str(Path("artifacts") / ".matplotlib"))
import matplotlib.pyplot as plt
import pandas as pd

def create_plots(dataset_path="artifacts/insurance_trajectories.parquet", output_dir="artifacts/plots"):
    df = pd.read_parquet(dataset_path); out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    charts = [(df.groupby("step")["purchased"].mean(), "Adhesion rate", "adhesion_rate.png"),
              (df.groupby("step")["state_digital_engagement"].mean(), "Average engagement", "engagement.png"),
              (df["action_type"].value_counts(), "Actions", "actions.png"),
              (df.groupby(["step", "state_journey_stage"]).size().unstack(fill_value=0), "Journey stages", "journey.png"),
              (df.groupby("step")["reward"].mean(), "Average reward", "reward.png")]
    for values, title, filename in charts:
        ax = values.plot(kind="bar" if filename == "actions.png" else "line", figsize=(8, 4), title=title)
        ax.set_xlabel("month" if filename != "actions.png" else "action"); plt.tight_layout(); plt.savefig(out / filename, dpi=150); plt.close()

if __name__ == "__main__": create_plots()
