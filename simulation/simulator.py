"""Multi-step scenario simulation using EXP-005 predictions, never environment ground truth."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import torch
from pydantic import BaseModel, Field
from model.encoder import JOURNEY, NEXT_NUMERIC
from model.world_model import InsuranceWorldModel

CLOSED_PROFILES = {
    "AUTO_CUSTOMER": {"age": 42, "tenure_months": 30, "auto_policy": True, "home_policy": False, "life_policy": False, "claims_12m": 0, "premium_monthly": 80.0, "digital_engagement": .48, "journey_stage": "CUSTOMER"},
    "DIGITAL_PROSPECT": {"age": 31, "tenure_months": 2, "auto_policy": False, "home_policy": False, "life_policy": False, "claims_12m": 0, "premium_monthly": 0.0, "digital_engagement": .78, "journey_stage": "INTERESTED"},
    "AT_RISK_CUSTOMER": {"age": 55, "tenure_months": 54, "auto_policy": True, "home_policy": True, "life_policy": False, "claims_12m": 2, "premium_monthly": 135.0, "digital_engagement": .22, "journey_stage": "CONSIDERING"},
}
PRODUCTS = ("AUTO", "HOME", "LIFE")
CHANNELS = ("APP", "EMAIL", "BROKER", "CALL_CENTER")
CADENCES = ("ONCE", "MONTHLY")

class ProductStrategy(BaseModel):
    product: str
    price: float = Field(ge=20, le=250)
    channel: str
    discount: float = Field(ge=0, le=.50)
    cadence: str = "ONCE"

    def model_post_init(self, __context):
        if self.product not in PRODUCTS or self.channel not in CHANNELS or self.cadence not in CADENCES:
            raise ValueError("Closed-domain product, channel or cadence is invalid")

class Scenario(BaseModel):
    profile: str
    strategy: ProductStrategy
    horizon_months: int = Field(ge=1, le=24)
    simulations: int = Field(ge=10, le=1000)
    seed: int = 42

    def model_post_init(self, __context):
        if self.profile not in CLOSED_PROFILES:
            raise ValueError("Closed-domain profile is invalid")

class WorldModelSimulator:
    def __init__(self, artifact_dir: str | Path = "artifacts/exp-005"):
        artifact = Path(artifact_dir); bundle = joblib.load(artifact / "preprocessing.joblib")
        self.state_preprocessor, self.action_preprocessor = bundle["state_preprocessor"], bundle["action_preprocessor"]
        self.numeric_scaler, self.reward_scaler = bundle["numeric_scaler"], bundle["reward_scaler"]
        checkpoint = torch.load(artifact / "world_model_v1.pt", map_location="cpu", weights_only=True)
        self.model = InsuranceWorldModel(checkpoint["state_dim"], checkpoint["action_dim"], len(NEXT_NUMERIC), len(JOURNEY), latent_dim=checkpoint["latent_dim"], hidden_dim=checkpoint["hidden_dim"], residual_numeric=checkpoint.get("residual_numeric", False), event_heads=checkpoint.get("event_heads", False))
        self.model.load_state_dict(checkpoint["state_dict"]); self.model.eval()

    @staticmethod
    def _action(strategy: ProductStrategy | None) -> dict:
        if strategy is None:
            return {"action_type": "NO_ACTION", "action_product": "NONE", "action_price": 0.0, "action_channel": "NONE", "action_discount": 0.0}
        return {"action_type": "OFFER_PRODUCT", "action_product": strategy.product, "action_price": strategy.price, "action_channel": strategy.channel, "action_discount": strategy.discount}

    def predict(self, state: dict, strategy: ProductStrategy | None) -> dict:
        state_row = {f"state_{key}": value for key, value in state.items()}
        state_features = self.state_preprocessor.transform(pd.DataFrame([state_row])).astype("float32")
        action_features = self.action_preprocessor.transform(pd.DataFrame([self._action(strategy)])).astype("float32")
        with torch.no_grad(): output = self.model(torch.tensor(state_features), torch.tensor(action_features))
        numeric = self.numeric_scaler.inverse_transform(output["next_numeric"].numpy())[0]
        reward = float(self.reward_scaler.inverse_transform(output["reward"].numpy())[0, 0])
        journey_prob = torch.softmax(output["next_journey"], dim=1).numpy()[0]
        return {"numeric": numeric, "journey_probabilities": journey_prob, "reward": reward,
                "purchase_probability": float(torch.sigmoid(output.get("purchase_logit", torch.tensor([0.0])))[0]),
                "cancellation_probability": float(torch.sigmoid(output.get("cancellation_logit", torch.tensor([0.0])))[0])}

    @staticmethod
    def _decode_state(prediction: dict, rng: np.random.Generator) -> dict:
        values = dict(zip(NEXT_NUMERIC, prediction["numeric"])); journey = JOURNEY[int(rng.choice(len(JOURNEY), p=prediction["journey_probabilities"]))]
        return {"age": int(np.clip(round(values["next_state_age"]), 18, 100)), "tenure_months": max(0, int(round(values["next_state_tenure_months"]))),
                "auto_policy": bool(values["next_state_auto_policy"] >= .5), "home_policy": bool(values["next_state_home_policy"] >= .5), "life_policy": bool(values["next_state_life_policy"] >= .5),
                "claims_12m": max(0, int(round(values["next_state_claims_12m"]))), "premium_monthly": max(0.0, float(values["next_state_premium_monthly"])),
                "digital_engagement": float(np.clip(values["next_state_digital_engagement"], 0, 1)), "journey_stage": journey}

    @staticmethod
    def _summary(trajectories: list[dict]) -> dict:
        total_rewards = np.array([item["total_reward"] for item in trajectories])
        all_steps = [step for trajectory in trajectories for step in trajectory["steps"]]
        return {
            "expected_total_reward": float(total_rewards.mean()),
            "reward_p10": float(np.quantile(total_rewards, .1)),
            "reward_p90": float(np.quantile(total_rewards, .9)),
            "purchase_at_least_once": float(np.mean([item["any_purchase"] for item in trajectories])),
            "cancellation_at_least_once": float(np.mean([item["any_cancellation"] for item in trajectories])),
            "purchase_monthly_rate": float(np.mean([step["purchased"] for step in all_steps])),
            "cancellation_monthly_rate": float(np.mean([step["cancelled"] for step in all_steps])),
            "final_premium_mean": float(np.mean([item["final_state"]["premium_monthly"] for item in trajectories])),
            "active_at_horizon": float(np.mean([item["active_at_horizon"] for item in trajectories])),
            "target_product_active_at_horizon": float(np.mean([item["target_product_active_at_horizon"] for item in trajectories])),
            "success_rate": float(np.mean([item["successful"] for item in trajectories])),
            "active_months_mean": float(np.mean([item["active_months"] for item in trajectories])),
            "premium_exposure": float(np.mean([item["premium_exposure"] for item in trajectories])),
        }

    def _simulate_trajectories(self, scenario: Scenario, offer_strategy: bool) -> list[dict]:
        rng = np.random.default_rng(scenario.seed); trajectories = []
        for simulation_id in range(scenario.simulations):
            state, rewards, purchases, cancellations, steps = deepcopy(CLOSED_PROFILES[scenario.profile]), [], [], [], []
            terminated = False
            for month in range(scenario.horizon_months):
                product_key = f"{scenario.strategy.product.lower()}_policy"
                eligible_for_offer = not state[product_key]
                strategy = scenario.strategy if offer_strategy and eligible_for_offer and (scenario.strategy.cadence == "MONTHLY" or month == 0) else None
                active_customer = state["auto_policy"] or state["home_policy"] or state["life_policy"]
                prediction = self.predict(state, strategy)
                purchase = bool(strategy is not None and rng.random() < prediction["purchase_probability"])
                cancellation = bool(active_customer and rng.random() < prediction["cancellation_probability"])
                next_state = self._decode_state(prediction, rng)
                # Policy ownership is governed by the sampled business events,
                # not by thresholding a numeric decoder output independently.
                for policy_key in ("auto_policy", "home_policy", "life_policy"):
                    next_state[policy_key] = state[policy_key]
                if purchase:
                    next_state[product_key] = True
                    next_state["premium_monthly"] = max(next_state["premium_monthly"], state["premium_monthly"] + scenario.strategy.price * (1 - scenario.strategy.discount))
                    next_state["journey_stage"] = "CUSTOMER"
                if cancellation:
                    next_state.update(auto_policy=False, home_policy=False, life_policy=False, premium_monthly=0.0, journey_stage="CANCELLED")
                    terminated = True
                if not (next_state["auto_policy"] or next_state["home_policy"] or next_state["life_policy"]):
                    next_state["premium_monthly"] = 0.0
                steps.append({"month": month + 1, "reward": prediction["reward"], "offered": strategy is not None, "purchase_probability": prediction["purchase_probability"] if strategy else 0.0, "cancellation_probability": prediction["cancellation_probability"] if active_customer else 0.0, "purchased": purchase, "cancelled": cancellation, "journey_stage": next_state["journey_stage"], "premium_monthly": next_state["premium_monthly"]})
                rewards.append(prediction["reward"]); purchases.append(purchase); cancellations.append(cancellation); state = next_state
                if terminated: break
            active_at_horizon = state["auto_policy"] or state["home_policy"] or state["life_policy"]
            active_months = sum(step["premium_monthly"] > 0 for step in steps)
            premium_exposure = sum(step["premium_monthly"] for step in steps)
            target_product_active = state[product_key]
            trajectories.append({"simulation_id": simulation_id, "total_reward": float(sum(rewards)), "any_purchase": any(purchases), "any_cancellation": any(cancellations), "terminated": terminated, "final_state": state, "active_at_horizon": active_at_horizon, "target_product_active_at_horizon": target_product_active, "successful": bool(any(purchases) and target_product_active), "active_months": active_months, "premium_exposure": premium_exposure, "steps": steps})
        return trajectories

    def simulate(self, scenario: Scenario) -> dict:
        treatment = self._simulate_trajectories(scenario, offer_strategy=True)
        return {"scenario": scenario.model_dump(), "model": "EXP-005", "summary": self._summary(treatment), "sample_trajectories": treatment[:10]}
