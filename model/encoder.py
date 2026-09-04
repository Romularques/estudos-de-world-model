"""Feature schema and leakage-safe preprocessing for the public trajectory dataset."""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

STATE_NUMERIC = ["state_age", "state_tenure_months", "state_auto_policy", "state_home_policy", "state_life_policy", "state_claims_12m", "state_premium_monthly", "state_digital_engagement"]
ACTION_NUMERIC = ["action_price", "action_discount"]
STATE_CATEGORICAL = ["state_journey_stage"]
ACTION_CATEGORICAL = ["action_type", "action_product", "action_channel"]
CATEGORICAL = STATE_CATEGORICAL + ACTION_CATEGORICAL
NEXT_NUMERIC = [c.replace("state_", "next_state_") for c in STATE_NUMERIC]
JOURNEY = ["UNAWARE", "AWARE", "INTERESTED", "QUOTING", "CONSIDERING", "CUSTOMER", "CANCELLED"]


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer([( "numeric", StandardScaler(), STATE_NUMERIC + ACTION_NUMERIC),
                              ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)])


def build_state_preprocessor() -> ColumnTransformer:
    return ColumnTransformer([("numeric", StandardScaler(), STATE_NUMERIC),
                              ("categorical", OneHotEncoder(handle_unknown="ignore"), STATE_CATEGORICAL)])


def build_action_preprocessor() -> ColumnTransformer:
    return ColumnTransformer([("numeric", StandardScaler(), ACTION_NUMERIC),
                              ("categorical", OneHotEncoder(handle_unknown="ignore"), ACTION_CATEGORICAL)])


def customer_split(frame: pd.DataFrame, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split complete customer trajectories; no customer appears in two partitions."""
    customers = np.array(sorted(frame.customer_id.unique()))
    rng = np.random.default_rng(seed); rng.shuffle(customers)
    n = len(customers); train_end, valid_end = int(.70 * n), int(.85 * n)
    groups = [set(customers[:train_end]), set(customers[train_end:valid_end]), set(customers[valid_end:])]
    return tuple(frame[frame.customer_id.isin(group)].reset_index(drop=True) for group in groups)


def targets(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    numeric = frame[NEXT_NUMERIC].astype(float).to_numpy()
    journey = np.array([JOURNEY.index(value) for value in frame.next_state_journey_stage])
    reward = frame.reward.astype(float).to_numpy()
    return numeric, journey, reward


def event_targets(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Post-action event labels; valid outputs, never valid input features."""
    return frame.purchased.astype("float32").to_numpy(), frame.cancelled.astype("float32").to_numpy()
