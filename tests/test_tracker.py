from gold_tracker.notifiers import NotificationError
from gold_tracker.tracker import GoldTracker, build_message, format_try


def test_format_try_uses_turkish_separators():
    assert format_try(6693.8) == "6.693,80 TL"
    assert format_try(950) == "950,00 TL"


def test_build_message_contains_price_and_target():
    message = build_message(6150.25, 6200)
    assert "6.150,25 TL" in message
    assert "6.200,00 TL" in message


def test_no_alert_when_price_is_above_target(storage, notifier, source):
    storage.add_subscriber("+905551112233", 6000)
    result = GoldTracker(source, notifier, storage).check_once()

    assert result.notified == []
    assert notifier.sent == []


def test_alert_when_price_drops_to_target(storage, notifier, source):
    storage.add_subscriber("+905551112233", 6500)
    result = GoldTracker(source, notifier, storage).check_once()

    assert result.notified == ["+905551112233"]
    assert notifier.sent[0][0] == "+905551112233"
    assert storage.get_subscriber("+905551112233").notified is True


def test_alert_is_sent_only_once_while_price_stays_low(storage, notifier, source):
    storage.add_subscriber("+905551112233", 7000)
    tracker = GoldTracker(source, notifier, storage)

    tracker.check_once()
    tracker.check_once()

    assert len(notifier.sent) == 1


def test_alert_rearms_after_price_goes_back_up(storage, notifier, source):
    storage.add_subscriber("+905551112233", 6600)
    tracker = GoldTracker(source, notifier, storage)

    tracker.check_once()          # 6500 <= 6600 -> alert
    source.price = 6700
    result = tracker.check_once()  # back above target -> rearm
    source.price = 6550
    tracker.check_once()          # drops again -> second alert

    assert result.rearmed == ["+905551112233"]
    assert len(notifier.sent) == 2


def test_only_matching_subscribers_are_alerted(storage, notifier, source):
    storage.add_subscriber("+905551112233", 6600)
    storage.add_subscriber("+905559998877", 6000)
    result = GoldTracker(source, notifier, storage).check_once()

    assert result.notified == ["+905551112233"]


def test_failed_sms_is_retried_on_next_check(storage, source):
    class FlakyNotifier:
        def __init__(self):
            self.calls = 0

        def send(self, phone, message):
            self.calls += 1
            if self.calls == 1:
                raise NotificationError("network down")

    notifier = FlakyNotifier()
    storage.add_subscriber("+905551112233", 6600)
    tracker = GoldTracker(source, notifier, storage)

    first = tracker.check_once()
    second = tracker.check_once()

    assert first.failed == ["+905551112233"]
    assert second.notified == ["+905551112233"]


def test_every_check_is_saved_to_history(storage, notifier, source):
    tracker = GoldTracker(source, notifier, storage)
    tracker.check_once()
    source.price = 6400
    tracker.check_once()

    prices = [p.price for p in storage.price_history()]
    assert prices == [6400, 6500]
