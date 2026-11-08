from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/shop"
    JWT_SECRET: str = "insecure-dev-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 60 * 24
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    ADMIN_EMAILS: str = "admin@shop.com"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def admin_email_list(self) -> list[str]:
        return [e.strip().lower() for e in self.ADMIN_EMAILS.split(",") if e.strip()]

    @property
    def gateway_configured(self) -> bool:
        return bool(self.RAZORPAY_KEY_ID and self.RAZORPAY_KEY_SECRET)


settings = Settings()
