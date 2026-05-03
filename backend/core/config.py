from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = Field(
        default="postgresql+asyncpg://eureka:eureka@localhost:5432/eureka_db",
        alias="DATABASE_URL",
    )
    secret_key: str = Field(default="your-secret-key-here-min-32-chars", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    aws_access_key_id: str = Field(default="", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", alias="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="ap-south-1", alias="AWS_REGION")
    s3_bucket_name: str = Field(default="eureka-uploads", alias="S3_BUCKET_NAME")
    use_local_storage: bool = Field(default=True, alias="USE_LOCAL_STORAGE")
    local_upload_dir: str = Field(default="uploads", alias="LOCAL_UPLOAD_DIR")

    environment: str = Field(default="development", alias="ENVIRONMENT")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
