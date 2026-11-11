import pytest

from durdraw.main import main


def test_undosize_zero_is_rejected(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(['--undosize', '0'])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert 'Undo size must be between 1 and 1000' in captured.err


def test_undosize_above_maximum_is_rejected(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(['--undosize', '1001'])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert 'Undo size must be between 1 and 1000' in captured.err
