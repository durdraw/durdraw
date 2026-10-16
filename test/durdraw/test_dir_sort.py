import os
from types import SimpleNamespace

from durdraw.durdraw_ui_curses import ALL_FILE_MASKS, DEFAULT_LOAD_FILE_MASKS, UserInterface


def make_ui(sort_mode, flatten_dirs=False):
    ui = UserInterface.__new__(UserInterface)
    ui.appState = SimpleNamespace(
        usingDirMode=True,
        dirSort=sort_mode,
        flattenDirs=flatten_dirs,
        sixteenc_browsing=False,
    )
    return ui


def test_sort_local_names_by_name(tmp_path):
    assert make_ui("name").sortLocalNames(str(tmp_path), ["beta.ans", "Alpha.ans"]) == [
        "Alpha.ans",
        "beta.ans",
    ]


def test_sort_local_names_by_size_largest_first(tmp_path):
    small = tmp_path / "small.ans"
    large = tmp_path / "large.ans"
    small.write_text("x")
    large.write_text("xxxx")

    assert make_ui("size").sortLocalNames(str(tmp_path), ["small.ans", "large.ans"]) == [
        "large.ans",
        "small.ans",
    ]


def test_sort_local_names_by_mtime_newest_first(tmp_path):
    old = tmp_path / "old.ans"
    new = tmp_path / "new.ans"
    old.write_text("old")
    new.write_text("new")
    old_time = 1_700_000_000
    new_time = old_time + 60
    os.utime(old, (old_time, old_time))
    os.utime(new, (new_time, new_time))

    assert make_ui("mtime").sortLocalNames(str(tmp_path), ["old.ans", "new.ans"]) == [
        "new.ans",
        "old.ans",
    ]


def test_get_local_folders_keeps_parent_first_and_sorts_dirs(tmp_path):
    zed = tmp_path / "zed"
    alpha = tmp_path / "alpha"
    zed.mkdir()
    alpha.mkdir()

    assert make_ui("name").getLocalFolders(str(tmp_path)) == ["../", "alpha/", "zed/"]


def test_set_local_play_queue_tracks_selected_file_and_skips_dirs(tmp_path):
    folder = tmp_path / "folder"
    one = tmp_path / "one.ans"
    two = tmp_path / "two.ans"
    folder.mkdir()
    one.write_text("one")
    two.write_text("two")
    ui = make_ui("name")

    ui.setLocalPlayQueue(str(tmp_path), ["../", "folder/", "one.ans", "two.ans"], ["../", "folder/"], "two.ans")

    assert ui.appState.play_queue == [str(one), str(two)]
    assert ui.appState.play_queue_position == 1
    assert ui.appState.play_queue_direction == 0
    assert ui.appState.play_queue_auto_advance is False


def test_set_sixteenc_play_queue_tracks_selected_file_and_skips_parent():
    ui = make_ui("name")

    ui.setSixteenColorsPlayQueue("pack-01", ["../", "one.ans", "two.ans"], ["../"], "two.ans")

    assert ui.appState.play_queue == [
        ("16colo.rs", "pack-01", "one.ans"),
        ("16colo.rs", "pack-01", "two.ans"),
    ]
    assert ui.appState.play_queue_position == 1
    assert ui.appState.play_queue_direction == 0
    assert ui.appState.play_queue_auto_advance is False


def test_filter_file_names_uses_default_load_allowlist_case_insensitive():
    ui = make_ui("name")

    assert ui.filterFileNames(
        ["art.ANS", "readme.nfo", "image.jpg", "song.xm", "demo.tx5", "FILE_ID.DIZ"],
        DEFAULT_LOAD_FILE_MASKS,
    ) == ["art.ANS", "readme.nfo", "FILE_ID.DIZ"]


def test_build_sixteenc_file_list_filters_default_and_show_all_keeps_parent():
    ui = make_ui("name")
    names = ["art.ANS", "image.jpg", "info.NFO", "song.xm"]

    assert ui.buildSixteenColorsFileList(["../"], names, DEFAULT_LOAD_FILE_MASKS) == [
        "../",
        "art.ANS",
        "info.NFO",
    ]
    assert ui.buildSixteenColorsFileList(["../"], names, ALL_FILE_MASKS) == [
        "../",
        "art.ANS",
        "image.jpg",
        "info.NFO",
        "song.xm",
    ]


def test_get_local_file_list_flatten_dirs_recurses_without_folders(tmp_path):
    nested = tmp_path / "nested"
    deeper = nested / "deeper"
    nested.mkdir()
    deeper.mkdir()
    top_file = tmp_path / "top.ans"
    nested_file = nested / "mid.dur"
    deeper_file = deeper / "deep.txt"
    ignored_file = deeper / "skip.bin"
    top_file.write_text("top")
    nested_file.write_text("nested")
    deeper_file.write_text("deep")
    ignored_file.write_text("skip")
    ui = make_ui("name", flatten_dirs=True)

    file_list, folders = ui.getLocalFileList(str(tmp_path), ["*.ans", "*.dur", "*.txt"])

    assert folders == []
    assert file_list == [
        os.path.join("nested", "deeper", "deep.txt"),
        os.path.join("nested", "mid.dur"),
        "top.ans",
    ]


def test_set_local_play_queue_handles_flattened_relative_paths(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()
    top_file = tmp_path / "top.ans"
    nested_file = nested / "mid.dur"
    top_file.write_text("top")
    nested_file.write_text("nested")
    ui = make_ui("name", flatten_dirs=True)
    selected_name = os.path.join("nested", "mid.dur")

    ui.setLocalPlayQueue(str(tmp_path), [selected_name, "top.ans"], [], selected_name)

    assert ui.appState.play_queue == [str(nested_file), str(top_file)]
    assert ui.appState.play_queue_position == 0


def test_request_viewer_file_change_sets_direction_and_stops_viewer():
    ui = make_ui("name")
    ui.appState.play_queue = ["one.ans", "two.ans"]
    ui.appState.play_queue_position = 0
    ui.appState.play_queue_direction = 0
    ui.appState.topLine = 7
    ui.appState.firstCol = 4
    ui.playing = True

    assert ui.requestViewerFileChange(1) is True
    assert ui.appState.play_queue_direction == 1
    assert ui.playing is False
    assert ui.appState.topLine == 0
    assert ui.appState.firstCol == 0


def test_request_viewer_file_change_ignores_out_of_range_move():
    ui = make_ui("name")
    ui.appState.play_queue = ["one.ans", "two.ans"]
    ui.appState.play_queue_position = 0
    ui.appState.play_queue_direction = 0
    ui.appState.topLine = 7
    ui.appState.firstCol = 4
    ui.playing = True

    assert ui.requestViewerFileChange(-1) is False
    assert ui.appState.play_queue_direction == 0
    assert ui.playing is True
    assert ui.appState.topLine == 7
    assert ui.appState.firstCol == 4


def test_viewer_one_key_logs_current_file_as_good(tmp_path):
    art_file = tmp_path / "one.ans"
    ui = make_ui("name")
    ui.appState.play_queue = [str(art_file)]
    ui.appState.play_queue_position = 0
    messages = []
    ui.log = SimpleNamespace(warning=lambda message: messages.append(message))

    ui.handlePlayOnlyModeInput(ord("1"))

    assert messages == [f"good: {art_file}"]


def test_viewer_zero_key_logs_current_file_as_flagged(tmp_path):
    art_file = tmp_path / "one.ans"
    ui = make_ui("name")
    ui.appState.play_queue = [str(art_file)]
    ui.appState.play_queue_position = 0
    messages = []
    ui.log = SimpleNamespace(warning=lambda message: messages.append(message))

    ui.handlePlayOnlyModeInput(ord("0"))

    assert messages == [f"flagged: {art_file}"]


def test_viewer_file_classification_ignores_remote_archive_entries():
    ui = make_ui("name")
    ui.appState.play_queue = [("16colo.rs", "pack-01", "one.ans")]
    ui.appState.play_queue_position = 0
    messages = []
    ui.log = SimpleNamespace(warning=lambda message: messages.append(message))

    assert ui.logViewerFileClassification("good") is False
    assert messages == []


def test_load_play_queue_position_resolves_sixteenc_queue_item():
    ui = make_ui("name")
    ui.appState.play_queue = [("16colo.rs", "pack-01", "one.ans")]
    ui.appState.play_queue_position = 0
    ui.appState.sixteenc_pack = None
    loaded_urls = []

    ui.sixteenc_api = SimpleNamespace(
        get_url_for_file=lambda pack, filename: f"https://16colo.rs/pack/{pack}/raw/{filename}"
    )
    ui.loadRemoteFile = lambda url: loaded_urls.append(url) or True

    assert ui.loadPlayQueuePosition() is True
    assert loaded_urls == ["https://16colo.rs/pack/pack-01/raw/one.ans"]
    assert ui.appState.sixteenc_pack == "pack-01"


def test_run_play_queue_loads_requested_next_file():
    ui = make_ui("name")
    ui.appState.play_queue = ["one.ans", "two.ans"]
    ui.appState.play_queue_position = 0
    ui.appState.play_queue_direction = 0
    ui.appState.play_queue_auto_advance = False
    ui.appState.durview_running = True
    loaded_positions = []

    def load_position():
        loaded_positions.append(ui.appState.play_queue_position)
        return True

    def enter_view_mode():
        if loaded_positions == [0]:
            ui.appState.play_queue_direction = 1
        else:
            ui.appState.durview_running = False

    ui.loadPlayQueuePosition = load_position
    ui.enterViewMode = enter_view_mode

    ui.runPlayQueue()

    assert loaded_positions == [0, 1]
