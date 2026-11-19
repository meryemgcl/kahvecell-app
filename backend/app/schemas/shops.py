from pydantic import BaseModel, Field


class ProductResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    price: float
    image_url: str | None = None
    is_available: bool
    category: str | None = None


class ShopResponse(BaseModel):
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    opening_hours: dict | None = None
    rating: float
    photo_url: str | None = None
    is_active: bool
    distance_km: float | None = None


class ShopDetailResponse(ShopResponse):
    menu: list[ProductResponse] = Field(default_factory=list)
