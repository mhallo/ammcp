from dataclasses import dataclass


@dataclass
class Track:
    id: int
    name: str
    artist: str
    album: str


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
