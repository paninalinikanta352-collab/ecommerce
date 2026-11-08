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

## 4. MailHog (local email for verification)

`python -m app.seed` also creates an admin (auto-verified), but normal signups **verify by email link** before they can log in.

- Download MailHog once: <https://github.com/mailhog/MailHog/releases> (Windows: `MailHog_windows_amd64.exe`)
- Run it: `MailHog_windows_amd64.exe` → SMTP on `:1025`, inbox UI at <http://localhost:8025>
- Register a user on the site, click the link in MailHog's inbox, done.

No config needed — `.env` defaults already point at MailHog. For real email (Gmail example):

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USER=you@gmail.com
SMTP_PASS=<16-char app password>
```

Verification links carry a one-use token; the DB stores only its SHA-256 hash, and the link expires after 24 hours (`VERIFY_TOKEN_HOURS` in `.env`). Admins listed in `ADMIN_EMAILS` skip verification entirely.

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
| Verification mail never shows up | MailHog isn't running (inbox UI at <http://localhost:8025>) or SMTP settings wrong |
| "Verify your email first" on login though you clicked the link | use the **Resend** button on the login page; old pre-verification users need a new link |
| Login 403 after clicking a reused/expired link | tokens are one-use and 24h — request a fresh one |
| Checkout 503 | Add the Razorpay keys, restart backend |
| `npm run dev` error on first run | run `npm install` first |
