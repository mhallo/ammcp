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
            "track": {
                "id": 1,
                "name": "Song",
                "artist": "Artist",
                "album": "Album",
                "persistent_id": "PID1",
            },
            "duration": 180.0,
            "player_position": 42.5,
        }
        mock_run.return_value = cp(stdout=json.dumps(payload))
        status = mc.get_current_track()
        assert status.player_state == "playing"
        assert status.track == mc.Track(
            id=1, name="Song", artist="Artist", album="Album", persistent_id="PID1"
        )
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


class TestAssignmentScriptsDontLeakOutput:
    """osascript prints a script's final expression value; a bare property
    assignment (`x = y;`) is not valid JSON once printed (worse, a bare
    string like "songs" isn't even accidentally-valid JSON like a number
    would be). Every void/mutating script must end on something that
    evaluates to undefined so stdout stays empty."""

    @pytest.mark.parametrize(
        "script_name",
        [
            "_SET_VOLUME",
            "_SEEK_TO",
            "_SET_SHUFFLE_ENABLED",
            "_SET_SHUFFLE_MODE",
            "_SET_REPEAT",
        ],
    )
    def test_ends_with_void_0(self, script_name):
        script = getattr(mc, script_name).strip()
        assert script.endswith("void 0;"), script


class TestSeekAndPlaybackModes:
    def test_seek_to_clamps_negative(self, mock_run, cp):
        mock_run.return_value = cp(stdout="")
        mc.seek_to(-5)
        _, kwargs = mock_run.call_args
        assert "= 0.0;" in kwargs["input"]

    def test_set_shuffle_enabled_only(self, mock_run, cp):
        mock_run.return_value = cp(stdout="")
        mc.set_shuffle(True)
        assert mock_run.call_count == 1
        _, kwargs = mock_run.call_args
        assert "shuffleEnabled = true;" in kwargs["input"]

    def test_set_shuffle_enabled_and_mode(self, mock_run, cp):
        mock_run.return_value = cp(stdout="")
        mc.set_shuffle(True, "albums")
        assert mock_run.call_count == 2
        _, kwargs = mock_run.call_args
        assert 'shuffleMode = "albums";' in kwargs["input"]

    def test_set_shuffle_rejects_invalid_mode(self, mock_run, cp):
        mock_run.return_value = cp(stdout="")
        with pytest.raises(ValueError, match="mode must be one of"):
            mc.set_shuffle(True, "bogus")

    def test_set_repeat(self, mock_run, cp):
        mock_run.return_value = cp(stdout="")
        mc.set_repeat("all")
        _, kwargs = mock_run.call_args
        assert 'songRepeat = "all";' in kwargs["input"]

    def test_set_repeat_rejects_invalid_mode(self, mock_run, cp):
        with pytest.raises(ValueError, match="mode must be one of"):
            mc.set_repeat("bogus")


class TestFavoriteAndRate:
    def test_favorite_track_success(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": True}))
        mc.favorite_track("PID1", True)
        _, kwargs = mock_run.call_args
        assert "favorited = true;" in kwargs["input"]
        assert json.dumps("PID1") in kwargs["input"]

    def test_favorite_track_not_found_raises(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": False, "error": "track not found"}))
        with pytest.raises(MusicControlError, match="track not found"):
            mc.favorite_track("PID999", True)

    def test_rate_track_clamps(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": True}))
        mc.rate_track("PID1", 500)
        _, kwargs = mock_run.call_args
        assert "rating = 100;" in kwargs["input"]

    def test_rate_track_not_found_raises(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": False, "error": "track not found"}))
        with pytest.raises(MusicControlError, match="track not found"):
            mc.rate_track("PID999", 50)


class TestGetTrackDetails:
    def test_returns_full_track(self, mock_run, cp):
        payload = {
            "ok": True,
            "track": {
                "id": 1,
                "name": "Song",
                "artist": "Artist",
                "album": "Album",
                "persistent_id": "PID1",
                "genre": "Metal",
                "year": 1996,
                "bpm": 0,
                "date_added": "2025-10-28T00:55:02.000Z",
                "played_count": 3,
                "played_date": None,
                "skipped_count": 0,
                "rating": 60,
                "favorited": True,
            },
        }
        mock_run.return_value = cp(stdout=json.dumps(payload))
        track = mc.get_track_details("PID1")
        assert track.genre == "Metal"
        assert track.year == 1996
        assert track.favorited is True
        assert track.played_date is None

    def test_not_found_raises(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": False, "error": "track not found"}))
        with pytest.raises(MusicControlError, match="track not found"):
            mc.get_track_details("PID999")


class TestSearchLibrary:
    def test_returns_tracks(self, mock_run, cp):
        payload = [{"id": 1, "name": "A", "artist": "B", "album": "C", "persistent_id": "PID1"}]
        mock_run.return_value = cp(stdout=json.dumps(payload))
        results = mc.search_library("roots", limit=5)
        assert results == [mc.Track(id=1, name="A", artist="B", album="C", persistent_id="PID1")]

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

    def test_play_track_not_found_raises(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": False, "error": "track not found"}))
        with pytest.raises(MusicControlError, match="track not found"):
            mc.play_track("PID999")

    def test_create_playlist(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"id": 5, "name": "New"}))
        assert mc.create_playlist("New") == mc.Playlist(id=5, name="New")

    def test_list_playlist_tracks(self, mock_run, cp):
        payload = {
            "ok": True,
            "tracks": [{"id": 9, "name": "T", "artist": "A", "album": "Al", "persistent_id": "PID9"}],
        }
        mock_run.return_value = cp(stdout=json.dumps(payload))
        assert mc.list_playlist_tracks("Faves") == [
            mc.Track(id=9, name="T", artist="A", album="Al", persistent_id="PID9")
        ]

    def test_list_playlist_tracks_not_found_raises(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": False, "error": "playlist not found"}))
        with pytest.raises(MusicControlError, match="playlist not found"):
            mc.list_playlist_tracks("Nope")

    def test_list_playlist_tracks_sends_offset_and_limit(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": True, "tracks": []}))
        mc.list_playlist_tracks("Faves", offset=100, limit=25)
        _, kwargs = mock_run.call_args
        assert ".slice(100, 100 + 25)" in kwargs["input"]

    def test_list_playlist_tracks_clamps_offset_and_limit(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": True, "tracks": []}))
        mc.list_playlist_tracks("Faves", offset=-5, limit=0)
        _, kwargs = mock_run.call_args
        assert ".slice(0, 0 + 1)" in kwargs["input"]

    def test_search_playlist_tracks(self, mock_run, cp):
        payload = {
            "ok": True,
            "tracks": [{"id": 9, "name": "T", "artist": "A", "album": "Al", "persistent_id": "PID9"}],
        }
        mock_run.return_value = cp(stdout=json.dumps(payload))
        assert mc.search_playlist_tracks("Faves", "t") == [
            mc.Track(id=9, name="T", artist="A", album="Al", persistent_id="PID9")
        ]

    def test_search_playlist_tracks_not_found_raises(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": False, "error": "playlist not found"}))
        with pytest.raises(MusicControlError, match="playlist not found"):
            mc.search_playlist_tracks("Nope", "t")

    def test_add_track_to_playlist_success(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": True}))
        mc.add_track_to_playlist("Faves", "PID1")

    def test_add_track_to_playlist_failure_raises(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": False, "error": "track not found"}))
        with pytest.raises(MusicControlError, match="track not found"):
            mc.add_track_to_playlist("Faves", "PID999")

    def test_remove_track_from_playlist_success(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": True}))
        mc.remove_track_from_playlist("Faves", 1)

    def test_remove_track_from_playlist_not_in_playlist_raises(self, mock_run, cp):
        mock_run.return_value = cp(stdout=json.dumps({"ok": False, "error": "track not in playlist"}))
        with pytest.raises(MusicControlError, match="track not in playlist"):
            mc.remove_track_from_playlist("Faves", 999)
