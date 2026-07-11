from unittest.mock import MagicMock

from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import ElicitResult

from ammcp import server as server_module
from ammcp.models import Playlist, Track


async def _accept(context, params):
    return ElicitResult(action="accept", content={"confirm": True})


async def _decline(context, params):
    return ElicitResult(action="decline")


class TestToolAnnotations:
    async def test_only_remove_track_is_destructive(self):
        tools = await server_module.mcp.list_tools()
        destructive = {t.name for t in tools if t.annotations.destructiveHint}
        assert destructive == {"remove_track_from_playlist"}

    async def test_read_only_tools_are_marked(self):
        tools = await server_module.mcp.list_tools()
        read_only = {t.name for t in tools if t.annotations.readOnlyHint}
        assert read_only == {
            "get_current_track",
            "get_volume",
            "search_library",
            "list_playlists",
            "list_playlist_tracks",
            "search_playlist_tracks",
            "get_track_details",
        }


class TestRemoveTrackElicitation:
    async def test_decline_does_not_touch_the_playlist(self, monkeypatch):
        remove_mock = MagicMock()
        monkeypatch.setattr(server_module.mc, "remove_track_from_playlist", remove_mock)

        async with create_connected_server_and_client_session(
            server_module.mcp._mcp_server, elicitation_callback=_decline
        ) as client:
            result = await client.call_tool(
                "remove_track_from_playlist", {"playlist_name": "Faves", "track_id": 1}
            )

        assert "Cancelled" in result.content[0].text
        remove_mock.assert_not_called()

    async def test_accept_removes_with_the_given_args(self, monkeypatch):
        remove_mock = MagicMock()
        monkeypatch.setattr(server_module.mc, "remove_track_from_playlist", remove_mock)

        async with create_connected_server_and_client_session(
            server_module.mcp._mcp_server, elicitation_callback=_accept
        ) as client:
            result = await client.call_tool(
                "remove_track_from_playlist", {"playlist_name": "Faves", "track_id": 1}
            )

        assert "Removed" in result.content[0].text
        remove_mock.assert_called_once_with("Faves", 1)


class TestToolsDelegateToMusicControl:
    async def test_create_playlist(self, monkeypatch):
        monkeypatch.setattr(
            server_module.mc, "create_playlist", MagicMock(return_value=Playlist(id=1, name="New"))
        )
        async with create_connected_server_and_client_session(server_module.mcp._mcp_server) as client:
            result = await client.call_tool("create_playlist", {"name": "New"})
        assert result.structuredContent == {"id": 1, "name": "New"}

    async def test_search_library(self, monkeypatch):
        monkeypatch.setattr(
            server_module.mc,
            "search_library",
            MagicMock(return_value=[Track(id=1, name="A", artist="B", album="C")]),
        )
        async with create_connected_server_and_client_session(server_module.mcp._mcp_server) as client:
            result = await client.call_tool("search_library", {"query": "a"})
        [track] = result.structuredContent["result"]
        assert track["id"] == 1
        assert track["name"] == "A"
        assert track["artist"] == "B"
        assert track["album"] == "C"

    async def test_favorite_track(self, monkeypatch):
        favorite_mock = MagicMock()
        monkeypatch.setattr(server_module.mc, "favorite_track", favorite_mock)
        async with create_connected_server_and_client_session(server_module.mcp._mcp_server) as client:
            result = await client.call_tool("favorite_track", {"track_id": 1, "favorited": False})
        assert "Unfavorited" in result.content[0].text
        favorite_mock.assert_called_once_with(1, False)

    async def test_get_track_details(self, monkeypatch):
        monkeypatch.setattr(
            server_module.mc,
            "get_track_details",
            MagicMock(return_value=Track(id=1, name="A", artist="B", album="C", genre="Metal")),
        )
        async with create_connected_server_and_client_session(server_module.mcp._mcp_server) as client:
            result = await client.call_tool("get_track_details", {"track_id": 1})
        assert result.structuredContent["genre"] == "Metal"
