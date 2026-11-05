from unittest.mock import MagicMock

import pytest

from gold_tracker.notifiers import NotificationError, TwilioSmsNotifier


def make_notifier(status_code=201):
    session = MagicMock()
    session.post.return_value.status_code = status_code
    session.post.return_value.text = "error body"
    notifier = TwilioSmsNotifier("AC123", "secret", "+15005550006", session=session)
    return notifier, session


def test_twilio_sends_expected_request():
    notifier, session = make_notifier()
    notifier.send("+905551112233", "hello")

    url = session.post.call_args.args[0]
    kwargs = session.post.call_args.kwargs
    assert url.endswith("/Accounts/AC123/Messages.json")
    assert kwargs["data"] == {"From": "+15005550006", "To": "+905551112233", "Body": "hello"}
    assert kwargs["auth"] == ("AC123", "secret")


def test_twilio_error_response_raises():
    notifier, _ = make_notifier(status_code=400)
    with pytest.raises(NotificationError):
        notifier.send("+905551112233", "hello")


def test_twilio_requires_credentials():
    with pytest.raises(ValueError):
        TwilioSmsNotifier("", "", "")
