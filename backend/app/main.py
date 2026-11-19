from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import sqlite3
from pathlib import Path
import os

from app.db.session import engine
from app.models import Base
from app.api.v1.auth import router as auth_router
from app.api.v1.subscriptions import router as subscriptions_router
from app.api.v1.shops import router as shops_router
from app.api.v1.orders import router as orders_router


app = FastAPI(title="KahveCell API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(subscriptions_router, prefix="/api/v1")
app.include_router(shops_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")


@app.on_event("startup")
def create_database_tables() -> None:
    Base.metadata.create_all(bind=engine)
    database_url = os.getenv("DATABASE_URL")
    if database_url and database_url.startswith("sqlite:///"):
        database_file = Path(database_url.removeprefix("sqlite:///"))
        if not database_file.is_absolute():
            database_file = Path(__file__).resolve().parents[1] / database_file
    else:
        database_file = Path(__file__).resolve().parents[1] / "kahvecell.db"
    connection = sqlite3.connect(database_file)
    try:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(users)").fetchall()
        }
        if "is_verified" not in columns:
            connection.execute(
                "ALTER TABLE users ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT 0"
            )
            connection.commit()
    finally:
        connection.close()

    try:
        from seed import seed
        seed()
    except Exception as exc:
        print(f"Seed data yüklenemedi: {exc}")


@app.get("/", response_class=PlainTextResponse)
def read_root() -> str:
    return "çalışıyor"


@app.get("/api/v1/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
