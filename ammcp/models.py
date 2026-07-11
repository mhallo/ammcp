from dataclasses import dataclass


@dataclass
class Track:
    # `id` is scoped to how the track was looked up (library browse, the
    # currently-playing track, and a playlist copy of the same song can all
    # report different `id`s for the same underlying song) — it's only
    # reliable for identifying one specific occurrence within a single
    # playlist listing (what remove_track_from_playlist needs). For
    # everything else, use `persistent_id`, which stays identical for a
    # given song across all of those contexts.
    id: int
    name: str
    artist: str
    album: str
    persistent_id: str
    # Only populated by get_track_details — list/search endpoints skip these
    # to stay fast, since each extra field costs a round-trip per track.
    genre: str | None = None
    year: int | None = None
    bpm: int | None = None
    date_added: str | None = None
    played_count: int | None = None
    played_date: str | None = None
    skipped_count: int | None = None
    rating: int | None = None
    favorited: bool | None = None


@dataclass
class Playlist:
    id: int
    name: str


@dataclass
class PlayerStatus:
    player_state: str
    track: Track | None = None
    duration: float | None = None
    player_position: float | None = None
