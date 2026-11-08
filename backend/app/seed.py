"""Run with: python -m app.seed
Creates tables, an admin user (email from ADMIN_EMAILS / admin@shop.com,
password admin123) and a small product catalog."""
from sqlalchemy import func, select

from .config import settings
from .database import Base, SessionLocal, engine
from .models import Product, User
from .security import hash_password

# picsum.photos gives stable, well-sized placeholder images by seed
PRODUCTS = [
    ("Aurora Wireless Headphones", "electronics", 499900, 24,
     "Over-ear ANC headphones. 30-hour battery, USB-C fast charge.",
     "https://picsum.photos/seed/headphones/600/600"),
    ("Nimbus Mechanical Keyboard", "electronics", 349900, 12,
     "75% hot-swappable mechanical keyboard with brown switches and PBT caps.",
     "https://picsum.photos/seed/keyboard/600/600"),
    ("Pulse Fitness Band 3", "electronics", 199900, 40,
     "SpO2, heart-rate and sleep tracking with a 10-day battery.",
     "https://picsum.photos/seed/band/600/600"),
    ("Drift Cloud Sneakers", "fashion", 259900, 30,
     "Everyday runners with a knit upper and foam midsole.",
     "https://picsum.photos/seed/sneakers/600/600"),
    ("Merino Everyday Tee", "fashion", 99900, 55,
     "100% merino wool tee. Breathable, odor-resistant, machine washable.",
     "https://picsum.photos/seed/tee/600/600"),
    ("Ranger Canvas Backpack", "fashion", 179900, 18,
     "22L waxed-canvas backpack with a padded 15\" laptop sleeve.",
     "https://picsum.photos/seed/backpack/600/600"),
    ("Ember Pour-Over Coffee Kit", "home", 149900, 21,
     "Borosilicate carafe, stainless dripper and a single-origin 250g bag.",
     "https://picsum.photos/seed/coffee/600/600"),
    ("Terra Ceramic Planter Set", "home", 79900, 35,
     "Set of three matte-glaze planters with drainage trays.",
     "https://picsum.photos/seed/planter/600/600"),
    ("Halo Smart Desk Lamp", "home", 229900, 15,
     "Touch-control LED lamp, five color temperatures, USB-C port in the base.",
     "https://picsum.photos/seed/lamp/600/600"),
    ("Flux Yoga Mat 6mm", "fitness", 129900, 45,
     "Non-slip TPE mat with alignment lines and a carry strap.",
     "https://picsum.photos/seed/yogamat/600/600"),
]


def run():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        admin_email = settings.admin_email_list[0] if settings.admin_email_list else "admin@shop.com"
        if not db.scalar(select(User).where(User.email == admin_email)):
            db.add(
                User(
                    email=admin_email,
                    full_name="Shop Admin",
                    hashed_password=hash_password("admin123"),
                    is_admin=True,
                )
            )
            print(f"admin user created -> {admin_email} / admin123")

        count = db.scalar(select(func.count(Product.id)))
        if not count:
            for i, (name, category, paise, stock, desc, url) in enumerate(PRODUCTS, start=1):
                slug = name.lower().replace(" ", "-")
                db.add(
                    Product(
                        slug=slug,
                        name=name,
                        description=desc,
                        category=category,
                        price_paise=paise,
                        image_url=url,
                        stock=stock,
                    )
                )
            print(f"{len(PRODUCTS)} products seeded")
        else:
            print(f"products already present ({count}), skipping")

        db.commit()
        print("seed done")
    finally:
        db.close()


if __name__ == "__main__":
    run()
