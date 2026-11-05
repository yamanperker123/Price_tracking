from gold_tracker.cli import main
from gold_tracker.config import Settings


def settings(tmp_path):
    return Settings(db_path=str(tmp_path / "test.db"), notifier="console")


def test_add_list_remove(tmp_path, capsys):
    s = settings(tmp_path)

    assert main(["add", "05551112233", "--target", "6200"], s) == 0
    assert main(["list"], s) == 0
    output = capsys.readouterr().out
    assert "+905551112233" in output
    assert "6.200,00 TL" in output

    assert main(["remove", "+905551112233"], s) == 0
    assert main(["remove", "+905551112233"], s) == 1


def test_invalid_phone_returns_error(tmp_path, capsys):
    assert main(["add", "123", "--target", "6200"], settings(tmp_path)) == 1
    assert "Invalid phone number" in capsys.readouterr().err
