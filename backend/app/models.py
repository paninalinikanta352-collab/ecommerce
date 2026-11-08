import datetime as dt

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(80), index=True)
    # Money is stored as integer paise (₹1 = 100 paise). Never use floats for money.
    price_paise: Mapped[int] = mapped_column(Integer)
    image_url: Mapped[str] = mapped_column(String(500))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    user = relationship("User")
    product = relationship("Product")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # created -> paid -> shipped -> delivered  (failed / cancelled as terminal miss-states)
    status: Mapped[str] = mapped_column(String(20), default="created", index=True)
    total_paise: Mapped[int] = mapped_column(Integer)
    razorpay_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipping_name: Mapped[str] = mapped_column(String(120))
    shipping_phone: Mapped[str] = mapped_column(String(20))
    shipping_address: Mapped[str] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    user = relationship("User")

    @property
    def user_email(self) -> str | None:
        return self.user.email if self.user else None


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    # Snapshot fields: orders must survive the product being renamed/deleted later.
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    product_name: Mapped[str] = mapped_column(String(160))
    unit_price_paise: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
