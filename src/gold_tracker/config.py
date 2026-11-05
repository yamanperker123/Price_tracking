"""Application settings, read from environment variables (or a local .env file)."""

from __future__ import annotations

import os
from dataclasses import dataclass

try:  # python-dotenv is optional at runtime
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


DEFAULT_PRICE_URL = "https://finans.truncgil.com/v4/today.json"


@dataclass(frozen=True)
class Settings:
    db_path: str = "data/gold_tracker.db"
    price_source_url: str = DEFAULT_PRICE_URL
    gold_symbol: str = "GRA"  # "GRA" = gram altın in the Truncgil feed
    price_field: str = "Selling"
    check_interval_seconds: int = 300
    notifier: str = "console"  # "console" or "twilio"
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_from_number: str | None = None

    @classmethod
    def from_env(cls) -> Settings:
        if load_dotenv is not None:
            load_dotenv()
        env = os.environ
        return cls(
            db_path=env.get("DB_PATH", cls.db_path),
            price_source_url=env.get("PRICE_SOURCE_URL", cls.price_source_url),
            gold_symbol=env.get("GOLD_SYMBOL", cls.gold_symbol),
            price_field=env.get("PRICE_FIELD", cls.price_field),
            check_interval_seconds=int(
                env.get("CHECK_INTERVAL_SECONDS", cls.check_interval_seconds)
            ),
            notifier=env.get("NOTIFIER", cls.notifier).lower(),
            twilio_account_sid=env.get("TWILIO_ACCOUNT_SID"),
            twilio_auth_token=env.get("TWILIO_AUTH_TOKEN"),
            twilio_from_number=env.get("TWILIO_FROM_NUMBER"),
        )
