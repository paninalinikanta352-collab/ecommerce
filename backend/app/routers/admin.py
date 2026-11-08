from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import Order, Product, User
from ..schemas import (
    AdminOrderOut,
    OrderStatusIn,
    ProductCreate,
    ProductOut,
    ProductUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _unique_slug(db: Session, name: str, current_id: int | None = None) -> str:
    base = name.strip().lower().replace(" ", "-") or "product"
    slug, i = base, 1
    while True:
        stmt = select(Product).where(Product.slug == slug)
        existing = db.scalar(stmt)
        if existing is None or (current_id is not None and existing.id == current_id):
            return slug
        i += 1
        slug = f"{base}-{i}"


@router.get("/products", response_model=list[ProductOut])
def list_all_products(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = select(Product).order_by(Product.created_at.desc())
    return db.scalars(stmt).all()


@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(
    data: ProductCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    slug = _unique_slug(db, data.slug or data.name)
    product = Product(**data.model_dump(exclude={"slug"}), slug=slug)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    data: ProductUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(404, "Product not found")
    updates = data.model_dump(exclude_none=True)
    if "name" in updates:
        updates["slug"] = _unique_slug(db, updates["name"], product.id)
    for field, value in updates.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Soft delete: hide from the store, keep old orders intact."""
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(404, "Product not found")
    product.is_active = False
    db.commit()
    return {"ok": True, "product_id": product_id, "is_active": False}


@router.get("/orders", response_model=list[AdminOrderOut])
def list_all_orders(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = select(Order).order_by(Order.created_at.desc()).limit(200)
    orders = db.scalars(stmt).unique().all()
    return [AdminOrderOut.model_validate(o) for o in orders]


@router.patch("/orders/{order_id}", response_model=AdminOrderOut)
def set_order_status(
    order_id: int,
    data: OrderStatusIn,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(404, "Order not found")
    order.status = data.status
    db.commit()
    db.refresh(order)
    return AdminOrderOut.model_validate(order)
