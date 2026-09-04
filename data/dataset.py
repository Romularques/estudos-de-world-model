"""Trajectory tabularization and deterministic policy used for collection."""
from __future__ import annotations
import pandas as pd
from environment.models import Action, ActionType, Channel, CustomerState, Product


def policy(state: CustomerState, rng) -> Action:
    missing = [p for p, owned in [(Product.AUTO, state.auto_policy), (Product.HOME, state.home_policy), (Product.LIFE, state.life_policy)] if not owned]
    draw = rng.random()
    if missing and draw < 0.43:
        product = missing[int(rng.integers(len(missing)))]; price = {Product.AUTO: 80, Product.HOME: 55, Product.LIFE: 65}[product]
        channel = [Channel.APP, Channel.EMAIL, Channel.BROKER, Channel.CALL_CENTER][int(rng.integers(4))]
        return Action(action_type=ActionType.OFFER_PRODUCT, product=product, price=price, channel=channel, discount=round(float(rng.uniform(0, .2)), 2))
    if draw < 0.65: return Action(action_type=ActionType.SEND_MESSAGE)
    if draw < 0.78: return Action(action_type=ActionType.CONTACT_BROKER)
    if state.premium_monthly > 0 and draw < 0.86: return Action(action_type=ActionType.CHANGE_PRICE, discount=.05)
    return Action(action_type=ActionType.NO_ACTION)


def flatten_transition(trajectory_id: int, customer_id: int, timestamp: str, step: int, state: CustomerState, action: Action, next_state: CustomerState, reward: float, done: bool, include_latent: bool, info: dict) -> dict:
    row = {"trajectory_id": trajectory_id, "customer_id": customer_id, "timestamp": timestamp, "step": step, "reward": reward, "done": done,
           "action_type": action.action_type.value, "action_product": action.product.value if action.product else None,
           # Numeric action fields use a neutral sentinel, keeping the training matrix finite.
           "action_price": action.price if action.price is not None else 0.0, "action_channel": action.channel.value if action.channel else "NONE", "action_discount": action.discount,
           "purchase_probability": info["purchase_probability"], "purchased": info["purchased"], "cancelled": info["cancelled"]}
    row.update({f"state_{k}": v for k, v in state.observable(include_latent).items()})
    row.update({f"next_state_{k}": v for k, v in next_state.observable(include_latent).items()})
    return row


def validate_dataset(frame: pd.DataFrame) -> None:
    required = {"trajectory_id", "customer_id", "step", "reward", "action_type", "state_age", "next_state_age"}
    missing = required - set(frame.columns)
    if missing: raise ValueError(f"Dataset missing columns: {sorted(missing)}")
    numeric = frame.select_dtypes(include="number")
    if numeric.isna().any().any(): raise ValueError("Dataset contains NaN numeric values")
