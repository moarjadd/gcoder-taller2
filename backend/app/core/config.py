import os


class Settings:
    secret_key: str = os.getenv("SECRET_KEY", "change-this-local-development-secret")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./storage/gcoder.db")


settings = Settings()
