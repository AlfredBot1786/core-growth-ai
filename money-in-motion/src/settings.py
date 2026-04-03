"""Configuration settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


def _load_env():
    env_path = Path(__file__).parent.parent / "config" / ".env"
    if env_path.exists():
        load_dotenv(env_path)


_load_env()


@dataclass
class Settings:
    # SEC EDGAR
    contact_email: str = os.getenv("CONTACT_EMAIL", "")
    sec_rate_limit: float = float(os.getenv("SEC_RATE_LIMIT", "8"))
    sec_retry_attempts: int = int(os.getenv("SEC_RETRY_ATTEMPTS", "3"))
    sec_retry_backoff: float = float(os.getenv("SEC_RETRY_BACKOFF", "2.0"))

    # Anthropic
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    scoring_model: str = os.getenv("SCORING_MODEL", "claude-sonnet-4-6")

    # Supabase
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")

    # LinkedIn / Apify
    apify_token: str = os.getenv("APIFY_TOKEN", "")
    target_company_urls: list[str] = field(default_factory=lambda: [
        u.strip() for u in os.getenv("TARGET_COMPANY_URLS", "").split(",") if u.strip()
    ])
    apify_timeout_seconds: int = int(os.getenv("APIFY_TIMEOUT_SECONDS", "300"))

    # WARN Act
    target_states: list[str] = field(default_factory=lambda: [
        s.strip() for s in os.getenv("TARGET_STATES", "").split(",") if s.strip()
    ])

    # Email Alerts
    alert_email: str = os.getenv("ALERT_EMAIL", "")
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_pass: str = os.getenv("SMTP_PASS", "")

    # Cost Circuit Breakers
    max_claude_calls_per_run: int = int(os.getenv("MAX_CLAUDE_CALLS_PER_RUN", "200"))
    max_events_per_run: int = int(os.getenv("MAX_EVENTS_PER_RUN", "300"))
    max_t1_alerts_per_run: int = int(os.getenv("MAX_T1_ALERTS_PER_RUN", "20"))

    # Pipeline
    default_lookback_hours: int = int(os.getenv("DEFAULT_LOOKBACK_HOURS", "24"))
    local_cache_dir: str = os.getenv("LOCAL_CACHE_DIR", ".cache")
    export_dir: str = os.getenv("EXPORT_DIR", "exports")

    # Server Auth
    api_auth_token: str = os.getenv("API_AUTH_TOKEN", "")

    @property
    def has_email_alerts(self) -> bool:
        return bool(self.smtp_user and self.smtp_pass and self.alert_email)

    @property
    def has_linkedin(self) -> bool:
        return bool(self.apify_token and self.target_company_urls)

    def validate(self) -> list[str]:
        errors = []
        if not self.contact_email:
            errors.append("CONTACT_EMAIL required (SEC blocks requests without it)")
        if not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY required for Claude scoring")
        if not self.supabase_url:
            errors.append("SUPABASE_URL required for data persistence")
        if not self.supabase_key:
            errors.append("SUPABASE_KEY required for data persistence")
        if not self.api_auth_token:
            errors.append("API_AUTH_TOKEN recommended for webhook security")
        return errors


settings = Settings()
