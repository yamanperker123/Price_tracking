from unittest.mock import MagicMock

import pytest
import requests

from gold_tracker.price_sources import (
    PriceSourceError,
    TruncgilPriceSource,
    parse_turkish_number,
)

SAMPLE_FEED = {
    "Update_Date": "2026-11-05 12:00:00",
    "USD": {"Type": "Currency", "Buying": 41.95, "Selling": 42.01},
    "GRA": {"Type": "Gold", "Buying": 6690.12, "Selling": 6693.82, "Change": -0.42},
}


@pytest.mark.parametrize(
    "value, expected",
    [
        (6693.82, 6693.82),
        ("6693.82", 6693.82),
        ("6.693,82", 6693.82),
        ("₺6.693,82", 6693.82),
        ("950,5", 950.5),
    ],
)
def test_parse_turkish_number(value, expected):
    assert parse_turkish_number(value) == pytest.approx(expected)


@pytest.mark.parametrize("value", [None, "", "abc"])
def test_parse_turkish_number_rejects_garbage(value):
    with pytest.raises(PriceSourceError):
        parse_turkish_number(value)


def make_source(json_data=None, error=None):
    session = MagicMock()
    if error:
        session.get.side_effect = error
    else:
        session.get.return_value.json.return_value = json_data
    return TruncgilPriceSource("https://example.test/today.json", session=session)


def test_reads_gram_gold_selling_price():
    assert make_source(SAMPLE_FEED).get_price() == pytest.approx(6693.82)


def test_missing_symbol_raises():
    with pytest.raises(PriceSourceError):
        make_source({"USD": SAMPLE_FEED["USD"]}).get_price()


def test_network_error_raises_price_source_error():
    with pytest.raises(PriceSourceError):
        make_source(error=requests.ConnectionError("offline")).get_price()
