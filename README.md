# ammcp

MCP server for controlling Apple Music on macOS, using JXA (`osascript -l JavaScript`) — no API keys, no MusicKit, just talks to `Music.app` directly. Only works on macOS with Music.app installed.

## Setup

```bash
uv sync
```

## Try it standalone

```bash
uv run python -c "from ammcp import music_control as mc; print(mc.get_current_track())"
```

The first time this runs, macOS will prompt for **Automation** permission — the process (Terminal, or whatever spawns the server) needs permission to control Music.app. If you miss the prompt or deny it, re-enable it at:

**System Settings → Privacy & Security → Automation** → find the app/process and check "Music".

## Tools

- `play`, `pause`, `play_pause`, `next_track`, `previous_track`
- `get_current_track` — name/artist/album/duration/position/player state
- `set_volume(level)`, `get_volume`
- `search_library(query, limit)` — searches local library by name/artist/album
- `list_playlists`
- `play_playlist(name)`
- `play_track(track_id)` — play a track by id from `search_library` results
- `create_playlist(name)`
- `list_playlist_tracks(playlist_name)` — returns tracks with **playlist-scoped** ids (Music.app assigns a new id when a track is added to a playlist, so these are not the same ids `search_library` returns)
- `add_track_to_playlist(playlist_name, track_id)` — `track_id` from `search_library`
- `remove_track_from_playlist(playlist_name, track_id)` — `track_id` from `list_playlist_tracks`. **Destructive and irreversible.** Marked `destructiveHint: true` in its tool annotations, and always asks the connecting client to confirm via MCP elicitation before removing anything — if the client doesn't support elicitation, the call will fail rather than silently deleting.

## Tests

```bash
uv sync --group dev
uv run pytest
```

Tests mock `subprocess`/the MCP transport, so they don't touch your real Music.app or library.

## Use with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "apple-music": {
      "command": "uv",
      "args": ["--directory", "/<your-clone-path>/ammcp", "run", "ammcp"]
    }
  }
}
```

Restart Claude Desktop. The first tool call will trigger the Automation permission prompt described above.

## Known limitations

- `search_library` only searches your local library, not the full Apple Music catalog (that would need the Apple Music API/MusicKit).
- No queue/"Up Next" manipulation — Music.app no longer exposes that via AppleScript on modern macOS.
- No playlist deletion (only track removal) or reordering yet.
