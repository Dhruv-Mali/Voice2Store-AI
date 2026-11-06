from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    businesses: Mapped[list["Business"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(120), default="default")
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(20), default="en")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    owner: Mapped[User] = relationship(back_populates="businesses")
    websites: Mapped[list["WebsiteConfiguration"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    products: Mapped[list["Product"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    published_sites: Mapped[list["PublishedSite"]] = relationship(back_populates="business", cascade="all, delete-orphan")


class WebsiteConfiguration(Base):
    __tablename__ = "website_configurations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id"), nullable=False, index=True)
    website_name: Mapped[str] = mapped_column(String(255), nullable=False)
    website_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True, default=dict)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    business: Mapped[Business] = relationship(back_populates="websites")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    price: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(120), default="General")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    business: Mapped[Business] = relationship(back_populates="products")


class PublishedSite(Base):
    __tablename__ = "published_sites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id"), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    share_url: Mapped[str] = mapped_column(String(500), nullable=False)
    qr_code_url: Mapped[str] = mapped_column(String(500), nullable=False)
    seo_title: Mapped[str] = mapped_column(String(200), nullable=False)
    seo_description: Mapped[str] = mapped_column(String(400), nullable=False)
    website_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    whatsapp_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    business: Mapped[Business] = relationship(back_populates="published_sites")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    plan_code: Mapped[str] = mapped_column(String(50), nullable=False, default="free")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    amount_paid: Mapped[str] = mapped_column(String(50), nullable=False, default="0")
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")
    started_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ends_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    usage_limits: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    current_usage: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    last_payment_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="subscriptions")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    plan_code: Mapped[str] = mapped_column(String(50), nullable=False, default="free")
    order_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    payment_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    signature: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[str] = mapped_column(String(50), nullable=False, default="0")
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="razorpay")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    verified_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="payments")
