import datetime as dt

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=6)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    is_admin: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- products ----------
class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = ""
    category: str = Field(min_length=1, max_length=80)
    price_paise: int = Field(gt=0)
    image_url: str = Field(min_length=1, max_length=500)
    stock: int = Field(default=0, ge=0)


class ProductCreate(ProductBase):
    slug: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    category: str | None = Field(default=None, min_length=1, max_length=80)
    price_paise: int | None = Field(default=None, gt=0)
    image_url: str | None = Field(default=None, max_length=500)
    stock: int | None = Field(default=None, ge=0)


class ProductOut(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    is_active: bool


# ---------- cart ----------
class CartItemIn(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)


class CartQuantityIn(BaseModel):
    quantity: int = Field(ge=1)


class CartItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quantity: int
    product: ProductOut


class CartOut(BaseModel):
    items: list[CartItemOut]
    total_paise: int


# ---------- checkout / orders ----------
class CheckoutIn(BaseModel):
    shipping_name: str = Field(min_length=1, max_length=120)
    shipping_phone: str = Field(min_length=6, max_length=20)
    shipping_address: str = Field(min_length=10)


class RazorpayVerifyIn(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class CheckoutOut(BaseModel):
    """Everything the frontend needs to open the Razorpay modal."""

    order_id: int
    razorpay_order_id: str
    amount_paise: int
    razorpay_key_id: str
    name: str = "MyShop"
    email: str


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_name: str
    unit_price_paise: int
    quantity: int


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    total_paise: int
    razorpay_order_id: str | None
    razorpay_payment_id: str | None
    shipping_name: str
    shipping_phone: str
    shipping_address: str
    created_at: dt.datetime
    items: list[OrderItemOut]


class AdminOrderOut(OrderOut):
    user_email: str | None


class OrderStatusIn(BaseModel):
    status: str = Field(pattern="^(created|paid|shipped|delivered|cancelled)$")
