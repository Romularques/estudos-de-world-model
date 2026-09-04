import numpy as np
from data.generate_dataset import generate

def test_dataset_has_transition_contract_and_no_nans(tmp_path):
    public, oracle = generate(8, 3, 42, tmp_path / "data.parquet")
    assert len(public) == 24 and {"state_age", "action_type", "next_state_age", "reward"} <= set(public)
    assert not public.select_dtypes(include="number").isna().any().any()
    assert "state_trust" not in public and "state_trust" in oracle

def test_seed_reproducibility_and_variation(tmp_path):
    a, _ = generate(5, 2, 42, tmp_path / "a.parquet"); b, _ = generate(5, 2, 42, tmp_path / "b.parquet"); c, _ = generate(5, 2, 43, tmp_path / "c.parquet")
    assert a.equals(b)
    assert not a.equals(c)
    assert np.isfinite(a.select_dtypes(include="number").to_numpy()).all()
