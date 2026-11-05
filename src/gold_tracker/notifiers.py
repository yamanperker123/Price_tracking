"""How alerts are delivered."""

from __future__ import annotations

import logging
from typing import Protocol

import requests

logger = logging.getLogger(__name__)

TWILIO_API = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"


class NotificationError(RuntimeError):
    """Raised when a message could not be sent."""


class Notifier(Protocol):
    def send(self, phone: str, message: str) -> None:
        """Send `message` to `phone` (E.164 format, e.g. +905551112233)."""


class ConsoleNotifier:
    """Prints messages instead of sending them. Useful for local testing."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send(self, phone: str, message: str) -> None:
        self.sent.append((phone, message))
        print(f"[SMS -> {phone}] {message}")


class TwilioSmsNotifier:
    """Sends SMS through the Twilio REST API."""

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
        session: requests.Session | None = None,
        timeout: float = 10.0,
    ) -> None:
        if not (account_sid and auth_token and from_number):
            raise ValueError(
                "TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER "
                "must be set to use the Twilio notifier"
            )
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.session = session or requests.Session()
        self.timeout = timeout

    def send(self, phone: str, message: str) -> None:
        url = TWILIO_API.format(sid=self.account_sid)
        try:
            response = self.session.post(
                url,
                data={"From": self.from_number, "To": phone, "Body": message},
                auth=(self.account_sid, self.auth_token),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise NotificationError(f"SMS to {phone} failed: {exc}") from exc

        if response.status_code >= 400:
            raise NotificationError(
                f"SMS to {phone} failed ({response.status_code}): {response.text}"
            )
        logger.info("SMS sent to %s", phone)
