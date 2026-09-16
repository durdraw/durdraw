import os

import pytest

from durdraw import durview


class FakeUI:
    instances = []

    def __init__(self, app):
        self.app = app
        self.mouse_initialized = False
        self.transparent_background_enabled = False
        self.quit_called = False
        FakeUI.instances.append(self)

    def initMouse(self):
        self.mouse_initialized = True

    def enableTransBackground(self):
        self.transparent_background_enabled = True

    def runDurView(self):
        self.app.durview_running = False

    def verySafeQuit(self):
        self.quit_called = True


@pytest.fixture(autouse=True)
def fake_ui(monkeypatch):
    FakeUI.instances = []
    monkeypatch.setattr(durview, "UI_Curses", FakeUI)


def test_dir_option_starts_browser_in_local_directory(tmp_path):
    durview.main(["--dir", str(tmp_path)])

    ui = FakeUI.instances[0]
    assert ui.app.workingLoadDirectory == str(tmp_path)
    assert ui.app.usingDirMode is True
    assert ui.app.dirSort == "name"
    assert ui.app.flattenDirs is False
    assert ui.app.sixteenc_browsing is False
    assert ui.app.playOnlyMode is True
    assert ui.app.editorRunning is False
    assert ui.app.play_queue == []
    assert ui.quit_called is True


def test_dir_option_expands_user_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    pack_dir = home / "p" / "gh" / "16colo.rs" / "pack"
    pack_dir.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))

    durview.main(["--dir", "~/p/gh/16colo.rs/pack"])

    ui = FakeUI.instances[0]
    assert ui.app.workingLoadDirectory == os.path.abspath(pack_dir)


def test_dir_option_cannot_be_combined_with_files(tmp_path):
    with pytest.raises(SystemExit):
        durview.main(["--dir", str(tmp_path), "examples/file_id.dur"])

    assert FakeUI.instances == []


def test_dir_sort_option_sets_sort_mode(tmp_path):
    durview.main(["--dir", str(tmp_path), "--dir-sort", "mtime"])

    ui = FakeUI.instances[0]
    assert ui.app.dirSort == "mtime"


def test_dir_sort_option_requires_dir():
    with pytest.raises(SystemExit):
        durview.main(["--dir-sort", "size"])

    assert FakeUI.instances == []


def test_flatten_dirs_option_sets_flatten_mode(tmp_path):
    durview.main(["--dir", str(tmp_path), "--flatten-dirs"])

    ui = FakeUI.instances[0]
    assert ui.app.workingLoadDirectory == str(tmp_path)
    assert ui.app.usingDirMode is True
    assert ui.app.flattenDirs is True


def test_flatten_dirs_option_requires_directory_browser():
    with pytest.raises(SystemExit):
        durview.main(["--flatten-dirs", "examples/file_id.dur"])

    assert FakeUI.instances == []


def test_file_arguments_enable_auto_advance_queue():
    durview.main(["one.ans", "two.ans"])

    ui = FakeUI.instances[0]
    assert ui.app.play_queue == ["one.ans", "two.ans"]
    assert ui.app.play_queue_position == 0
    assert ui.app.play_queue_auto_advance is True
