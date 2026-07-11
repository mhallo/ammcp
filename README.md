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

## Use with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "apple-music": {
      "command": "uv",
      "args": ["--directory", "/Users/matthallowell/git/ammcp", "run", "ammcp"]
    }
  }
}
```

Restart Claude Desktop. The first tool call will trigger the Automation permission prompt described above.

## Known limitations

- `search_library` only searches your local library, not the full Apple Music catalog (that would need the Apple Music API/MusicKit).
- No queue/"Up Next" manipulation yet.
- No playlist creation/editing yet.
