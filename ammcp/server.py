"""MCP server exposing Apple Music control as tools."""

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel

from . import music_control as mc

mcp = FastMCP("apple-music")


@mcp.tool(
    annotations=ToolAnnotations(
        title="Play", readOnlyHint=False, destructiveHint=False, idempotentHint=True
    )
)
def play() -> str:
    """Resume/start playback in Apple Music."""
    mc.play()
    return "Playing"


@mcp.tool(
    annotations=ToolAnnotations(
        title="Pause", readOnlyHint=False, destructiveHint=False, idempotentHint=True
    )
)
def pause() -> str:
    """Pause playback in Apple Music."""
    mc.pause()
    return "Paused"


@mcp.tool(
    annotations=ToolAnnotations(
        title="Toggle Play/Pause", readOnlyHint=False, destructiveHint=False, idempotentHint=False
    )
)
def play_pause() -> str:
    """Toggle play/pause in Apple Music."""
    mc.play_pause()
    return "Toggled playback"


@mcp.tool(
    annotations=ToolAnnotations(
        title="Next Track", readOnlyHint=False, destructiveHint=False, idempotentHint=False
    )
)
def next_track() -> str:
    """Skip to the next track."""
    mc.next_track()
    return "Skipped to next track"


@mcp.tool(
    annotations=ToolAnnotations(
        title="Previous Track", readOnlyHint=False, destructiveHint=False, idempotentHint=False
    )
)
def previous_track() -> str:
    """Go back to the previous track."""
    mc.previous_track()
    return "Went to previous track"


@mcp.tool(
    annotations=ToolAnnotations(
        title="Get Current Track", readOnlyHint=True, destructiveHint=False, idempotentHint=True
    )
)
def get_current_track() -> mc.PlayerStatus:
    """Get info about the currently playing (or paused) track, including player state."""
    return mc.get_current_track()


@mcp.tool(
    annotations=ToolAnnotations(
        title="Set Volume", readOnlyHint=False, destructiveHint=False, idempotentHint=True
    )
)
def set_volume(level: int) -> str:
    """Set playback volume (0-100)."""
    mc.set_volume(level)
    return f"Volume set to {level}"


@mcp.tool(
    annotations=ToolAnnotations(
        title="Get Volume", readOnlyHint=True, destructiveHint=False, idempotentHint=True
    )
)
def get_volume() -> int:
    """Get the current playback volume (0-100)."""
    return mc.get_volume()


@mcp.tool(
    annotations=ToolAnnotations(
        title="Seek To", readOnlyHint=False, destructiveHint=False, idempotentHint=True
    )
)
def seek_to(seconds: float) -> str:
    """Seek to a position (in seconds) within the currently playing track."""
    mc.seek_to(seconds)
    return f"Seeked to {seconds}s"


@mcp.tool(
    annotations=ToolAnnotations(
        title="Set Shuffle", readOnlyHint=False, destructiveHint=False, idempotentHint=True
    )
)
def set_shuffle(enabled: bool, mode: str | None = None) -> str:
    """Turn shuffle on/off, optionally also setting the shuffle mode
    ("songs", "albums", or "groupings")."""
    mc.set_shuffle(enabled, mode)
    return f"Shuffle {'enabled' if enabled else 'disabled'}" + (f" ({mode})" if mode else "")


@mcp.tool(
    annotations=ToolAnnotations(
        title="Set Repeat", readOnlyHint=False, destructiveHint=False, idempotentHint=True
    )
)
def set_repeat(mode: str) -> str:
    """Set repeat mode: "off", "one" (repeat current track), or "all"."""
    mc.set_repeat(mode)
    return f"Repeat set to '{mode}'"


@mcp.tool(
    annotations=ToolAnnotations(
        title="Search Library", readOnlyHint=True, destructiveHint=False, idempotentHint=True
    )
)
def search_library(query: str, limit: int = 20) -> list[mc.Track]:
    """Search the local Apple Music library by track name, artist, or album."""
    return mc.search_library(query, limit)


@mcp.tool(
    annotations=ToolAnnotations(
        title="Get Track Details", readOnlyHint=True, destructiveHint=False, idempotentHint=True
    )
)
def get_track_details(persistent_id: str) -> mc.Track:
    """Get full metadata for a single track by its persistent_id (stable
    across contexts — from search_library, get_current_track, or a
    playlist listing), including genre, year, bpm, date added, play/skip
    counts, rating, and favorited status — fields the list/search tools
    omit to stay fast."""
    return mc.get_track_details(persistent_id)


@mcp.tool(
    annotations=ToolAnnotations(
        title="List Playlists", readOnlyHint=True, destructiveHint=False, idempotentHint=True
    )
)
def list_playlists() -> list[mc.Playlist]:
    """List all playlists in the Apple Music library."""
    return mc.list_playlists()


@mcp.tool(
    annotations=ToolAnnotations(
        title="Play Playlist", readOnlyHint=False, destructiveHint=False, idempotentHint=False
    )
)
def play_playlist(name: str) -> str:
    """Start playing a playlist by exact name."""
    mc.play_playlist(name)
    return f"Playing playlist '{name}'"


@mcp.tool(
    annotations=ToolAnnotations(
        title="Play Track", readOnlyHint=False, destructiveHint=False, idempotentHint=False
    )
)
def play_track(persistent_id: str) -> str:
    """Play a specific track by its persistent_id (from search_library, a
    playlist listing, or get_current_track)."""
    mc.play_track(persistent_id)
    return "Playing track"


@mcp.tool(
    annotations=ToolAnnotations(
        title="Favorite Track", readOnlyHint=False, destructiveHint=False, idempotentHint=True
    )
)
def favorite_track(persistent_id: str, favorited: bool = True) -> str:
    """Favorite (or unfavorite) a track by its persistent_id."""
    mc.favorite_track(persistent_id, favorited)
    return f"{'Favorited' if favorited else 'Unfavorited'} track"


@mcp.tool(
    annotations=ToolAnnotations(
        title="Rate Track", readOnlyHint=False, destructiveHint=False, idempotentHint=True
    )
)
def rate_track(persistent_id: str, rating: int) -> str:
    """Set a track's star rating, 0-100 (20 per star, e.g. 100 = 5 stars, 0 = no rating)."""
    mc.rate_track(persistent_id, rating)
    return f"Rating set to {rating}"


@mcp.tool(
    annotations=ToolAnnotations(
        title="Create Playlist", readOnlyHint=False, destructiveHint=False, idempotentHint=False
    )
)
def create_playlist(name: str) -> mc.Playlist:
    """Create a new, empty playlist."""
    return mc.create_playlist(name)


@mcp.tool(
    annotations=ToolAnnotations(
        title="List Playlist Tracks", readOnlyHint=True, destructiveHint=False, idempotentHint=True
    )
)
def list_playlist_tracks(playlist_name: str, offset: int = 0, limit: int = 50) -> list[mc.Track]:
    """List the tracks currently in a playlist, one page at a time (default
    50). Each track has both `id` (playlist-scoped — what
    remove_track_from_playlist expects) and `persistent_id` (stable across
    contexts — what favorite_track/rate_track/get_track_details/
    add_track_to_playlist/play_track expect). For large playlists, prefer
    search_playlist_tracks to find a specific track instead of paging
    through the whole thing."""
    return mc.list_playlist_tracks(playlist_name, offset, limit)


@mcp.tool(
    annotations=ToolAnnotations(
        title="Search Playlist Tracks", readOnlyHint=True, destructiveHint=False, idempotentHint=True
    )
)
def search_playlist_tracks(playlist_name: str, query: str, limit: int = 20) -> list[mc.Track]:
    """Search within a single playlist by track name, artist, or album.
    Fast even on very large playlists (thousands of tracks) since the
    filtering happens inside Music.app rather than by listing every track.
    Prefer this over list_playlist_tracks when looking for a specific song."""
    return mc.search_playlist_tracks(playlist_name, query, limit)


@mcp.tool(
    annotations=ToolAnnotations(
        title="Add Track to Playlist", readOnlyHint=False, destructiveHint=False, idempotentHint=False
    )
)
def add_track_to_playlist(playlist_name: str, persistent_id: str) -> str:
    """Add a track (by persistent_id from search_library) to an existing playlist."""
    mc.add_track_to_playlist(playlist_name, persistent_id)
    return f"Added track to '{playlist_name}'"


class ConfirmRemoval(BaseModel):
    confirm: bool


@mcp.tool(
    annotations=ToolAnnotations(
        title="Remove Track from Playlist",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
    )
)
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
