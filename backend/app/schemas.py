from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(ch.isupper() for ch in value):
            raise ValueError("Password must include at least one uppercase character")
        if not any(ch.isdigit() for ch in value):
            raise ValueError("Password must include at least one number")
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str


class UserToken(BaseModel):
    token: str
    user: UserPublic


class BusinessCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    industry: str = Field(default="default", min_length=1, max_length=120)
    location: str | None = Field(default=None, max_length=255)
    language: str = Field(default="en", min_length=2, max_length=20)


class BusinessUpdate(BusinessCreate):
    pass


class WebsiteConfigCreate(BaseModel):
    website_name: str = Field(..., min_length=2, max_length=255)
    website_data: dict[str, Any] = Field(default_factory=dict)


class ProductCreate(BaseModel):
    business_id: str | None = None
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=2000)
    price: str = Field(..., min_length=1, max_length=120)
    category: str = Field(default="General", min_length=1, max_length=120)
    image_url: str | None = Field(default=None, max_length=500)
    featured: bool = False


class ProductUpdate(ProductCreate):
    pass


class PublishWebsiteRequest(BaseModel):
    business_id: str | None = None
    website: dict[str, Any] = Field(default_factory=dict)
    business_name: str | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    message: str | None = None


class CreateCheckoutRequest(BaseModel):
    plan_code: str = Field(..., min_length=1, max_length=50)


class VerifyPaymentRequest(BaseModel):
    plan_code: str = Field(..., min_length=1, max_length=50)
    razorpay_order_id: str = Field(..., min_length=1, max_length=200)
    razorpay_payment_id: str = Field(..., min_length=1, max_length=200)
    razorpay_signature: str = Field(..., min_length=1, max_length=255)


class SubscriptionPlanResponse(BaseModel):
    code: str
    name: str
    price: int
    currency: str
    description: str
    features: list[str]
    usage_limits: dict[str, int]


class SubscriptionSummary(BaseModel):
    plan_code: str
    plan_name: str
    status: str
    amount_paid: str
    currency: str
    started_at: str | None = None
    ends_at: str | None = None
    usage_limits: dict[str, int]
    current_usage: dict[str, int]


class PaymentRecord(BaseModel):
    id: str
    plan_code: str
    order_id: str | None = None
    payment_id: str | None = None
    status: str
    amount: str
    currency: str
    provider: str
    created_at: str | None = None
    verified_at: str | None = None
    failure_reason: str | None = None
