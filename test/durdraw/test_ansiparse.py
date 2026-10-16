from types import SimpleNamespace

from durdraw.durdraw_ansiparse import (
    get_width_and_height_of_ansi_blob,
    parse_ansi_escape_codes,
)


def app_state():
    return SimpleNamespace(
        colorMode="16",
        debug=False,
        defaultFgColor=8,
        defaultBgColor=0,
        sauce=None,
        wrapWidth=80,
    )


def test_csi_h_uses_one_based_row_and_column():
    frame = parse_ansi_escape_codes("\x1b[2;3HX", appState=app_state())

    assert frame.content[1][2] == "X"
    assert frame.content[2][3] == " "


def test_csi_h_defaults_missing_row_and_column_to_one():
    frame = parse_ansi_escape_codes(
        "\x1b[HZ\x1b[2;HX\x1b[;3HY",
        appState=app_state(),
    )

    assert frame.content[0][0] == "Z"
    assert frame.content[1][0] == "X"
    assert frame.content[0][2] == "Y"


def test_csi_f_moves_cursor_like_csi_h():
    frame = parse_ansi_escape_codes("\x1b[3;4fX", appState=app_state())

    assert frame.content[2][3] == "X"


def test_csi_save_and_restore_cursor_position():
    frame = parse_ansi_escape_codes(
        "A\x1b[s\x1b[3CB\x1b[uZ",
        appState=app_state(),
    )

    assert frame.content[0][0] == "A"
    assert frame.content[0][1] == "Z"
    assert frame.content[0][4] == "B"


def test_csi_backward_and_up_clamp_to_origin():
    frame = parse_ansi_escape_codes(
        "\x1b[5D\x1b[5AX",
        appState=app_state(),
    )

    assert frame.content[0][0] == "X"


def test_incomplete_csi_at_eof_does_not_crash_width_scan():
    assert get_width_and_height_of_ansi_blob("abc\x1b[\x00\x00") == (0, 0)
