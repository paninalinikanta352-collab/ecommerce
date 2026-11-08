# MyShop — detailed setup

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL running locally (any 13+; created with a superuser password you know)

## 1. Database

In psql/pgAdmin:

```sql
CREATE DATABASE shop;
```

## 2. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env     # Windows
cp .env.example .env       # macOS/Linux
```

Edit `.env`:

- `DATABASE_URL` — your real Postgres user/password, e.g. `postgresql+psycopg2://postgres:YOURPASSWORD@localhost:5432/shop`
- `JWT_SECRET` — any long random string
- `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` — optional for browsing; required for checkout

Then:

```bash
python -m app.seed          # creates tables, admin user, demo catalog
uvicorn app.main:app --reload
```

- API live at `http://localhost:8000`
- Interactive docs at `http://localhost:8000/docs`

**Admin account from seed:** first email in `ADMIN_EMAILS` (default `admin@shop.com`), password `admin123`.
Any future registration with an email in `ADMIN_EMAILS` also becomes admin automatically.

## 3. Frontend

```bash
cd frontend
npm install
copy .env.local.example .env.local   # Windows
cp .env.local.example .env.local     # macOS/Linux
npm run dev
```

Store opens at `http://localhost:3000`.

## 4. Razorpay (only needed to test checkout)

1. Sign up at <https://dashboard.razorpay.com>
2. Settings → API Keys → generate **test** keys
3. Paste them into `backend/.env` and restart uvicorn

Test-mode cards: `4111 1111 1111 1111`, any future expiry, any CVV. UPI test VPAs also work.

Without keys, checkout returns `503 "Payment gateway is not configured on the server"` — the rest of the app is fully usable.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `connection refused` on port 5432 | Postgres service isn't running — start it |
| `password authentication failed` | Fix `DATABASE_URL` password in `backend/.env` |
| CORS errors in the browser console | uvicorn not running, or `FRONTEND_ORIGIN` mismatch — restart backend |
| Checkout 503 | Add the Razorpay keys, restart backend |
| `npm run dev` error on first run | run `npm install` first |
