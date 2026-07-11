"""MCP server exposing Apple Music control as tools."""

from mcp.server.fastmcp import FastMCP

from . import music_control as mc

mcp = FastMCP("apple-music")


@mcp.tool()
def play() -> str:
    """Resume/start playback in Apple Music."""
    mc.play()
    return "Playing"


@mcp.tool()
def pause() -> str:
    """Pause playback in Apple Music."""
    mc.pause()
    return "Paused"


@mcp.tool()
def play_pause() -> str:
    """Toggle play/pause in Apple Music."""
    mc.play_pause()
    return "Toggled playback"


@mcp.tool()
def next_track() -> str:
    """Skip to the next track."""
    mc.next_track()
    return "Skipped to next track"


@mcp.tool()
def previous_track() -> str:
    """Go back to the previous track."""
    mc.previous_track()
    return "Went to previous track"


@mcp.tool()
def get_current_track() -> mc.PlayerStatus:
    """Get info about the currently playing (or paused) track, including player state."""
    return mc.get_current_track()


@mcp.tool()
def set_volume(level: int) -> str:
    """Set playback volume (0-100)."""
    mc.set_volume(level)
    return f"Volume set to {level}"


@mcp.tool()
def get_volume() -> int:
    """Get the current playback volume (0-100)."""
    return mc.get_volume()


@mcp.tool()
def search_library(query: str, limit: int = 20) -> list[mc.Track]:
    """Search the local Apple Music library by track name, artist, or album."""
    return mc.search_library(query, limit)


@mcp.tool()
def list_playlists() -> list[mc.Playlist]:
    """List all playlists in the Apple Music library."""
    return mc.list_playlists()


@mcp.tool()
def play_playlist(name: str) -> str:
    """Start playing a playlist by exact name."""
    mc.play_playlist(name)
    return f"Playing playlist '{name}'"


@mcp.tool()
def play_track(track_id: int) -> str:
    """Play a specific track by its persistent id (from search_library results)."""
    mc.play_track_by_id(track_id)
    return "Playing track"


def main():
    mcp.run()


if __name__ == "__main__":
    main()
