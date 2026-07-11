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
- `seek_to(seconds)` — seek within the current track
- `set_shuffle(enabled, mode)` — `mode` is `"songs"`, `"albums"`, or `"groupings"`
- `set_repeat(mode)` — `"off"`, `"one"`, or `"all"`
- `search_library(query, limit)` — searches local library by name/artist/album
- `get_track_details(persistent_id)` — full metadata for one track (genre, year, bpm, date added, play/skip counts, rating, favorited). Omitted from list/search results to keep those fast — each extra field is a separate round-trip to Music.app per track, so it only makes sense to fetch them one track at a time
- `favorite_track(persistent_id, favorited)`, `rate_track(persistent_id, rating)` — rating is 0-100, 20 per star
- `list_playlists`
- `play_playlist(name)`
- `play_track(persistent_id)` — play a track by persistent_id from `search_library` results
- `create_playlist(name)`
- `list_playlist_tracks(playlist_name, offset, limit)` — paginated (default 50/page)
- `search_playlist_tracks(playlist_name, query, limit)` — filters server-side inside Music.app, so it's fast even on playlists with thousands of tracks. Prefer this over paging through `list_playlist_tracks` when looking for something specific
- `add_track_to_playlist(playlist_name, persistent_id)` — `persistent_id` from `search_library`
- `remove_track_from_playlist(playlist_name, track_id)` — `track_id` (not `persistent_id`!) from `list_playlist_tracks`. **Destructive and irreversible.** Marked `destructiveHint: true` in its tool annotations, and always asks the connecting client to confirm via MCP elicitation before removing anything — if the client doesn't support elicitation, the call will fail rather than silently deleting.

### Two track identifiers — `id` vs `persistent_id`

Every `Track` carries both, and which one to use depends on the operation:

- **`persistent_id`** — stable for a given song across every context (library browse, currently-playing, a copy inside a playlist). Use this for anything that means "this song": `play_track`, `favorite_track`, `rate_track`, `get_track_details`, `add_track_to_playlist`.
- **`id`** — scoped to *how* the track was looked up. Music.app hands out a fresh `id` when a track is duplicated into a playlist, and the currently-playing track can report yet another `id` for the same song. Only reliable for identifying one specific occurrence within a single playlist listing — which is exactly what `remove_track_from_playlist` needs (if a song appears twice in one playlist, both copies share a `persistent_id`, so only `id` can tell them apart).

Mixing these up fails loudly (`"track not found"`), not silently.

**A further wrinkle:** a currently-playing track that isn't in your local library at all — streaming directly from Apple Music's catalog (`class: "urlTrack"`) rather than a saved library item — isn't addressable by *any* id, `persistent_id` included, since `whose()` lookups only search `app.tracks` (your library). `get_current_track` will still report it, but a follow-up `get_track_details`/`favorite_track`/etc. on that id will fail. This is a boundary of what Music.app's scripting bridge exposes, not something this project can work around.

### Not scriptable (verified, not just undocumented)

- **EQ enable/preset** — `EQ enabled` can't be set at all in the current Music.app, even from plain AppleScript (`Can't set EQ enabled`, error -10006). Apple appears to have locked this down at the app level.
- **AirPlay output device selection** — `airplayDevices` can be listed (and looks settable via `.selected`) but wasn't wired up here; a reasonable follow-up if you want to route playback to another device.
- Music.app's native `search` command errors over JXA (`Can't convert types`) — the `whose()`-based filtering used throughout this project is the working alternative.

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
