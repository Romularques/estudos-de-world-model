"""Typed contracts for the synthetic insurance environment."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class Product(str, Enum):
    AUTO = "AUTO"
    HOME = "HOME"
    LIFE = "LIFE"


class Channel(str, Enum):
    APP = "APP"
    EMAIL = "EMAIL"
    BROKER = "BROKER"
    CALL_CENTER = "CALL_CENTER"


class ActionType(str, Enum):
    NO_ACTION = "NO_ACTION"
    OFFER_PRODUCT = "OFFER_PRODUCT"
    SEND_MESSAGE = "SEND_MESSAGE"
    CONTACT_BROKER = "CONTACT_BROKER"
    CHANGE_PRICE = "CHANGE_PRICE"


class JourneyStage(str, Enum):
    UNAWARE = "UNAWARE"
    AWARE = "AWARE"
    INTERESTED = "INTERESTED"
    QUOTING = "QUOTING"
    CONSIDERING = "CONSIDERING"
    CUSTOMER = "CUSTOMER"
    CANCELLED = "CANCELLED"


class Action(BaseModel):
    action_type: ActionType
    product: Optional[Product] = None
    price: Optional[float] = Field(default=None, gt=0)
    channel: Optional[Channel] = None
    discount: float = Field(default=0.0, ge=0.0, le=0.8)

    @model_validator(mode="after")
    def validate_offer_fields(self):
        if self.action_type == ActionType.OFFER_PRODUCT:
            if self.product is None or self.price is None or self.channel is None:
                raise ValueError("OFFER_PRODUCT requires product, price and channel")
        return self


class CustomerState(BaseModel):
    age: int = Field(ge=18, le=100)
    tenure_months: int = Field(ge=0)
    auto_policy: bool
    home_policy: bool
    life_policy: bool
    claims_12m: int = Field(ge=0, le=20)
    premium_monthly: float = Field(ge=0)
    digital_engagement: float = Field(ge=0, le=1)
    price_sensitivity: float = Field(ge=0, le=1)  # latent by default
    insurance_affinity: float = Field(ge=0, le=1)  # latent by default
    trust: float = Field(ge=0, le=1)  # latent by default
    journey_stage: JourneyStage

    def observable(self, include_latent: bool = False) -> dict:
        payload = self.model_dump(mode="json")
        if not include_latent:
            for key in ("price_sensitivity", "insurance_affinity", "trust"):
                payload.pop(key)
        return payload
