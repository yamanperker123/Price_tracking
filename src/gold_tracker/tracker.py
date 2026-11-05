"""Core logic: check the price and alert subscribers whose target was reached."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from .notifiers import NotificationError, Notifier
from .price_sources import PriceSource
from .storage import Storage, Subscriber

logger = logging.getLogger(__name__)


def format_try(amount: float) -> str:
    """Format a number the Turkish way: 6693.8 -> '6.693,80 TL'."""
    text = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{text} TL"


def build_message(price: float, target: float) -> str:
    return (
        f"Altın alarmı: Gram altın {format_try(price)} seviyesine düştü. "
        f"Hedefiniz: {format_try(target)}."
    )


@dataclass
class CheckResult:
    price: float
    notified: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    rearmed: list[str] = field(default_factory=list)


def should_notify(price: float, subscriber: Subscriber) -> bool:
    return price <= subscriber.target_price and not subscriber.notified


def should_rearm(price: float, subscriber: Subscriber) -> bool:
    """Once the price goes back above the target, the subscriber can be alerted again."""
    return price > subscriber.target_price and subscriber.notified


class GoldTracker:
    def __init__(self, source: PriceSource, notifier: Notifier, storage: Storage) -> None:
        self.source = source
        self.notifier = notifier
        self.storage = storage

    def check_once(self) -> CheckResult:
        price = self.source.get_price()
        self.storage.save_price(price)
        result = CheckResult(price=price)
        logger.info("Current gram gold price: %s", format_try(price))

        for subscriber in self.storage.list_subscribers():
            if should_notify(price, subscriber):
                try:
                    self.notifier.send(
                        subscriber.phone, build_message(price, subscriber.target_price)
                    )
                except NotificationError as exc:
                    logger.error("%s", exc)
                    result.failed.append(subscriber.phone)
                    continue
                self.storage.set_notified(subscriber.id, True)
                result.notified.append(subscriber.phone)
            elif should_rearm(price, subscriber):
                self.storage.set_notified(subscriber.id, False)
                result.rearmed.append(subscriber.phone)

        return result

    def run_forever(self, interval_seconds: int) -> None:  # pragma: no cover
        logger.info("Tracking started, checking every %s seconds", interval_seconds)
        while True:
            try:
                self.check_once()
            except Exception:  # keep the bot alive on temporary errors
                logger.exception("Price check failed")
            time.sleep(interval_seconds)
