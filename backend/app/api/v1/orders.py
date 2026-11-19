from datetime import datetime, UTC
import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.qr import create_qr_payload, verify_qr_payload
from app.core.events import order_events
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import (
    Order,
    OrderStatus,
    Product,
    Shop,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    User,
    UserRole,
)
from app.schemas.orders import (
    CreateOrderRequest,
    OrderResponse,
    OrderStatusUpdateRequest,
    QRPayloadResponse,
    VerifyQRRequest,
)


router = APIRouter(prefix="/orders", tags=["Orders"])

STATUS_ORDER = [
    OrderStatus.PENDING,
    OrderStatus.ACCEPTED,
    OrderStatus.PREPARING,
    OrderStatus.READY,
    OrderStatus.DELIVERED,
]


def serialize_order(order: Order) -> OrderResponse:
    created_at = order.created_at.isoformat()
    payload, _, qr_code = create_qr_payload(
        order.id,
        order.user_id,
        order.shop_id,
        created_at,
    )
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        shop_id=order.shop_id,
        product_id=order.product_id,
        shop_name=order.shop.name if order.shop else None,
        product_name=order.product.name if order.product else None,
        customer_name=order.user.full_name if order.user else None,
        customer_phone=order.user.phone_number if order.user else None,
        quantity=order.quantity,
        customizations=order.customizations,
        status=order.status.value,
        created_at=created_at,
        updated_at=order.updated_at.isoformat(),
        qr_payload=QRPayloadResponse(**payload),
        qr_code_data_url=qr_code,
    )


@router.post("", response_model=OrderResponse)
def create_order(
    payload: CreateOrderRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == SubscriptionStatus.ACTIVE,
    ).first()

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Aktif aboneliğiniz bulunmuyor. Sipariş vermek için paket satın alın.",
        )
    if (
        subscription.expires_at.replace(tzinfo=UTC) < datetime.now(UTC)
    ):
        subscription.status = SubscriptionStatus.CANCELLED
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Aboneliğinizin süresi dolmuş.",
        )
    if (
        subscription.plan_type != SubscriptionPlan.UNLIMITED
        and subscription.remaining_credits <= 0
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Aylık kahve hakkınız bitti.",
        )

    shop = db.query(Shop).filter(
        Shop.id == payload.shop_id,
        Shop.is_active == True,
    ).first()
    if shop is None:
        raise HTTPException(status_code=404, detail="Aktif dükkân bulunamadı.")

    product = db.query(Product).filter(
        Product.id == payload.product_id,
        Product.shop_id == payload.shop_id,
        Product.is_available == True,
    ).first()
    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Bu ürün dükkanda bulunamadı veya satışta değil.",
        )

    now = datetime.now(UTC)
    order = Order(
        user_id=user.id,
        shop_id=shop.id,
        product_id=product.id,
        quantity=1,
        customizations=payload.customizations,
        status=OrderStatus.PENDING,
        created_at=now,
        updated_at=now,
        qr_signature="",
    )
    db.add(order)
    db.flush()

    created_at = order.created_at.isoformat()
    _, _, _ = create_qr_payload(
        order.id,
        order.user_id,
        order.shop_id,
        created_at,
    )
    unsigned = {
        "order_id": order.id,
        "user_id": order.user_id,
        "shop_id": order.shop_id,
        "created_at": created_at,
    }
    import json
    import hashlib
    import hmac
    import os
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    order.qr_signature = hmac.new(
        os.getenv("QR_SECRET_KEY", "kahvecell-qr-development-secret").encode(),
        canonical.encode(),
        hashlib.sha256,
    ).hexdigest()

    if subscription.plan_type != SubscriptionPlan.UNLIMITED:
        subscription.remaining_credits -= 1

    db.commit()
    db.refresh(order)
    return serialize_order(order)


@router.get("/history", response_model=list[OrderResponse])
def order_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    orders = db.query(Order).filter(
        Order.user_id == user.id
    ).order_by(Order.created_at.desc()).all()
    return [serialize_order(order) for order in orders]


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")

    if order.user_id == user.id:
        return serialize_order(order)
    if user.role == UserRole.ADMIN:
        return serialize_order(order)

    shop = db.query(Shop).filter(
        Shop.id == order.shop_id,
        Shop.owner_id == user.id,
    ).first()
    if user.role == UserRole.SHOP_OWNER and shop is not None:
        return serialize_order(order)

    raise HTTPException(status_code=403, detail="Bu siparişe erişim yetkiniz yok.")


@router.get("/{order_id}/stream")
async def stream_order_status(
    order_id: str,
    access_token: str = Query(..., alias="access_token"),
    db: Session = Depends(get_db),
):
    try:
        payload = decode_access_token(access_token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Geçersiz erişim tokenı.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Geçersiz veya süresi dolmuş token.")

    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if user is None or not user.is_verified:
        raise HTTPException(status_code=401, detail="Kullanıcı doğrulanmamış.")

    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")

    if order.user_id != user.id:
        if user.role == UserRole.ADMIN:
            pass
        elif user.role == UserRole.SHOP_OWNER:
            shop = db.query(Shop).filter(
                Shop.id == order.shop_id,
                Shop.owner_id == user.id,
            ).first()
            if shop is None:
                raise HTTPException(status_code=403, detail="Bu siparişe erişim yetkiniz yok.")
        else:
            raise HTTPException(status_code=403, detail="Bu siparişe erişim yetkiniz yok.")

    subscriber = order_events.subscribe(order_id)
    loop, queue = subscriber

    async def event_stream():
        try:
            initial = json.dumps(
                {"order_id": order_id, "status": order.status.value},
                ensure_ascii=False,
            )
            yield f"data: {initial}\n\n"

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f"data: {event}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            order_events.unsubscribe(order_id, subscriber)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/shop/pending", response_model=list[OrderResponse])
def pending_shop_orders(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in (UserRole.SHOP_OWNER, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Dükkân sahibi yetkisi gerekli.")

    query = db.query(Order)
    if user.role == UserRole.SHOP_OWNER:
        owned_shop_ids = [
            shop.id for shop in db.query(Shop).filter(Shop.owner_id == user.id).all()
        ]
        if not owned_shop_ids:
            raise HTTPException(status_code=404, detail="Size ait dükkân bulunamadı.")
        query = query.filter(Order.shop_id.in_(owned_shop_ids))

    orders = query.order_by(Order.created_at.desc()).all()
    return [serialize_order(order) for order in orders]


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: str,
    payload: OrderStatusUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in (UserRole.SHOP_OWNER, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Sipariş durumunu dükkân sahibi veya yönetici güncelleyebilir.")

    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")

    if user.role == UserRole.SHOP_OWNER:
        shop = db.query(Shop).filter(
            Shop.id == order.shop_id,
            Shop.owner_id == user.id,
        ).first()
        if shop is None:
            raise HTTPException(status_code=403, detail="Bu sipariş size ait bir dükkana bağlı değil.")

    new_status = OrderStatus(payload.status)
    current_index = STATUS_ORDER.index(order.status)
    new_index = STATUS_ORDER.index(new_status)
    if new_index != current_index + 1:
        raise HTTPException(
            status_code=409,
            detail=f"Geçersiz durum geçişi: {order.status.value} -> {new_status.value}",
        )

    order.status = new_status
    order.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(order)
    order_events.publish(order.id, new_status.value)
    return serialize_order(order)


@router.post("/{order_id}/verify-qr")
def verify_order_qr(
    order_id: str,
    payload: VerifyQRRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in (UserRole.SHOP_OWNER, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="QR kodu dükkân sahibi veya yönetici doğrulayabilir.")

    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")

    if user.role == UserRole.SHOP_OWNER:
        shop = db.query(Shop).filter(
            Shop.id == order.shop_id,
            Shop.owner_id == user.id,
        ).first()
        if shop is None:
            raise HTTPException(status_code=403, detail="Bu QR size ait bir dükkana ait değil.")

    qr_payload = payload.qr_payload
    if not verify_qr_payload(qr_payload):
        raise HTTPException(status_code=400, detail="QR kod sahte veya değiştirildi.")
    if (
        qr_payload.get("order_id") != order.id
        or qr_payload.get("user_id") != order.user_id
        or qr_payload.get("shop_id") != order.shop_id
    ):
        raise HTTPException(status_code=400, detail="QR kod bu siparişe ait değil.")

    return {
        "valid": True,
        "message": "Evet, bu gerçek bir KahveCell sipariş QR kodu.",
        "order_id": order.id,
        "status": order.status.value,
    }
