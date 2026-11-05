import pytest

from gold_tracker.notifiers import ConsoleNotifier
from gold_tracker.storage import Storage


class FakePriceSource:
    def __init__(self, price: float) -> None:
        self.price = price

    def get_price(self) -> float:
        return self.price


@pytest.fixture
def storage():
    db = Storage(":memory:")
    yield db
    db.close()


@pytest.fixture
def notifier():
    return ConsoleNotifier()


@pytest.fixture
def source():
    return FakePriceSource(6500.0)
