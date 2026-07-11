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
        title="Search Library", readOnlyHint=True, destructiveHint=False, idempotentHint=True
    )
)
def search_library(query: str, limit: int = 20) -> list[mc.Track]:
    """Search the local Apple Music library by track name, artist, or album."""
    return mc.search_library(query, limit)


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
def play_track(track_id: int) -> str:
    """Play a specific track by its library-wide id (from search_library results)."""
    mc.play_track_by_id(track_id)
    return "Playing track"


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
def list_playlist_tracks(playlist_name: str) -> list[mc.Track]:
    """List the tracks currently in a playlist. The returned track ids are
    playlist-scoped (not the same as search_library ids) and are what
    remove_track_from_playlist expects."""
    return mc.list_playlist_tracks(playlist_name)


@mcp.tool(
    annotations=ToolAnnotations(
        title="Add Track to Playlist", readOnlyHint=False, destructiveHint=False, idempotentHint=False
    )
)
def add_track_to_playlist(playlist_name: str, track_id: int) -> str:
    """Add a track (by library-wide id from search_library) to an existing playlist."""
    mc.add_track_to_playlist(playlist_name, track_id)
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
