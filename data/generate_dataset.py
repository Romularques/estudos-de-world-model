"""CLI: python -m data.generate_dataset --customers 10000 --months 12."""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from environment.insurance_env import InsuranceEnvironment
from .dataset import flatten_transition, policy, validate_dataset


def generate(customers: int, months: int, seed: int, output: str | Path, oracle_output: str | Path | None = None):
    env, rng = InsuranceEnvironment(seed), np.random.default_rng(seed + 1)
    public_rows, oracle_rows = [], []
    start = pd.Timestamp("2025-01-01")
    for customer_id in range(customers):
        state = env.initial_state()
        for step in range(months):
            action = policy(state, rng); next_state, reward, info = env.step(state, action)
            common = (customer_id, customer_id, str(start + pd.DateOffset(months=step)), step, state, action, next_state, reward, step == months - 1, info)
            public_rows.append(flatten_transition(*common[:-1], include_latent=False, info=common[-1]))
            oracle_rows.append(flatten_transition(*common[:-1], include_latent=True, info=common[-1]))
            state = next_state
    public, oracle = pd.DataFrame(public_rows), pd.DataFrame(oracle_rows)
    validate_dataset(public)
    output = Path(output); output.parent.mkdir(parents=True, exist_ok=True); public.to_parquet(output, index=False)
    oracle_path = Path(oracle_output) if oracle_output else output.with_name("insurance_oracle.parquet")
    oracle.to_parquet(oracle_path, index=False)
    return public, oracle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--customers", type=int, default=10_000); parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42); parser.add_argument("--output", default="artifacts/insurance_trajectories.parquet")
    args = parser.parse_args(); public, _ = generate(**vars(args))
    print(f"Generated {len(public):,} transitions at {args.output}")

if __name__ == "__main__": main()
