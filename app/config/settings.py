from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "Reddit Automation API"
    debug: bool = False
    log_level: str = "INFO"

    # Browser
    headless: bool = True
    proxy_url: Optional[str] = None  # e.g. "http://user:pass@host:port"

    # Sessions
    session_dir: str = "data/sessions"

    # CAPTCHA
    captcha_api_key: Optional[str] = None
    captcha_service: str = "2captcha"  # or "anticaptcha"
    # When True and no API key is set, browser opens visibly so you can solve CAPTCHA manually
    allow_manual_captcha: bool = True
    manual_captcha_timeout: int = 120  # seconds to wait for manual solve

    # Retry
    max_retries: int = 3
    retry_backoff: float = 2.0


settings = Settings()
