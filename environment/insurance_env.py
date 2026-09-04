"""Known, deliberately simple ground-truth dynamics for insurance behaviour."""
from __future__ import annotations
import math
import numpy as np
from .models import Action, ActionType, Channel, CustomerState, JourneyStage, Product

PRODUCT_COST = {Product.AUTO: 45.0, Product.HOME: 30.0, Product.LIFE: 38.0}
PRODUCT_BASE_PRICE = {Product.AUTO: 80.0, Product.HOME: 55.0, Product.LIFE: 65.0}


def sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-float(np.clip(value, -20, 20))))


class InsuranceEnvironment:
    """Synthetic MDP. Stochasticity is solely sourced from its seeded RNG."""
    def __init__(self, seed: int | None = None):
        self.rng = np.random.default_rng(seed)

    def initial_state(self) -> CustomerState:
        auto = bool(self.rng.random() < 0.48)
        home = bool(self.rng.random() < (0.24 + 0.16 * auto))
        life = bool(self.rng.random() < 0.20)
        policies = int(auto) + int(home) + int(life)
        affinity = float(np.clip(self.rng.beta(2, 2) + 0.08 * auto, 0, 1))
        trust = float(self.rng.beta(3, 2))
        stage = JourneyStage.CUSTOMER if policies else JourneyStage.UNAWARE
        return CustomerState(age=int(self.rng.integers(18, 76)), tenure_months=int(self.rng.integers(0, 121)),
            auto_policy=auto, home_policy=home, life_policy=life, claims_12m=int(self.rng.poisson(0.25)),
            premium_monthly=round(sum(PRODUCT_BASE_PRICE[p] for p, own in [(Product.AUTO, auto), (Product.HOME, home), (Product.LIFE, life)] if own), 2),
            digital_engagement=float(self.rng.beta(2, 3)), price_sensitivity=float(self.rng.beta(2, 2)),
            insurance_affinity=affinity, trust=trust, journey_stage=stage)

    def purchase_probability(self, state: CustomerState, action: Action) -> float:
        if action.product is None or action.product == Product.AUTO and state.auto_policy or action.product == Product.HOME and state.home_policy or action.product == Product.LIFE and state.life_policy:
            return 0.0
        channel = {Channel.APP: 1.2 * state.digital_engagement, Channel.EMAIL: 0.25 * state.digital_engagement,
                   Channel.BROKER: 0.55 + 0.45 * (1 - state.digital_engagement), Channel.CALL_CENTER: 0.20}[action.channel]
        price_effect = 2.8 * action.discount * state.price_sensitivity - 1.4 * (action.price / PRODUCT_BASE_PRICE[action.product] - 1) * state.price_sensitivity
        cross_sell = 0.35 if action.product == Product.HOME and state.auto_policy else 0.0
        stage = {JourneyStage.UNAWARE: -1.3, JourneyStage.AWARE: -0.8, JourneyStage.INTERESTED: -0.35, JourneyStage.QUOTING: 0.1, JourneyStage.CONSIDERING: 0.35, JourneyStage.CUSTOMER: -0.15, JourneyStage.CANCELLED: -1.0}[state.journey_stage]
        return sigmoid(-2.0 + 2.1 * state.insurance_affinity + 1.5 * state.trust + channel + price_effect + cross_sell + stage + self.rng.normal(0, 0.12))

    def step(self, state: CustomerState, action: Action):
        data = state.model_dump()
        info: dict = {"purchase_probability": 0.0, "purchased": False, "cancelled": False}
        reward = 0.0
        data["tenure_months"] += 1
        data["age"] = min(100, data["age"] + (1 if data["tenure_months"] % 12 == 0 else 0))
        # Claims decrease trust and increase price sensitivity; their process is otherwise stable.
        new_claim = self.rng.random() < min(0.18, 0.018 + 0.025 * data["claims_12m"])
        data["claims_12m"] = max(0, data["claims_12m"] - (1 if self.rng.random() < 0.08 else 0)) + int(new_claim)
        if new_claim:
            data["trust"] = max(0.0, data["trust"] - 0.10)
            data["price_sensitivity"] = min(1.0, data["price_sensitivity"] + 0.05)

        if action.action_type == ActionType.OFFER_PRODUCT:
            p = self.purchase_probability(state, action); info["purchase_probability"] = p
            data["journey_stage"] = JourneyStage.QUOTING if state.journey_stage not in (JourneyStage.CUSTOMER, JourneyStage.CANCELLED) else state.journey_stage
            if self.rng.random() < p:
                data[f"{action.product.value.lower()}_policy"] = True
                data["premium_monthly"] += action.price * (1 - action.discount)
                data["trust"] = min(1.0, data["trust"] + 0.06); data["insurance_affinity"] = min(1.0, data["insurance_affinity"] + 0.08)
                data["journey_stage"] = JourneyStage.CUSTOMER; info["purchased"] = True
                reward = action.price * (1 - action.discount) - PRODUCT_COST[action.product] - 8.0
            else:
                data["digital_engagement"] = max(0.0, data["digital_engagement"] - 0.03)
                if state.journey_stage != JourneyStage.CANCELLED: data["journey_stage"] = JourneyStage.CONSIDERING
                reward = -8.0
        elif action.action_type == ActionType.SEND_MESSAGE:
            data["digital_engagement"] = min(1.0, data["digital_engagement"] + 0.06)
            data["journey_stage"] = JourneyStage.AWARE if state.journey_stage == JourneyStage.UNAWARE else JourneyStage.INTERESTED
            reward = -1.0
        elif action.action_type == ActionType.CONTACT_BROKER:
            data["trust"] = min(1.0, data["trust"] + 0.07); data["journey_stage"] = JourneyStage.INTERESTED
            reward = -5.0
        elif action.action_type == ActionType.CHANGE_PRICE:
            delta = (action.discount or 0.05) * state.price_sensitivity
            data["premium_monthly"] *= (1 - delta); data["trust"] = min(1.0, data["trust"] + 0.02)
            reward = -state.premium_monthly * delta
        # Cancellation is more likely after claims and low trust; never cancels a non-customer.
        if state.journey_stage == JourneyStage.CUSTOMER and self.rng.random() < sigmoid(-4.2 + 2.4 * data["claims_12m"] - 2.3 * data["trust"]):
            data.update(auto_policy=False, home_policy=False, life_policy=False, premium_monthly=0.0, journey_stage=JourneyStage.CANCELLED)
            info["cancelled"] = True; reward -= 12.0
        next_state = CustomerState(**data)
        return next_state, float(reward), info
