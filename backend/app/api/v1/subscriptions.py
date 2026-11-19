from datetime import datetime, timedelta, UTC
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db.session import get_db
from app.models import (
    Payment,
    PaymentStatus,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    User,
)
from app.schemas.subscriptions import (
    PaymentResponse,
    PlanResponse,
    ProcessPaymentRequest,
    SubscriptionRequest,
    SubscriptionResponse,
    SubscriptionUpdateRequest,
)


router = APIRouter(tags=["Subscriptions"])

PLANS = {
    SubscriptionPlan.STARTER: {
        "plan_type": "STARTER",
        "name": "Starter",
        "monthly_price": 89.99,
        "monthly_credits": 10,
        "guest_credits": 0,
        "priority_support": False,
    },
    SubscriptionPlan.PREMIUM: {
        "plan_type": "PREMIUM",
        "name": "Premium",
        "monthly_price": 149.99,
        "monthly_credits": 20,
        "guest_credits": 2,
        "priority_support": False,
    },
    SubscriptionPlan.UNLIMITED: {
        "plan_type": "UNLIMITED",
        "name": "Unlimited",
        "monthly_price": 249.99,
        "monthly_credits": -1,
        "guest_credits": 5,
        "priority_support": True,
    },
}

SUCCESS_CARD = "4242-4242-4242-4242"
FAILED_CARD = "4000-0000-0000-0002"


def normalize_card(card_token: str) -> str:
    return card_token.replace("-", "").replace(" ", "")


def plan_enum(value: str) -> SubscriptionPlan:
    return SubscriptionPlan(value)


def active_subscription(db: Session, user_id: str) -> Subscription | None:
    return db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status == SubscriptionStatus.ACTIVE,
    ).first()


def serialize_subscription(subscription: Subscription) -> SubscriptionResponse:
    return SubscriptionResponse(
        id=subscription.id,
        plan_type=subscription.plan_type.value,
        remaining_credits=subscription.remaining_credits,
        status=subscription.status.value,
        started_at=subscription.started_at.isoformat(),
        expires_at=subscription.expires_at.isoformat(),
    )


def process_mock_payment(
    db: Session,
    user: User,
    plan_type: SubscriptionPlan,
    card_token: str,
    subscription_id: str | None = None,
) -> PaymentResponse:
    card = normalize_card(card_token)
    is_success = card == SUCCESS_CARD.replace("-", "")
    transaction_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    amount = PLANS[plan_type]["monthly_price"]

    payment = Payment(
        user_id=user.id,
        subscription_id=subscription_id,
        plan_type=plan_type,
        amount=amount,
        status=PaymentStatus.SUCCESS if is_success else PaymentStatus.FAILED,
        transaction_id=transaction_id,
        created_at=now,
    )
    db.add(payment)
    db.flush()

    if not is_success:
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "success": False,
                "transaction_id": transaction_id,
                "amount": amount,
                "timestamp": now.isoformat(),
                "status": "FAILED",
            },
        )

    return PaymentResponse(
        success=True,
        transaction_id=transaction_id,
        amount=amount,
        timestamp=now.isoformat(),
        status="SUCCESS",
    )


@router.get("/subscriptions/plans", response_model=list[PlanResponse])
def list_plans():
    return [PlanResponse(**plan) for plan in PLANS.values()]


@router.post("/payments/process", response_model=PaymentResponse)
def process_payment(
    payload: ProcessPaymentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan_type = plan_enum(payload.subscription_plan)
    return process_mock_payment(db, user, plan_type, payload.card_token)


@router.post("/subscriptions", response_model=SubscriptionResponse)
def purchase_subscription(
    payload: SubscriptionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan_type = plan_enum(payload.plan_type)
    existing = active_subscription(db, user.id)

    payment = process_mock_payment(db, user, plan_type, payload.card_token)

    if existing is not None:
        existing.plan_type = plan_type
        existing.remaining_credits = PLANS[plan_type]["monthly_credits"]
        existing.status = SubscriptionStatus.ACTIVE
        existing.started_at = datetime.now(UTC)
        existing.expires_at = datetime.now(UTC) + timedelta(days=30)
        subscription = existing
        payment_subscription_id = existing.id
    else:
        subscription = Subscription(
            user_id=user.id,
            plan_type=plan_type,
            remaining_credits=PLANS[plan_type]["monthly_credits"],
            status=SubscriptionStatus.ACTIVE,
            started_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
        db.add(subscription)
        db.flush()
        payment_subscription_id = subscription.id

    payment_record = db.query(Payment).filter(
        Payment.transaction_id == payment.transaction_id
    ).first()
    if payment_record is not None:
        payment_record.subscription_id = payment_subscription_id

    db.commit()
    db.refresh(subscription)
    return serialize_subscription(subscription)


@router.get("/subscriptions/me", response_model=SubscriptionResponse)
def get_my_subscription(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subscription = active_subscription(db, user.id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="Aktif abonelik bulunamadı.")
    return serialize_subscription(subscription)


@router.patch("/subscriptions/me", response_model=SubscriptionResponse)
def change_subscription(
    payload: SubscriptionUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subscription = active_subscription(db, user.id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="Aktif abonelik bulunamadı.")

    new_plan = plan_enum(payload.plan_type)
    process_mock_payment(
        db,
        user,
        new_plan,
        payload.card_token,
        subscription.id,
    )

    subscription.plan_type = new_plan
    subscription.remaining_credits = PLANS[new_plan]["monthly_credits"]
    subscription.status = SubscriptionStatus.ACTIVE
    subscription.started_at = datetime.now(UTC)
    subscription.expires_at = datetime.now(UTC) + timedelta(days=30)
    db.commit()
    db.refresh(subscription)
    return serialize_subscription(subscription)


@router.delete("/subscriptions/me")
def cancel_subscription(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subscription = active_subscription(db, user.id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="Aktif abonelik bulunamadı.")

    subscription.status = SubscriptionStatus.CANCELLED
    subscription.remaining_credits = 0
    db.commit()
    return {"success": True, "message": "Abonelik iptal edildi."}


@router.get("/payments/history")
def payment_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payments = db.query(Payment).filter(Payment.user_id == user.id).order_by(
        Payment.created_at.desc()
    ).all()
    return [
        {
            "transaction_id": payment.transaction_id,
            "plan_type": payment.plan_type.value,
            "amount": float(payment.amount),
            "status": payment.status.value,
            "timestamp": payment.created_at.isoformat(),
        }
        for payment in payments
    ]
