# ammcp

MCP server for controlling Apple Music on macOS. Talks to `Music.app` directly over JXA (`osascript -l JavaScript`), no API key or MusicKit setup required. macOS only, and Music.app needs to be installed.

## Setup

```bash
uv sync
```

## Try it standalone

```bash
uv run python -c "from ammcp import music_control as mc; print(mc.get_current_track())"
```

First run triggers a macOS Automation permission prompt for whatever process is calling in (Terminal, Claude Desktop, etc). If you miss it or deny it, fix it manually in System Settings → Privacy & Security → Automation, and check "Music" for the relevant app.

## Tools

- `play`, `pause`, `play_pause`, `next_track`, `previous_track`
- `get_current_track` — name/artist/album/duration/position/player state
- `set_volume(level)`, `get_volume`
- `seek_to(seconds)` — seek within the current track
- `set_shuffle(enabled, mode)` — mode is `"songs"`, `"albums"`, or `"groupings"`
- `set_repeat(mode)` — `"off"`, `"one"`, or `"all"`
- `search_library(query, limit)` — searches local library by name/artist/album
- `get_track_details(persistent_id)` — genre, year, bpm, date added, play/skip counts, rating, favorited. Not included in list/search results, since each field costs a round-trip to Music.app
- `favorite_track(persistent_id, favorited)`, `rate_track(persistent_id, rating)` — rating is 0-100, 20 per star
- `list_playlists`
- `play_playlist(name)`
- `play_track(persistent_id)` — see "id vs persistent_id" below
- `create_playlist(name)`
- `list_playlist_tracks(playlist_name, offset, limit)` — paginated, 50 per page by default
- `search_playlist_tracks(playlist_name, query, limit)` — filters inside Music.app itself, fast even on huge playlists. Use this instead of paging through `list_playlist_tracks` when you already know what you're looking for
- `add_track_to_playlist(playlist_name, persistent_id)` — see "id vs persistent_id" below
- `remove_track_from_playlist(playlist_name, track_id)` — takes `track_id` from `list_playlist_tracks`, not `persistent_id`. Destructive and irreversible: marked `destructiveHint: true`, and always confirms via MCP elicitation before deleting anything. If the client doesn't support elicitation, the call just fails instead of deleting silently

## id vs persistent_id

Every `Track` has both, and each tool expects a specific one:

- `persistent_id` — stable for a song across every context: library, currently-playing, a copy inside a playlist. Used by `play_track`, `favorite_track`, `rate_track`, `get_track_details`, `add_track_to_playlist`.
- `id` — scoped to how the track was looked up. Music.app assigns a new `id` when a track is duplicated into a playlist, and the currently-playing track often reports yet another `id` for the same song. Only useful for picking one occurrence out of a playlist listing, which is what `remove_track_from_playlist` needs — two copies of the same song in one playlist share a `persistent_id`, so only `id` tells them apart.

Using the wrong one fails with `"track not found"` rather than silently doing the wrong thing.

One more catch: a track streaming straight from Apple Music's catalog (not saved to your library — `class: "urlTrack"`) has no valid id at all, `persistent_id` included, since `whose()` lookups only search your library. `get_current_track` still reports it fine, but `get_track_details`/`favorite_track`/etc. on that track will fail. That's a limit of Music.app's scripting, not something fixable here.

## Not scriptable

- EQ enable/preset — `EQ enabled` can't be set from JXA or plain AppleScript (`Can't set EQ enabled`, error -10006). Locked down at the app level.
- AirPlay device selection — `airplayDevices` can be listed and looks settable via `.selected`, but isn't wired up here yet. Worth adding if you want to route playback to another device.
- Music.app's native `search` command errors over JXA (`Can't convert types`). The `whose()` filtering used throughout this project is the working alternative.

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

Restart Claude Desktop. The first tool call triggers the Automation permission prompt described above.

## Known limitations

- `search_library` only searches your local library, not the full Apple Music catalog (would need the Apple Music API/MusicKit for that).
- No queue/"Up Next" manipulation — Music.app no longer exposes that via AppleScript on modern macOS.
- No playlist deletion (only track removal), and no reordering.
