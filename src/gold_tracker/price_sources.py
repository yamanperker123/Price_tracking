"""Where gold prices come from."""

from __future__ import annotations

from typing import Protocol

import requests


class PriceSourceError(RuntimeError):
    """Raised when a price cannot be fetched or parsed."""


class PriceSource(Protocol):
    def get_price(self) -> float:
        """Return the current gold price in TRY."""


def parse_turkish_number(value: object) -> float:
    """Parse numbers like 6693.82, "6693.82" or "6.693,82" into a float."""
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str) or not value.strip():
        raise PriceSourceError(f"Unexpected price value: {value!r}")

    text = value.strip().replace("₺", "").replace("TL", "").strip()
    if "," in text:
        # Turkish format: "." for thousands, "," for decimals
        text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError as exc:
        raise PriceSourceError(f"Unexpected price value: {value!r}") from exc


class TruncgilPriceSource:
    """Reads gram gold price from the free Truncgil finance feed."""

    def __init__(
        self,
        url: str,
        symbol: str = "GRA",
        field: str = "Selling",
        session: requests.Session | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.url = url
        self.symbol = symbol
        self.field = field
        self.session = session or requests.Session()
        self.timeout = timeout

    def get_price(self) -> float:
        try:
            response = self.session.get(self.url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise PriceSourceError(f"Could not fetch prices: {exc}") from exc

        return self.extract_price(data)

    def extract_price(self, data: dict) -> float:
        item = data.get(self.symbol)
        if not isinstance(item, dict) or self.field not in item:
            raise PriceSourceError(
                f"'{self.symbol}.{self.field}' not found in price feed"
            )
        price = parse_turkish_number(item[self.field])
        if price <= 0:
            raise PriceSourceError(f"Invalid price: {price}")
        return price
