import hashlib
import sqlite3
from datetime import datetime, timedelta, UTC
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.session import engine
from app.models import (
    Base,
    Product,
    Shop,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    User,
    UserRole,
)


BACKEND_DIR = Path(__file__).resolve().parent
DATABASE_FILE = BACKEND_DIR / "kahvecell.db"

TEST_PHONE = "05321234567"
TEST_PASSWORD = "Ankara123!"
TEST_FULL_NAME = "Ankara Test Kullanıcı"
TEST_EMAIL = "test@kahvecell.local"
SHOP_OWNER_PHONE = "05329876543"
SHOP_OWNER_PASSWORD = "Sahip123!"
SHOP_OWNER_FULL_NAME = "Kızılay Dükkân Sahibi"


SHOPS = [
    {
        "name": "KahveCell Kızılay",
        "address": "Kızılay Meydanı, Çankaya, Ankara",
        "latitude": 39.9208,
        "longitude": 32.8541,
        "opening_hours": {"weekdays": "08:00-23:00", "weekend": "09:00-23:00"},
    },
    {
        "name": "KahveCell Çankaya",
        "address": "Çankaya Caddesi, Çankaya, Ankara",
        "latitude": 39.8916,
        "longitude": 32.8662,
        "opening_hours": {"weekdays": "08:00-22:30", "weekend": "09:00-23:00"},
    },
    {
        "name": "KahveCell Bahçelievler",
        "address": "Bahçelievler 7. Cadde, Çankaya, Ankara",
        "latitude": 39.9542,
        "longitude": 32.8187,
        "opening_hours": {"weekdays": "08:00-22:00", "weekend": "09:00-22:00"},
    },
    {
        "name": "KahveCell Çayyolu",
        "address": "Çayyolu 19 Mayıs Caddesi, Çankaya, Ankara",
        "latitude": 39.8750,
        "longitude": 32.7022,
        "opening_hours": {"weekdays": "07:30-22:30", "weekend": "08:30-23:00"},
    },
    {
        "name": "KahveCell Tuna",
        "address": "Tuna Caddesi, Bahçelievler, Ankara",
        "latitude": 39.9488,
        "longitude": 32.8213,
        "opening_hours": {"weekdays": "08:00-22:00", "weekend": "09:00-22:30"},
    },
]


PRODUCTS = [
    ("Espresso", "Yoğun ve kısa servis edilen klasik espresso", 55.00, "hot"),
    ("Americano", "Espresso ve sıcak su dengesi", 65.00, "hot"),
    ("Cappuccino", "Espresso, süt ve süt köpüğü", 85.00, "hot"),
    ("Latte", "Sütlü ve yumuşak içim kahve", 90.00, "hot"),
    ("Türk Kahvesi", "Geleneksel ince çekim Türk kahvesi", 70.00, "hot"),
    ("Filtre Kahve", "Günlük demleme filtre kahve", 75.00, "hot"),
]


def ensure_password_column() -> None:
    if not DATABASE_FILE.exists():
        return

    connection = sqlite3.connect(DATABASE_FILE)
    try:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(users)").fetchall()
        }
        if "password_hash" not in columns:
            connection.execute(
                "ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"
            )
        if "is_verified" not in columns:
            connection.execute(
                "ALTER TABLE users ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT 0"
            )
        connection.commit()
    finally:
        connection.close()


def hash_password(password: str) -> str:
    salt = "kahvecell-static-education-salt"
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()


def seed() -> None:
    ensure_password_column()
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        test_user = db.query(User).filter(User.phone_number == TEST_PHONE).first()
        if test_user is None:
            test_user = User(
                phone_number=TEST_PHONE,
                full_name=TEST_FULL_NAME,
                email=TEST_EMAIL,
                role=UserRole.CUSTOMER,
                is_verified=True,
                password_hash=hash_password(TEST_PASSWORD),
                preferences={
                    "coffee_types": ["Espresso", "Türk Kahvesi"],
                    "allergens": [],
                },
            )
            db.add(test_user)
            db.flush()
        else:
            test_user.full_name = TEST_FULL_NAME
            test_user.email = TEST_EMAIL
            test_user.role = UserRole.CUSTOMER
            test_user.is_verified = True
            test_user.password_hash = hash_password(TEST_PASSWORD)

        subscription = (
            db.query(Subscription)
            .filter(
                Subscription.user_id == test_user.id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
            .first()
        )
        if subscription is None:
            db.add(
                Subscription(
                    user=test_user,
                    plan_type=SubscriptionPlan.STARTER,
                    remaining_credits=10,
                    status=SubscriptionStatus.ACTIVE,
                    started_at=datetime.now(UTC),
                    expires_at=datetime.now(UTC) + timedelta(days=30),
                )
            )

        for shop_seed in SHOPS:
            shop = db.query(Shop).filter(Shop.name == shop_seed["name"]).first()
            if shop is None:
                shop = Shop(
                    name=shop_seed["name"],
                    address=shop_seed["address"],
                    latitude=shop_seed["latitude"],
                    longitude=shop_seed["longitude"],
                    opening_hours=shop_seed["opening_hours"],
                    rating=4.6,
                    is_active=True,
                )
                db.add(shop)
                db.flush()

            for name, description, price, category in PRODUCTS:
                product = (
                    db.query(Product)
                    .filter(
                        Product.shop_id == shop.id,
                        Product.name == name,
                    )
                    .first()
                )
                if product is None:
                    db.add(
                        Product(
                            shop_id=shop.id,
                            name=name,
                            description=description,
                            price=price,
                            is_available=True,
                            category=category,
                        )
                    )

        shop_owner = db.query(User).filter(User.phone_number == SHOP_OWNER_PHONE).first()
        if shop_owner is None:
            shop_owner = User(
                phone_number=SHOP_OWNER_PHONE,
                full_name=SHOP_OWNER_FULL_NAME,
                role=UserRole.SHOP_OWNER,
                is_verified=True,
                password_hash=hash_password(SHOP_OWNER_PASSWORD),
            )
            db.add(shop_owner)
            db.flush()
        else:
            shop_owner.full_name = SHOP_OWNER_FULL_NAME
            shop_owner.role = UserRole.SHOP_OWNER
            shop_owner.is_verified = True
            shop_owner.password_hash = hash_password(SHOP_OWNER_PASSWORD)

        kizilay_shop = db.query(Shop).filter(Shop.name == "KahveCell Kızılay").first()
        if kizilay_shop is not None:
            kizilay_shop.owner_id = shop_owner.id

        db.commit()

        print(f"Dükkân sayısı: {db.query(Shop).count()}")
        print(f"Ürün sayısı: {db.query(Product).count()}")
        print(f"Kullanıcı sayısı: {db.query(User).count()}")
        print(f"Abonelik sayısı: {db.query(Subscription).count()}")

    print("Seed data başarıyla oluşturuldu.")
    print(f"Telefon: {TEST_PHONE}")
    print(f"Şifre: {TEST_PASSWORD}")
    print(f"Dükkân sahibi telefonu: {SHOP_OWNER_PHONE}")
    print(f"Dükkân sahibi OTP: 1234")
    print("Abonelik: STARTER, ACTIVE, 10 kahve hakkı")
    print("Dükkân: 5")


if __name__ == "__main__":
    seed()
