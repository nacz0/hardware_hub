from contextlib import asynccontextmanager
import re
import sqlite3
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from app.ai_audit import router as ai_audit_router
from app.auth import create_access_token, get_current_user, require_admin
from app.database import initialize_database
from app.hardware import router as hardware_router
from app.users import authenticate_user, create_user


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Hardware Hub API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(ai_audit_router)
app.include_router(hardware_router)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=72)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_valid_email(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_bcrypt_password(value)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    created_at: str


class UserCreateRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=72)
    role: Literal["admin", "user"] = "user"

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_valid_email(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_bcrypt_password(value)


def normalize_valid_email(value: str) -> str:
    normalized = value.strip().lower()
    if not EMAIL_PATTERN.fullmatch(normalized):
        raise ValueError("Valid email is required")
    return normalized


def validate_bcrypt_password(value: str) -> str:
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password must be 72 bytes or fewer")
    return value


def public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "created_at": user["created_at"],
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> dict[str, str]:
    user = authenticate_user(payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return {"access_token": create_access_token(user), "token_type": "bearer"}


@app.get("/auth/me", response_model=UserResponse)
def me(current_user: dict = Depends(get_current_user)) -> dict:
    return public_user(current_user)


@app.post(
    "/admin/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_account(
    payload: UserCreateRequest,
    _admin: dict = Depends(require_admin),
) -> dict:
    try:
        return create_user(payload.email, payload.password, payload.role)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        ) from None
