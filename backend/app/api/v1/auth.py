from datetime import datetime, timedelta, UTC

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    ACCESS_TOKEN_MINUTES,
    REFRESH_TOKEN_DAYS,
    OTP_CODE,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_value,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models import (
    OTPRequest,
    RefreshToken,
    User,
    UserRole,
)
from app.schemas.auth import (
    OTPRequest as OTPRequestSchema,
    OTPResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    VerifyOTPRequest,
    ProfileUpdateRequest,
    LoginRequest,
)


router = APIRouter(prefix="/auth", tags=["Authentication"])


def normalize_phone(phone_number: str) -> str:
    return phone_number.replace(" ", "").replace("-", "")


def invalidate_old_otps(db: Session, phone_number: str) -> None:
    db.query(OTPRequest).filter(
        OTPRequest.phone_number == phone_number,
        OTPRequest.is_used == False,
    ).update({"is_used": True})


def create_otp(db: Session, phone_number: str) -> OTPRequest:
    invalidate_old_otps(db, phone_number)
    otp = OTPRequest(
        phone_number=phone_number,
        code_hash=hash_value(OTP_CODE),
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    db.add(otp)
    db.commit()
    db.refresh(otp)
    return otp


def create_session(db: Session, user: User) -> TokenResponse:
    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_value(refresh_token),
            expires_at=datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_DAYS),
        )
    )
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=OTPResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    phone_number = normalize_phone(payload.phone_number)
    user = db.query(User).filter(User.phone_number == phone_number).first()

    if user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu GSM numarasıyla kayıtlı bir kullanıcı zaten var.",
        )

    user = User(
        phone_number=phone_number,
        full_name=payload.full_name or "",
        email=str(payload.email) if payload.email else None,
        password_hash=hash_password(payload.password),
        role=UserRole.CUSTOMER,
        is_verified=False,
    )
    db.add(user)
    db.flush()
    create_otp(db, phone_number)

    return OTPResponse(
        success=True,
        message="OTP gönderildi. Simülasyon kodu: 1234",
    )


@router.post("/request-otp", response_model=OTPResponse)
def request_otp(payload: OTPRequestSchema, db: Session = Depends(get_db)):
    phone_number = normalize_phone(payload.phone_number)
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bu GSM numarasıyla kayıtlı kullanıcı bulunamadı.",
        )

    create_otp(db, phone_number)
    return OTPResponse(
        success=True,
        message="Giriş OTP'si gönderildi. Simülasyon kodu: 1234",
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    phone_number = normalize_phone(payload.phone_number)
    user = db.query(User).filter(User.phone_number == phone_number).first()

    if (
        user is None
        or not user.password_hash
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telefon numarası veya şifre hatalı.",
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Telefon numarası henüz doğrulanmadı.",
        )

    return create_session(db, user)


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(payload: VerifyOTPRequest, db: Session = Depends(get_db)):
    phone_number = normalize_phone(payload.phone_number)
    otp = (
        db.query(OTPRequest)
        .filter(
            OTPRequest.phone_number == phone_number,
            OTPRequest.is_used == False,
        )
        .order_by(OTPRequest.created_at.desc())
        .first()
    )

    if otp is None:
        raise HTTPException(status_code=400, detail="Geçerli OTP bulunamadı.")
    if otp.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        otp.is_used = True
        db.commit()
        raise HTTPException(status_code=400, detail="OTP süresi dolmuş.")
    if otp.attempts >= 5:
        otp.is_used = True
        db.commit()
        raise HTTPException(status_code=429, detail="Çok fazla başarısız deneme.")
    if hash_value(payload.code) != otp.code_hash:
        otp.attempts += 1
        db.commit()
        raise HTTPException(status_code=400, detail="OTP kodu hatalı.")

    otp.is_used = True
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if user is None:
        db.rollback()
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    user.is_verified = True
    db.commit()
    db.refresh(user)
    return create_session(db, user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hash_value(payload.refresh_token)
    record = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked == False,
    ).first()

    if record is None:
        raise HTTPException(status_code=401, detail="Geçersiz refresh token.")
    if record.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        record.revoked = True
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token süresi dolmuş.")

    user = db.query(User).filter(User.id == record.user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı.")

    record.revoked = True
    db.commit()
    return create_session(db, user)


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if authorization is None or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Erişim tokenı gerekli.")

    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Geçersiz erişim tokenı.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Geçersiz veya süresi dolmuş token.")

    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if user is None or not user.is_verified:
        raise HTTPException(status_code=401, detail="Kullanıcı doğrulanmamış.")
    return user


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return UserResponse(
        id=user.id,
        phone_number=user.phone_number,
        full_name=user.full_name,
        email=user.email,
        role=user.role.value,
        is_verified=user.is_verified,
    )


@router.patch("/me", response_model=UserResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.full_name = payload.full_name
    user.email = str(payload.email) if payload.email else None
    if payload.preferences is not None:
        user.preferences = payload.preferences

    db.commit()
    db.refresh(user)
    return UserResponse(
        id=user.id,
        phone_number=user.phone_number,
        full_name=user.full_name,
        email=user.email,
        role=user.role.value,
        is_verified=user.is_verified,
    )
