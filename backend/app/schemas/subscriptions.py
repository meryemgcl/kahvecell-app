from pydantic import BaseModel, Field
from typing import Literal


class PlanResponse(BaseModel):
    plan_type: Literal["STARTER", "PREMIUM", "UNLIMITED"]
    name: str
    monthly_price: float
    monthly_credits: int
    guest_credits: int
    priority_support: bool


class ProcessPaymentRequest(BaseModel):
    subscription_plan: Literal["STARTER", "PREMIUM", "UNLIMITED"]
    card_token: str = Field(min_length=3, max_length=50)


class SubscriptionRequest(BaseModel):
    plan_type: Literal["STARTER", "PREMIUM", "UNLIMITED"]
    card_token: str = Field(min_length=3, max_length=50)


class SubscriptionUpdateRequest(BaseModel):
    plan_type: Literal["STARTER", "PREMIUM", "UNLIMITED"]
    card_token: str = Field(min_length=3, max_length=50)


class SubscriptionResponse(BaseModel):
    id: str
    plan_type: str
    remaining_credits: int
    status: str
    started_at: str
    expires_at: str


class PaymentResponse(BaseModel):
    success: bool
    transaction_id: str
    amount: float
    timestamp: str
    status: str
