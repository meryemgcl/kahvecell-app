from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    phone_number: str = Field(min_length=10, max_length=15, pattern=r"^\+?[0-9]{10,15}$")
    full_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    password: str = Field(min_length=6, max_length=72)


class LoginRequest(BaseModel):
    phone_number: str = Field(min_length=10, max_length=15, pattern=r"^\+?[0-9]{10,15}$")
    password: str = Field(min_length=6, max_length=72)


class OTPRequest(BaseModel):
    phone_number: str = Field(min_length=10, max_length=15, pattern=r"^\+?[0-9]{10,15}$")


class VerifyOTPRequest(BaseModel):
    phone_number: str = Field(min_length=10, max_length=15, pattern=r"^\+?[0-9]{10,15}$")
    code: str = Field(min_length=4, max_length=4, pattern=r"^[0-9]{4}$")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class OTPResponse(BaseModel):
    success: bool
    message: str


class UserResponse(BaseModel):
    id: str
    phone_number: str
    full_name: str | None = None
    email: str | None = None
    role: str
    is_verified: bool


class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr | None = None
    preferences: dict | None = None
