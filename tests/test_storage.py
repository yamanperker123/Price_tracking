import pytest

from gold_tracker.storage import normalize_phone


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("+905551112233", "+905551112233"),
        ("05551112233", "+905551112233"),
        ("5551112233", "+905551112233"),
        ("0555 111 22 33", "+905551112233"),
        ("00905551112233", "+905551112233"),
    ],
)
def test_normalize_phone(raw, expected):
    assert normalize_phone(raw) == expected


@pytest.mark.parametrize("raw", ["", "123", "abc", "+0123456789"])
def test_invalid_phone_is_rejected(raw):
    with pytest.raises(ValueError):
        normalize_phone(raw)


def test_add_and_list_subscribers(storage):
    storage.add_subscriber("05551112233", 6200)
    subscribers = storage.list_subscribers()

    assert len(subscribers) == 1
    assert subscribers[0].phone == "+905551112233"
    assert subscribers[0].target_price == 6200


def test_adding_same_phone_updates_target_and_resets_alert(storage):
    sub = storage.add_subscriber("+905551112233", 6200)
    storage.set_notified(sub.id, True)

    updated = storage.add_subscriber("+905551112233", 6100)

    assert len(storage.list_subscribers()) == 1
    assert updated.target_price == 6100
    assert updated.notified is False


def test_target_must_be_positive(storage):
    with pytest.raises(ValueError):
        storage.add_subscriber("+905551112233", 0)


def test_remove_subscriber(storage):
    storage.add_subscriber("+905551112233", 6200)

    assert storage.remove_subscriber("05551112233") is True
    assert storage.remove_subscriber("05551112233") is False
    assert storage.list_subscribers() == []
