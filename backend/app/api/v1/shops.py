from math import asin, cos, radians, sin, sqrt

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Product, Shop
from app.schemas.shops import (
    ProductResponse,
    ShopDetailResponse,
    ShopResponse,
)
from fastapi import Depends


router = APIRouter(prefix="/shops", tags=["Shops"])

EARTH_RADIUS_KM = 6371.0


def haversine_distance(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    lat_1 = radians(latitude_1)
    lat_2 = radians(latitude_2)
    delta_lat = radians(latitude_2 - latitude_1)
    delta_lng = radians(longitude_2 - longitude_1)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat_1) * cos(lat_2) * sin(delta_lng / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def serialize_shop(
    shop: Shop,
    distance_km: float | None = None,
) -> ShopResponse:
    return ShopResponse(
        id=shop.id,
        name=shop.name,
        address=shop.address,
        latitude=shop.latitude,
        longitude=shop.longitude,
        opening_hours=shop.opening_hours,
        rating=shop.rating,
        photo_url=shop.photo_url,
        is_active=shop.is_active,
        distance_km=None if distance_km is None else round(distance_km, 2),
    )


@router.get("", response_model=list[ShopResponse])
def list_shops(
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
    radius: float | None = Query(default=None, gt=0),
    search: str | None = Query(default=None, min_length=1),
    db: Session = Depends(get_db),
):
    query = db.query(Shop)

    if lat is not None and lng is None:
        raise HTTPException(status_code=422, detail="lng parametresi lat ile birlikte gönderilmelidir.")
    if lng is not None and lat is None:
        raise HTTPException(status_code=422, detail="lat parametresi lng ile birlikte gönderilmelidir.")

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(Shop.name.ilike(term), Shop.address.ilike(term))
        )

    shops = query.all()
    result: list[tuple[float | None, Shop]] = []

    for shop in shops:
        distance = None
        if lat is not None and lng is not None:
            distance = haversine_distance(lat, lng, shop.latitude, shop.longitude)
            if radius is not None and distance > radius:
                continue
        result.append((distance, shop))

    if lat is not None and lng is not None:
        result.sort(key=lambda item: item[0])
    else:
        result.sort(key=lambda item: item[1].name.lower())

    return [
        serialize_shop(shop, distance)
        for distance, shop in result
    ]


@router.get("/{shop_id}", response_model=ShopDetailResponse)
def get_shop_detail(
    shop_id: str,
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
    db: Session = Depends(get_db),
):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if shop is None:
        raise HTTPException(status_code=404, detail="Dükkân bulunamadı.")

    distance = None
    if lat is not None and lng is not None:
        distance = haversine_distance(lat, lng, shop.latitude, shop.longitude)
    elif lat is not None or lng is not None:
        raise HTTPException(status_code=422, detail="lat ve lng birlikte gönderilmelidir.")

    menu = db.query(Product).filter(Product.shop_id == shop.id).all()
    menu.sort(key=lambda product: product.name.lower())

    return ShopDetailResponse(
        id=shop.id,
        name=shop.name,
        address=shop.address,
        latitude=shop.latitude,
        longitude=shop.longitude,
        opening_hours=shop.opening_hours,
        rating=shop.rating,
        photo_url=shop.photo_url,
        is_active=shop.is_active,
        distance_km=None if distance is None else round(distance, 2),
        menu=[
            ProductResponse(
                id=product.id,
                name=product.name,
                description=product.description,
                price=float(product.price),
                image_url=product.image_url,
                is_available=product.is_available,
                category=product.category,
            )
            for product in menu
        ],
    )


@router.get("/{shop_id}/menu", response_model=list[ProductResponse])
def get_shop_menu(shop_id: str, db: Session = Depends(get_db)):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if shop is None:
        raise HTTPException(status_code=404, detail="Dükkân bulunamadı.")

    products = db.query(Product).filter(Product.shop_id == shop_id).all()
    products.sort(key=lambda product: product.name.lower())
    return [
        ProductResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            price=float(product.price),
            image_url=product.image_url,
            is_available=product.is_available,
            category=product.category,
        )
        for product in products
    ]
