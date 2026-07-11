"""Control Apple Music on macOS via JXA (JavaScript for Automation).

Each JXA script is a module-level template; `{placeholders}` are filled via
`.format()` with `json.dumps()`-encoded values, so they're always valid JS
literals regardless of what the caller passes in.
"""

import json
import subprocess

from .exceptions import MusicControlError
from .models import Playlist, PlayerStatus, Track

_TIMEOUT = 10

_PLAY = 'Application("Music").play();'
_PAUSE = 'Application("Music").pause();'
_PLAY_PAUSE = 'Application("Music").playpause();'
_NEXT_TRACK = 'Application("Music").nextTrack();'
_PREVIOUS_TRACK = 'Application("Music").previousTrack();'

_GET_VOLUME = 'JSON.stringify({volume: Application("Music").soundVolume()});'
# osascript prints the value of a script's final expression; a bare
# assignment evaluates to the assigned value, which isn't valid JSON for
# strings (and only accidentally valid for numbers/booleans). Ending on
# `void 0` keeps these void calls' stdout empty.
_SET_VOLUME = 'Application("Music").soundVolume = {level}; void 0;'

_CURRENT_TRACK = """
const app = Application("Music");
const result = { player_state: app.playerState() };
try {
    const t = app.currentTrack();
    result.track = { id: t.id(), name: t.name(), artist: t.artist(), album: t.album() };
    result.duration = t.duration();
    result.player_position = app.playerPosition();
} catch (e) {}
JSON.stringify(result);
"""

_SEARCH_LIBRARY = """
const app = Application("Music");
const q = {query};
const seen = new Set();
const results = [];
outer:
for (const field of ["name", "artist", "album"]) {{
    const clause = {{}};
    clause[field] = {{_contains: q}};
    for (const t of app.tracks.whose(clause)()) {{
        const id = t.id();
        if (seen.has(id)) continue;
        seen.add(id);
        results.push({{ id, name: t.name(), artist: t.artist(), album: t.album() }});
        if (results.length >= {limit}) break outer;
    }}
}}
JSON.stringify(results);
"""

_LIST_PLAYLISTS = """
const app = Application("Music");
JSON.stringify(app.playlists().map(p => ({ id: p.id(), name: p.name() })));
"""

_PLAY_PLAYLIST = """
const app = Application("Music");
const matches = app.playlists.whose({{name: {name}}})();
if (matches.length === 0) {{
    JSON.stringify({{ok: false, error: "playlist not found"}});
}} else {{
    app.play(matches[0]);
    JSON.stringify({{ok: true}});
}}
"""

_PLAY_TRACK_BY_ID = """
const app = Application("Music");
const matches = app.tracks.whose({{id: {track_id}}})();
if (matches.length === 0) {{
    JSON.stringify({{ok: false, error: "track not found"}});
}} else {{
    app.play(matches[0]);
    JSON.stringify({{ok: true}});
}}
"""

_CREATE_PLAYLIST = """
const app = Application("Music");
const p = app.make({{new: "playlist", withProperties: {{name: {name}}}}});
JSON.stringify({{id: p.id(), name: p.name()}});
"""

_LIST_PLAYLIST_TRACKS = """
const app = Application("Music");
const playlists = app.playlists.whose({{name: {playlist_name}}})();
if (playlists.length === 0) {{
    JSON.stringify({{ok: false, error: "playlist not found"}});
}} else {{
    const page = playlists[0].tracks().slice({offset}, {offset} + {limit});
    const tracks = page.map(t => ({{ id: t.id(), name: t.name(), artist: t.artist(), album: t.album() }}));
    JSON.stringify({{ok: true, tracks}});
}}
"""

_SEARCH_PLAYLIST_TRACKS = """
const app = Application("Music");
const playlists = app.playlists.whose({{name: {playlist_name}}})();
if (playlists.length === 0) {{
    JSON.stringify({{ok: false, error: "playlist not found"}});
}} else {{
    const q = {query};
    const seen = new Set();
    const results = [];
    outer:
    for (const field of ["name", "artist", "album"]) {{
        const clause = {{}};
        clause[field] = {{_contains: q}};
        for (const t of playlists[0].tracks.whose(clause)()) {{
            const id = t.id();
            if (seen.has(id)) continue;
            seen.add(id);
            results.push({{ id, name: t.name(), artist: t.artist(), album: t.album() }});
            if (results.length >= {limit}) break outer;
        }}
    }}
    JSON.stringify({{ok: true, tracks: results}});
}}
"""

_ADD_TRACK_TO_PLAYLIST = """
const app = Application("Music");
const tracks = app.tracks.whose({{id: {track_id}}})();
const playlists = app.playlists.whose({{name: {playlist_name}}})();
if (tracks.length === 0) {{
    JSON.stringify({{ok: false, error: "track not found"}});
}} else if (playlists.length === 0) {{
    JSON.stringify({{ok: false, error: "playlist not found"}});
}} else {{
    app.duplicate(tracks[0], {{to: playlists[0]}});
    JSON.stringify({{ok: true}});
}}
"""

_REMOVE_TRACK_FROM_PLAYLIST = """
const app = Application("Music");
const playlists = app.playlists.whose({{name: {playlist_name}}})();
if (playlists.length === 0) {{
    JSON.stringify({{ok: false, error: "playlist not found"}});
}} else {{
    const matches = playlists[0].tracks.whose({{id: {track_id}}})();
    if (matches.length === 0) {{
        JSON.stringify({{ok: false, error: "track not in playlist"}});
    }} else {{
        app.delete(matches[0]);
        JSON.stringify({{ok: true}});
    }}
}}
"""

_SEEK_TO = 'Application("Music").playerPosition = {seconds}; void 0;'
_SET_SHUFFLE_ENABLED = 'Application("Music").shuffleEnabled = {enabled}; void 0;'
_SET_SHUFFLE_MODE = 'Application("Music").shuffleMode = {mode}; void 0;'
_SET_REPEAT = 'Application("Music").songRepeat = {mode}; void 0;'

_FAVORITE_TRACK = """
const app = Application("Music");
const matches = app.tracks.whose({{id: {track_id}}})();
if (matches.length === 0) {{
    JSON.stringify({{ok: false, error: "track not found"}});
}} else {{
    matches[0].favorited = {favorited};
    JSON.stringify({{ok: true}});
}}
"""

_RATE_TRACK = """
const app = Application("Music");
const matches = app.tracks.whose({{id: {track_id}}})();
if (matches.length === 0) {{
    JSON.stringify({{ok: false, error: "track not found"}});
}} else {{
    matches[0].rating = {rating};
    JSON.stringify({{ok: true}});
}}
"""

_GET_TRACK_DETAILS = """
const app = Application("Music");
const matches = app.tracks.whose({{id: {track_id}}})();
if (matches.length === 0) {{
    JSON.stringify({{ok: false, error: "track not found"}});
}} else {{
    const t = matches[0];
    JSON.stringify({{ok: true, track: {{
        id: t.id(), name: t.name(), artist: t.artist(), album: t.album(),
        genre: t.genre(), year: t.year(), bpm: t.bpm(),
        date_added: t.dateAdded(), played_count: t.playedCount(),
        played_date: t.playedDate(), skipped_count: t.skippedCount(),
        rating: t.rating(), favorited: t.favorited()
    }}}});
}}
"""


def _run_jxa(script: str):
    result = subprocess.run(
        ["osascript", "-l", "JavaScript"],
        input=script,
        capture_output=True,
        text=True,
        timeout=_TIMEOUT,
    )
    if result.returncode != 0:
        raise MusicControlError(result.stderr.strip() or "osascript failed")
    stdout = result.stdout.strip()
    return json.loads(stdout) if stdout else None


def _raise_if_not_ok(result: dict) -> None:
    if not result.get("ok", True):
        raise MusicControlError(result.get("error", "operation failed"))


def play() -> None:
    _run_jxa(_PLAY)


def pause() -> None:
    _run_jxa(_PAUSE)


def play_pause() -> None:
    _run_jxa(_PLAY_PAUSE)


def next_track() -> None:
    _run_jxa(_NEXT_TRACK)


def previous_track() -> None:
    _run_jxa(_PREVIOUS_TRACK)


def get_current_track() -> PlayerStatus:
    data = _run_jxa(_CURRENT_TRACK)
    track = Track(**data["track"]) if "track" in data else None
    return PlayerStatus(
        player_state=data["player_state"],
        track=track,
        duration=data.get("duration"),
        player_position=data.get("player_position"),
    )


def set_volume(level: int) -> None:
    level = max(0, min(100, int(level)))
    _run_jxa(_SET_VOLUME.format(level=level))


def get_volume() -> int:
    return _run_jxa(_GET_VOLUME)["volume"]


def search_library(query: str, limit: int = 20) -> list[Track]:
    script = _SEARCH_LIBRARY.format(query=json.dumps(query), limit=json.dumps(max(1, int(limit))))
    return [Track(**t) for t in _run_jxa(script)]


def list_playlists() -> list[Playlist]:
    return [Playlist(**p) for p in _run_jxa(_LIST_PLAYLISTS)]


def play_playlist(name: str) -> None:
    script = _PLAY_PLAYLIST.format(name=json.dumps(name))
    _raise_if_not_ok(_run_jxa(script))


def play_track_by_id(track_id: int) -> None:
    script = _PLAY_TRACK_BY_ID.format(track_id=json.dumps(track_id))
    _raise_if_not_ok(_run_jxa(script))


def create_playlist(name: str) -> Playlist:
    script = _CREATE_PLAYLIST.format(name=json.dumps(name))
    return Playlist(**_run_jxa(script))


def list_playlist_tracks(playlist_name: str, offset: int = 0, limit: int = 50) -> list[Track]:
    # Property access (name/artist/album) costs one Apple Event round-trip
    # per track, so this is paginated to stay well under the osascript
    # timeout on large playlists. Prefer search_playlist_tracks when you're
    # looking for a specific track — `whose()` filtering runs server-side
    # and is fast regardless of playlist size.
    script = _LIST_PLAYLIST_TRACKS.format(
        playlist_name=json.dumps(playlist_name),
        offset=json.dumps(max(0, int(offset))),
        limit=json.dumps(max(1, int(limit))),
    )
    result = _run_jxa(script)
    _raise_if_not_ok(result)
    return [Track(**t) for t in result["tracks"]]


def search_playlist_tracks(playlist_name: str, query: str, limit: int = 20) -> list[Track]:
    script = _SEARCH_PLAYLIST_TRACKS.format(
        playlist_name=json.dumps(playlist_name),
        query=json.dumps(query),
        limit=json.dumps(max(1, int(limit))),
    )
    result = _run_jxa(script)
    _raise_if_not_ok(result)
    return [Track(**t) for t in result["tracks"]]


def add_track_to_playlist(playlist_name: str, track_id: int) -> None:
    # track_id is a library-wide id (e.g. from search_library).
    script = _ADD_TRACK_TO_PLAYLIST.format(
        playlist_name=json.dumps(playlist_name), track_id=json.dumps(track_id)
    )
    _raise_if_not_ok(_run_jxa(script))


def remove_track_from_playlist(playlist_name: str, track_id: int) -> None:
    # track_id here is playlist-scoped, not the library-wide id — Music.app
    # assigns a new id when a track is duplicated into a playlist, so this
    # must come from list_playlist_tracks, not search_library.
    script = _REMOVE_TRACK_FROM_PLAYLIST.format(
        playlist_name=json.dumps(playlist_name), track_id=json.dumps(track_id)
    )
    _raise_if_not_ok(_run_jxa(script))


_SHUFFLE_MODES = {"songs", "albums", "groupings"}
_REPEAT_MODES = {"off", "one", "all"}


def seek_to(seconds: float) -> None:
    _run_jxa(_SEEK_TO.format(seconds=json.dumps(max(0.0, float(seconds)))))


def set_shuffle(enabled: bool, mode: str | None = None) -> None:
    _run_jxa(_SET_SHUFFLE_ENABLED.format(enabled=json.dumps(bool(enabled))))
    if mode is not None:
        if mode not in _SHUFFLE_MODES:
            raise ValueError(f"mode must be one of {sorted(_SHUFFLE_MODES)}")
        _run_jxa(_SET_SHUFFLE_MODE.format(mode=json.dumps(mode)))


def set_repeat(mode: str) -> None:
    if mode not in _REPEAT_MODES:
        raise ValueError(f"mode must be one of {sorted(_REPEAT_MODES)}")
    _run_jxa(_SET_REPEAT.format(mode=json.dumps(mode)))


def favorite_track(track_id: int, favorited: bool = True) -> None:
    script = _FAVORITE_TRACK.format(track_id=json.dumps(track_id), favorited=json.dumps(bool(favorited)))
    _raise_if_not_ok(_run_jxa(script))


def rate_track(track_id: int, rating: int) -> None:
    rating = max(0, min(100, int(rating)))
    script = _RATE_TRACK.format(track_id=json.dumps(track_id), rating=json.dumps(rating))
    _raise_if_not_ok(_run_jxa(script))


def get_track_details(track_id: int) -> Track:
    script = _GET_TRACK_DETAILS.format(track_id=json.dumps(track_id))
    result = _run_jxa(script)
    _raise_if_not_ok(result)
    return Track(**result["track"])
