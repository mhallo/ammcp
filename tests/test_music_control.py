import json

import pytest

from ammcp import music_control as mc
from ammcp.exceptions import MusicControlError


class TestRunJxa:
    def test_raises_on_nonzero_exit(self, mock_run, cp):
        mock_run.return_value = cp(returncode=1, stderr="boom")
        with pytest.raises(MusicControlError, match="boom"):
            mc.play()

    def test_raises_generic_message_when_stderr_empty(self, mock_run, cp):
        mock_run.return_value = cp(returncode=1, stderr="")
        with pytest.raises(MusicControlError, match="osascript failed"):
            mc.play()

    def test_returns_none_for_empty_stdout(self, mock_run, cp):
        mock_run.return_value = cp(stdout="")
        assert mc._run_jxa("void 0;") is None

    def test_sends_script_via_stdin(self, mock_run, cp):
        mock_run.return_value = cp(stdout="")
        mc.play()
        args, kwargs = mock_run.call_args
        assert args[0] == ["osascript", "-l", "JavaScript"]
        assert "play" in kwargs["input"]


class TestPlaybackCommands:
    @pytest.mark.parametrize(
        "func, keyword",
        [
            (mc.play, "play"),
            (mc.pause, "pause"),
            (mc.play_pause, "playpause"),
            (mc.next_track, "nextTrack"),
            (mc.previous_track, "previousTrack"),
        ],
    )
    def test_sends_expected_command(self, mock_run, cp, func, keyword):
        mock_run.return_value = cp(stdout="")
        func()
        _, kwargs = mock_run.call_args
        assert keyword in kwargs["input"]


class TestCurrentTrack:
    def test_returns_full_status_when_playing(self, mock_run, cp):
        payload = {
            "player_state": "playing",
            "track": {"id": 1, "name": "Song", "artist": "Artist", "album": "Album"},
            "duration": 180.0,
            "player_position": 42.5,
        }
        mock_run.return_value = cp(stdout=json.dumps(payload))
        status = mc.get_current_track()
        assert status.player_state == "playing"
        assert status.track == mc.Track(id=1, name="Song", artist="Artist", album="Album")
        assert status.duration == 180.0
        assert status.player_position == 42.5

    def test_returns_no_track_when_stopped(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"player_state": "stopped"}))
        status = mc.get_current_track()
        assert status.player_state == "stopped"
        assert status.track is None


class TestVolume:
    @pytest.mark.parametrize("level, expected", [(50, 50), (-10, 0), (150, 100)])
    def test_set_volume_clamps(self, mock_run, cp, level, expected):
        mock_run.return_value = cp(stdout="")
        mc.set_volume(level)
        _, kwargs = mock_run.call_args
        assert f"= {expected};" in kwargs["input"]

    def test_get_volume(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"volume": 73}))
        assert mc.get_volume() == 73


class TestSearchLibrary:
    def test_returns_tracks(self, mock_run, cp):
        payload = [{"id": 1, "name": "A", "artist": "B", "album": "C"}]
        mock_run.return_value = cp(stdout=json.dumps(payload))
        results = mc.search_library("roots", limit=5)
        assert results == [mc.Track(id=1, name="A", artist="B", album="C")]

    def test_embeds_query_and_limit_safely(self, mock_run, cp):
        mock_run.return_value = cp(stdout="[]")
        mc.search_library('weird "quote" query', limit=3)
        _, kwargs = mock_run.call_args
        assert json.dumps('weird "quote" query') in kwargs["input"]
        assert json.dumps(3) in kwargs["input"]


class TestPlaylists:
    def test_list_playlists(self, mock_run, cp):
        payload = [{"id": 1, "name": "Faves"}]
        mock_run.return_value = cp(stdout=json.dumps(payload))
        assert mc.list_playlists() == [mc.Playlist(id=1, name="Faves")]

    def test_play_playlist_success(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": True}))
        mc.play_playlist("Faves")

    def test_play_playlist_not_found_raises(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": False, "error": "playlist not found"}))
        with pytest.raises(MusicControlError, match="playlist not found"):
            mc.play_playlist("Nope")

    def test_play_track_by_id_not_found_raises(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": False, "error": "track not found"}))
        with pytest.raises(MusicControlError, match="track not found"):
            mc.play_track_by_id(999)

    def test_create_playlist(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"id": 5, "name": "New"}))
        assert mc.create_playlist("New") == mc.Playlist(id=5, name="New")

    def test_list_playlist_tracks(self, mock_run, cp):
        payload = {"ok": True, "tracks": [{"id": 9, "name": "T", "artist": "A", "album": "Al"}]}
        mock_run.return_value = cp(stdout=json.dumps(payload))
        assert mc.list_playlist_tracks("Faves") == [mc.Track(id=9, name="T", artist="A", album="Al")]

    def test_list_playlist_tracks_not_found_raises(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": False, "error": "playlist not found"}))
        with pytest.raises(MusicControlError, match="playlist not found"):
            mc.list_playlist_tracks("Nope")

    def test_add_track_to_playlist_success(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": True}))
        mc.add_track_to_playlist("Faves", 1)

    def test_add_track_to_playlist_failure_raises(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": False, "error": "track not found"}))
        with pytest.raises(MusicControlError, match="track not found"):
            mc.add_track_to_playlist("Faves", 999)

    def test_remove_track_from_playlist_success(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": True}))
        mc.remove_track_from_playlist("Faves", 1)

    def test_remove_track_from_playlist_not_in_playlist_raises(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": False, "error": "track not in playlist"}))
        with pytest.raises(MusicControlError, match="track not in playlist"):
            mc.remove_track_from_playlist("Faves", 999)
