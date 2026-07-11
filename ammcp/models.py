from dataclasses import dataclass


@dataclass
class Track:
    id: int
    name: str
    artist: str
    album: str
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
