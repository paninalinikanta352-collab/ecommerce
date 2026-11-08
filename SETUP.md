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

## 4. Verification (works out of the box)

New signups verify with a **6-digit code**. Without any SMTP configured, the code shows directly on the verify screen — so a fresh clone is usable in under a minute.

Optional — if you'd rather have the code **emailed** (Gmail example):

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USER=you@gmail.com
SMTP_PASS=<16-char app password>
```

Get the app password Google Account → Security → 2-Step Verification on → App passwords → "add name". Then restart uvicorn. The UX stays identical — the code just moves from the screen to your inbox.

Codes are stored **hashed (SHA-256)**, expire in **10 minutes** (`VERIFY_CODE_MINUTES`), lock out after **six wrong attempts**, and resend is **cooldown-limited**. Admins in `ADMIN_EMAILS` skip verification entirely. If you still enjoy watching mail arrive, [MailHog](https://github.com/mailhog/MailHog) works too (`SMTP_HOST=localhost`, `SMTP_PORT=1025`, inbox UI at <http://localhost:8025>) — but it's optional now, not a dependency.

## 5. Razorpay (only needed to test checkout)

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
| "needs a verification code" on login | go to `/verify` (the login page links there), get a fresh code |
| "Too many wrong attempts" on verify | the code died on purpose after 6 tries — "Send a new code" replaces it |
| Code emails: Gmail says bad credentials | app password wrong or 2-Step Verification off — regenerate it |
| Checkout 503 | Add the Razorpay keys, restart backend |
| `npm run dev` error on first run | run `npm install` first |
