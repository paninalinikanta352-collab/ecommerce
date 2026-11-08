import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..deps import get_current_user
from ..models import CartItem, Order, OrderItem, Product, User
from ..schemas import CheckoutIn, CheckoutOut, OrderOut, RazorpayVerifyIn
from ..utils.razorpay import create_razorpay_order, settings, verify_payment_signature

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=CheckoutOut, status_code=status.HTTP_201_CREATED)
def create_order(
    data: CheckoutIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Turn the cart into an order and create the matching Razorpay order."""
    if not settings.gateway_configured:
        raise HTTPException(503, "Payment gateway is not configured on the server")

    cart_items = (
        db.scalars(
            select(CartItem)
            .where(CartItem.user_id == user.id)
            .options(joinedload(CartItem.product))
        )
        .unique()
        .all()
    )
    if not cart_items:
        raise HTTPException(400, "Your cart is empty")

    for item in cart_items:
        if item.product.stock < item.quantity:
            raise HTTPException(400, f"Only {item.product.stock} left of {item.product.name}")

    total = sum(i.product.price_paise * i.quantity for i in cart_items)

    rp_order = create_razorpay_order(
        amount_paise=total,
        receipt=f"user{user.id}-t{int(time.time())}",
    )

    order = Order(
        user_id=user.id,
        status="created",
        total_paise=total,
        razorpay_order_id=rp_order["id"],
        shipping_name=data.shipping_name,
        shipping_phone=data.shipping_phone,
        shipping_address=data.shipping_address,
    )
    for item in cart_items:
        order.items.append(
            OrderItem(
                product_id=item.product_id,
                product_name=item.product.name,
                unit_price_paise=item.product.price_paise,
                quantity=item.quantity,
            )
        )
    db.add(order)
    db.commit()
    db.refresh(order)

    return CheckoutOut(
        order_id=order.id,
        razorpay_order_id=order.razorpay_order_id,
        amount_paise=order.total_paise,
        razorpay_key_id=settings.RAZORPAY_KEY_ID,
        email=user.email,
    )


@router.post("/verify", response_model=OrderOut)
def verify_payment(
    data: RazorpayVerifyIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Frontend calls this after the Razorpay modal succeeds. Verifies the
    signature so nobody can fake a payment from the browser."""
    order = db.scalar(
        select(Order).where(
            Order.razorpay_order_id == data.razorpay_order_id,
            Order.user_id == user.id,
        )
    )
    if order is None:
        raise HTTPException(404, "Order not found")

    if order.status == "paid":  # idempotent: double-verify is fine
        return order

    if not verify_payment_signature(
        razorpay_order_id=data.razorpay_order_id,
        razorpay_payment_id=data.razorpay_payment_id,
        signature=data.razorpay_signature,
    ):
        order.status = "failed"
        db.commit()
        raise HTTPException(400, "Payment signature verification failed")

    order.status = "paid"
    order.razorpay_payment_id = data.razorpay_payment_id

    for item in order.items:
        product = db.get(Product, item.product_id)
        if product:
            product.stock = max(product.stock - item.quantity, 0)

    # cart is now an order
    for cart_item in db.scalars(select(CartItem).where(CartItem.user_id == user.id)).all():
        db.delete(cart_item)

    db.commit()
    db.refresh(order)
    return order


@router.get("", response_model=list[OrderOut])
def my_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = (
        select(Order)
        .where(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .limit(100)
    )
    orders = db.scalars(stmt).unique().all()
    return [OrderOut.model_validate(o) for o in orders]


@router.get("/{order_id}", response_model=OrderOut)
def order_detail(
    order_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.scalar(
        select(Order).where(Order.id == order_id, Order.user_id == user.id)
    )
    if order is None:
        raise HTTPException(404, "Order not found")
    return OrderOut.model_validate(order)
