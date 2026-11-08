from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..deps import get_current_user
from ..models import CartItem, Product, User
from ..schemas import CartItemIn, CartItemOut, CartOut, CartQuantityIn

router = APIRouter(prefix="/cart", tags=["cart"], dependencies=[Depends(get_current_user)])


def _cart_out(db: Session, user: User) -> CartOut:
    items = (
        db.scalars(
            select(CartItem)
            .where(CartItem.user_id == user.id)
            .options(joinedload(CartItem.product))
            .order_by(CartItem.id)
        )
        .unique()
        .all()
    )
    total = sum(item.product.price_paise * item.quantity for item in items)
    return CartOut(
        items=[CartItemOut.model_validate(i) for i in items],
        total_paise=total,
    )


@router.get("", response_model=CartOut)
def view_cart(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _cart_out(db, user)


@router.post("/items", response_model=CartOut, status_code=status.HTTP_201_CREATED)
def add_item(
    data: CartItemIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.get(Product, data.product_id)
    if product is None or not product.is_active:
        raise HTTPException(404, "Product not found")
    if product.stock < data.quantity:
        raise HTTPException(400, f"Only {product.stock} left in stock")

    item = db.scalar(
        select(CartItem).where(
            CartItem.user_id == user.id, CartItem.product_id == product.id
        )
    )
    if item:
        item.quantity = min(item.quantity + data.quantity, product.stock)
    else:
        db.add(CartItem(user_id=user.id, product_id=product.id, quantity=data.quantity))
    db.commit()
    return _cart_out(db, user)


@router.patch("/items/{item_id}", response_model=CartOut)
def set_quantity(
    item_id: int,
    data: CartQuantityIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.scalar(select(CartItem).where(CartItem.id == item_id, CartItem.user_id == user.id))
    if item is None:
        raise HTTPException(404, "Cart item not found")
    product = db.get(Product, item.product_id)
    if data.quantity > product.stock:
        raise HTTPException(400, f"Only {product.stock} left in stock")
    item.quantity = data.quantity
    db.commit()
    return _cart_out(db, user)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item(
    item_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.scalar(select(CartItem).where(CartItem.id == item_id, CartItem.user_id == user.id))
    if item is None:
        raise HTTPException(404, "Cart item not found")
    db.delete(item)
    db.commit()
