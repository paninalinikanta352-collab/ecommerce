from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/shop"
    JWT_SECRET: str = "insecure-dev-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 60 * 24
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    # absolute base of this API, used inside verification links you get by email
    PUBLIC_API_URL: str = "http://localhost:8000"
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    ADMIN_EMAILS: str = "admin@shop.com"

    # Local dev default = MailHog (UI at http://localhost:8025).
    # For real email: SMTP_HOST=smtp.gmail.com, SMTP_PORT=587, SMTP_USE_TLS=true,
    # SMTP_USER / SMTP_PASS = gmail account + app password.
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USE_TLS: bool = False
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = "MyShop <no-reply@myshop.local>"
    VERIFY_TOKEN_HOURS: int = 24

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def admin_email_list(self) -> list[str]:
        return [e.strip().lower() for e in self.ADMIN_EMAILS.split(",") if e.strip()]

    @property
    def gateway_configured(self) -> bool:
        return bool(self.RAZORPAY_KEY_ID and self.RAZORPAY_KEY_SECRET)


settings = Settings()
