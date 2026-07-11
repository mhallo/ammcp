"""MCP server exposing Apple Music control as tools."""

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel

from . import music_control as mc

mcp = FastMCP("apple-music")


def music_tool(title: str, *, read_only: bool = False, destructive: bool = False, idempotent: bool):
    return mcp.tool(
        annotations=ToolAnnotations(
            title=title, readOnlyHint=read_only, destructiveHint=destructive, idempotentHint=idempotent
        )
    )


@music_tool("Play", idempotent=True)
def play() -> str:
    """Resume/start playback in Apple Music."""
    mc.play()
    return "Playing"


@music_tool("Pause", idempotent=True)
def pause() -> str:
    """Pause playback in Apple Music."""
    mc.pause()
    return "Paused"


@music_tool("Toggle Play/Pause", idempotent=False)
def play_pause() -> str:
    """Toggle play/pause in Apple Music."""
    mc.play_pause()
    return "Toggled playback"


@music_tool("Next Track", idempotent=False)
def next_track() -> str:
    """Skip to the next track."""
    mc.next_track()
    return "Skipped to next track"


@music_tool("Previous Track", idempotent=False)
def previous_track() -> str:
    """Go back to the previous track."""
    mc.previous_track()
    return "Went to previous track"


@music_tool("Get Current Track", read_only=True, idempotent=True)
def get_current_track() -> mc.PlayerStatus:
    """Get info about the currently playing (or paused) track, including player state."""
    return mc.get_current_track()


@music_tool("Set Volume", idempotent=True)
def set_volume(level: int) -> str:
    """Set playback volume (0-100)."""
    mc.set_volume(level)
    return f"Volume set to {level}"


@music_tool("Get Volume", read_only=True, idempotent=True)
def get_volume() -> int:
    """Get the current playback volume (0-100)."""
    return mc.get_volume()


@music_tool("Seek To", idempotent=True)
def seek_to(seconds: float) -> str:
    """Seek to a position (in seconds) within the currently playing track."""
    mc.seek_to(seconds)
    return f"Seeked to {seconds}s"


@music_tool("Set Shuffle", idempotent=True)
def set_shuffle(enabled: bool, mode: str | None = None) -> str:
    """Turn shuffle on/off, optionally also setting the shuffle mode
    ("songs", "albums", or "groupings")."""
    mc.set_shuffle(enabled, mode)
    return f"Shuffle {'enabled' if enabled else 'disabled'}" + (f" ({mode})" if mode else "")


@music_tool("Set Repeat", idempotent=True)
def set_repeat(mode: str) -> str:
    """Set repeat mode: "off", "one" (repeat current track), or "all"."""
    mc.set_repeat(mode)
    return f"Repeat set to '{mode}'"


@music_tool("Search Library", read_only=True, idempotent=True)
def search_library(query: str, limit: int = 20) -> list[mc.Track]:
    """Search the local Apple Music library by track name, artist, or album."""
    return mc.search_library(query, limit)


@music_tool("Get Track Details", read_only=True, idempotent=True)
def get_track_details(persistent_id: str) -> mc.Track:
    """Get full metadata for a single track by its persistent_id (from
    search_library, get_current_track, or a playlist listing), including
    genre, year, bpm, date added, play/skip counts, rating, and favorited
    status — fields the list/search tools omit to stay fast."""
    return mc.get_track_details(persistent_id)


@music_tool("List Playlists", read_only=True, idempotent=True)
def list_playlists() -> list[mc.Playlist]:
    """List all playlists in the Apple Music library."""
    return mc.list_playlists()


@music_tool("Play Playlist", idempotent=False)
def play_playlist(name: str) -> str:
    """Start playing a playlist by exact name."""
    mc.play_playlist(name)
    return f"Playing playlist '{name}'"


@music_tool("Play Track", idempotent=False)
def play_track(persistent_id: str) -> str:
    """Play a specific track by its persistent_id (from search_library, a
    playlist listing, or get_current_track)."""
    mc.play_track(persistent_id)
    return "Playing track"


@music_tool("Favorite Track", idempotent=True)
def favorite_track(persistent_id: str, favorited: bool = True) -> str:
    """Favorite (or unfavorite) a track by its persistent_id (from
    search_library, get_current_track, or a playlist listing)."""
    mc.favorite_track(persistent_id, favorited)
    return f"{'Favorited' if favorited else 'Unfavorited'} track"


@music_tool("Rate Track", idempotent=True)
def rate_track(persistent_id: str, rating: int) -> str:
    """Set a track's star rating, 0-100 (20 per star, e.g. 100 = 5 stars,
    0 = no rating). persistent_id can come from search_library,
    get_current_track, or a playlist listing."""
    mc.rate_track(persistent_id, rating)
    return f"Rating set to {rating}"


@music_tool("Create Playlist", idempotent=False)
def create_playlist(name: str) -> mc.Playlist:
    """Create a new, empty playlist."""
    return mc.create_playlist(name)


@music_tool("List Playlist Tracks", read_only=True, idempotent=True)
def list_playlist_tracks(playlist_name: str, offset: int = 0, limit: int = 50) -> list[mc.Track]:
    """List the tracks currently in a playlist, one page at a time (default
    50). Each track has both `id` (playlist-scoped — what
    remove_track_from_playlist expects) and `persistent_id` (stable across
    contexts — what favorite_track/rate_track/get_track_details/
    add_track_to_playlist/play_track expect). For large playlists, prefer
    search_playlist_tracks to find a specific track instead of paging
    through the whole thing."""
    return mc.list_playlist_tracks(playlist_name, offset, limit)


@music_tool("Search Playlist Tracks", read_only=True, idempotent=True)
def search_playlist_tracks(playlist_name: str, query: str, limit: int = 20) -> list[mc.Track]:
    """Search within a single playlist by track name, artist, or album.
    Fast even on very large playlists (thousands of tracks) since the
    filtering happens inside Music.app rather than by listing every track.
    Prefer this over list_playlist_tracks when looking for a specific song."""
    return mc.search_playlist_tracks(playlist_name, query, limit)


@music_tool("Add Track to Playlist", idempotent=False)
def add_track_to_playlist(playlist_name: str, persistent_id: str) -> str:
    """Add a track (by persistent_id from search_library, get_current_track,
    or a playlist listing) to an existing playlist."""
    mc.add_track_to_playlist(playlist_name, persistent_id)
    return f"Added track to '{playlist_name}'"


class ConfirmRemoval(BaseModel):
    confirm: bool


@music_tool("Remove Track from Playlist", destructive=True, idempotent=False)
async def remove_track_from_playlist(playlist_name: str, track_id: int, ctx: Context) -> str:
    """Remove a track from a playlist. DESTRUCTIVE and irreversible — always
    asks the user to confirm before removing. track_id must be a
    playlist-scoped id from list_playlist_tracks, not a search_library id."""
    elicitation = await ctx.elicit(
        message=(
            f"Remove track {track_id} from playlist '{playlist_name}'? "
            "This cannot be undone."
        ),
        schema=ConfirmRemoval,
    )
    if elicitation.action != "accept" or not elicitation.data.confirm:
        return "Cancelled — track was not removed."
    mc.remove_track_from_playlist(playlist_name, track_id)
    return f"Removed track from '{playlist_name}'"


def main():
    mcp.run()


if __name__ == "__main__":
    main()
