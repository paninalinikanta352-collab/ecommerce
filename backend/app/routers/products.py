from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Product
from ..schemas import ProductOut

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
def list_products(
    q: str | None = None,
    category: str | None = None,
    sort: str | None = None,  # price_asc | price_desc | newest
    db: Session = Depends(get_db),
):
    stmt = select(Product).where(Product.is_active.is_(True))
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q}%"))
    if category:
        stmt = stmt.where(Product.category == category)

    if sort == "price_asc":
        stmt = stmt.order_by(Product.price_paise.asc())
    elif sort == "price_desc":
        stmt = stmt.order_by(Product.price_paise.desc())
    elif sort == "newest":
        stmt = stmt.order_by(Product.created_at.desc())

    return db.scalars(stmt).all()


@router.get("/categories", response_model=list[str])
def list_categories(db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Product.category).distinct().where(Product.is_active.is_(True))
    ).all()
    return sorted(rows)


@router.get("/{slug}", response_model=ProductOut)
def get_product(slug: str, db: Session = Depends(get_db)):
    product = db.scalar(select(Product).where(Product.slug == slug, Product.is_active.is_(True)))
    if product is None:
        raise HTTPException(404, "Product not found")
    return product
