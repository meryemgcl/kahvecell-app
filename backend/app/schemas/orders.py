from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    shop_id: str = Field(min_length=36, max_length=36)
    product_id: str = Field(min_length=36, max_length=36)
    customizations: dict | None = None


class QRPayloadResponse(BaseModel):
    order_id: str
    user_id: str
    shop_id: str
    created_at: str
    signature: str


class OrderResponse(BaseModel):
    id: str
    user_id: str
    shop_id: str
    product_id: str
    shop_name: str | None = None
    product_name: str | None = None
    customer_name: str | None = None
    customer_phone: str | None = None
    quantity: int
    customizations: dict | None = None
    status: str
    created_at: str
    updated_at: str
    qr_payload: QRPayloadResponse
    qr_code_data_url: str


class OrderStatusUpdateRequest(BaseModel):
    status: str = Field(pattern=r"^(ACCEPTED|PREPARING|READY|DELIVERED)$")


class VerifyQRRequest(BaseModel):
    qr_payload: dict
