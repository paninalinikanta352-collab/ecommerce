# MyShop — Full-Stack E-commerce

<p>
  <img src="docs/screenshot.jpeg" alt="MyShop storefront" width="820" />
</p>

A complete e-commerce MVP built end to end: **Next.js (React, JavaScript)** storefront, **FastAPI** backend, **PostgreSQL** database, **Razorpay** payments — from first route to verified payment, in one repo.

## Features

**Storefront (Next.js App Router)**
- Product listing with live search (debounced), category filter and price sort
- Product detail pages with stock awareness
- Authenticated cart: add, adjust quantity, remove — with server-side validation
- Checkout collects shipping details and opens the **Razorpay payment modal**
- Order history and order detail with status tracking
- Admin panel: create/edit/hide products, view all orders, advance order status

**Backend (FastAPI + SQLAlchemy 2.0 + PostgreSQL)**
- JWT authentication (bcrypt-hashed passwords)
- REST router per domain: `auth`, `products`, `cart`, `orders`, `admin`
- **Razorpay order creation + server-side signature verification** — a browser can't fake "payment successful"
- Orders keep **snapshots** of product names/prices, so history survives product edits
- Soft-delete products (`is_active`) so old orders stay intact
- Interactive docs at `/docs` (OpenAPI)

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 14, React 18, plain CSS (no UI kit) |
| Auth | JWT bearer tokens, passlib/bcrypt |
| Backend | FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| Database | PostgreSQL |
| Payments | Razorpay Orders API + HMAC-SHA256 verification |
| Storage | Money as **integer paise** everywhere — floats never touch money |

## Project structure

```
ecommerce/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app + CORS
│   │   ├── config.py          # env settings
│   │   ├── database.py        # engine, session, Base
│   │   ├── models.py          # ORM models
│   │   ├── schemas.py         # request/response bodies
│   │   ├── security.py        # hashing + JWT
│   │   ├── deps.py            # current user / admin guards
│   │   ├── seed.py            # tables + admin + demo catalog
│   │   ├── routers/           # auth, products, cart, orders, admin
│   │   └── utils/razorpay.py  # order creation + signature check
│   ├── requirements.txt
│   └── .env.example           # never commit your real .env
└── frontend/
    ├── app/                   # Next.js App Router pages
    ├── components/            # Navbar, ProductCard
    ├── lib/api.js             # single fetch wrapper
    └── package.json
```

## Run it locally

Full setup guide in [SETUP.md](SETUP.md) — the short version:

```bash
# 1. PostgreSQL: create a database named "shop", then
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows | macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env        # then set DATABASE_URL + JWT_SECRET
python -m app.seed            # tables + admin user + demo catalog
uvicorn app.main:app --reload  # → http://localhost:8000/docs

# 2. new terminal
cd ../frontend
npm install
copy .env.local.example .env.local
npm run dev                    # → http://localhost:3000
```

**Admin login after seeding:** email from `ADMIN_EMAILS` (default `admin@shop.com`), password `admin123` — change the password immediately in any non-local use.

## Payments — how they actually work

1. `POST /orders` snapshots the cart into `order_items`, creates a matching **Razorpay order** via the SDK, returns the order id + amount + public key id
2. Frontend opens the Razorpay checkout modal
3. Razorpay returns `order_id | payment_id | signature`
4. `POST /orders/verify` recomputes `HMAC-SHA256(order_id|payment_id, key_secret)` server-side and compares before marking the order `paid`, decrementing stock and clearing the cart

Verification is idempotent. Without Razorpay keys configured, checkout fails with `503 "Payment gateway is not configured"` — everything else works.

## Notes on choices

- **JWT in localStorage** — the simplest correct thing for a demo; production would move to httpOnly cookies + CSRF handling
- **No Alembic yet** — `seed.py` creates tables directly; add migrations when the schema starts evolving under real data
- **Product images are URLs** — no upload pipeline in v1

## License

[MIT](LICENSE)
