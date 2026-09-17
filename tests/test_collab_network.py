"""Tests for collaboration networking: LAN discovery and P2P connection."""

import json
import time
import pytest
from unittest.mock import MagicMock, patch

from ecrit.collab.lan import LANPeer, LANDiscovery, SERVICE_ID, DISCOVERY_PORT
from ecrit.collab.p2p import ConnectionToken, P2PConnection


class TestLANPeer:
    def test_is_stale_fresh(self):
        peer = LANPeer(
            user_id="u1", user_name="Alice",
            ip_address="192.168.1.10", port=8741,
            last_seen=time.time(),
        )
        assert not peer.is_stale()

    def test_is_stale_old(self):
        peer = LANPeer(
            user_id="u1", user_name="Alice",
            ip_address="192.168.1.10", port=8741,
            last_seen=time.time() - 20.0,
        )
        assert peer.is_stale(timeout=10.0)

    def test_session_id_default(self):
        peer = LANPeer(
            user_id="u1", user_name="A",
            ip_address="127.0.0.1", port=8741,
        )
        assert peer.session_id == ""

    def test_project_title_default(self):
        peer = LANPeer(
            user_id="u1", user_name="A",
            ip_address="127.0.0.1", port=8741,
        )
        assert peer.project_title == ""


class TestLANDiscovery:
    def test_init(self):
        disc = LANDiscovery("u1", "Alice", port=9000)
        assert disc.user_id == "u1"
        assert disc.user_name == "Alice"
        assert disc.port == 9000

    def test_set_project_title(self):
        disc = LANDiscovery("u1", "Alice")
        disc.set_project_title("My Script")
        assert disc._project_title == "My Script"

    def test_set_session_id(self):
        disc = LANDiscovery("u1", "Alice")
        disc.set_session_id("sess-123")
        assert disc._session_id == "sess-123"

    def test_make_announce(self):
        disc = LANDiscovery("u1", "Alice", port=8741)
        disc.set_project_title("Test Project")
        disc.set_session_id("sess-abc")
        data = json.loads(disc._make_announce().decode("utf-8"))
        assert data["service"] == SERVICE_ID
        assert data["user_id"] == "u1"
        assert data["user_name"] == "Alice"
        assert data["port"] == 8741
        assert data["project_title"] == "Test Project"
        assert data["session_id"] == "sess-abc"

    def test_get_peers_empty(self):
        disc = LANDiscovery("u1", "Alice")
        assert disc.get_peers() == []

    def test_get_peers_prunes_stale(self):
        disc = LANDiscovery("u1", "Alice")
        disc._peers["old"] = LANPeer(
            user_id="old", user_name="Old",
            ip_address="1.2.3.4", port=8741,
            last_seen=time.time() - 100,
        )
        peers = disc.get_peers()
        assert peers == []
        assert "old" not in disc._peers

    def test_stop_clears_peers(self):
        disc = LANDiscovery("u1", "Alice")
        disc._peers["p1"] = LANPeer(
            user_id="p1", user_name="P",
            ip_address="1.2.3.4", port=8741,
            last_seen=time.time(),
        )
        disc.stop()
        assert disc._peers == {}
        assert disc._running is False

    def test_callbacks_set(self):
        disc = LANDiscovery("u1", "Alice")
        found_cb = MagicMock()
        lost_cb = MagicMock()
        disc.set_callbacks(on_peer_found=found_cb, on_peer_lost=lost_cb)
        assert disc._on_peer_found is found_cb
        assert disc._on_peer_lost is lost_cb

    def test_peer_lost_callback_on_stale(self):
        disc = LANDiscovery("u1", "Alice")
        lost_cb = MagicMock()
        disc.set_callbacks(on_peer_lost=lost_cb)
        disc._peers["stale"] = LANPeer(
            user_id="stale", user_name="S",
            ip_address="1.2.3.4", port=8741,
            last_seen=time.time() - 100,
        )
        disc.get_peers()
        lost_cb.assert_called_once_with("stale")


class TestConnectionToken:
    def test_encode_decode_roundtrip(self):
        token = ConnectionToken(
            host="192.168.1.5", port=8741,
            session_id="abc123", user_name="Bob",
            project_title="Screenplay",
        )
        encoded = token.encode()
        decoded = ConnectionToken.decode(encoded)
        assert decoded is not None
        assert decoded.host == "192.168.1.5"
        assert decoded.port == 8741
        assert decoded.session_id == "abc123"
        assert decoded.user_name == "Bob"
        assert decoded.project_title == "Screenplay"

    def test_decode_invalid_token(self):
        assert ConnectionToken.decode("not-valid-base64!!!") is None

    def test_decode_empty(self):
        assert ConnectionToken.decode("") is None

    def test_created_at_auto_set(self):
        token = ConnectionToken(host="h", port=1, session_id="s", user_name="u")
        assert token.created_at > 0


class TestP2PConnection:
    def test_init(self):
        p2p = P2PConnection("u1", "Alice")
        assert p2p.user_id == "u1"
        assert p2p.user_name == "Alice"
        assert p2p._port == 0
        assert not p2p._running

    def test_not_connected_initially(self):
        p2p = P2PConnection("u1", "Alice")
        assert not p2p.is_connected()
        assert p2p.get_peer_count() == 0
        assert p2p.get_client_ids() == []

    def test_send_no_peer(self):
        p2p = P2PConnection("u1", "Alice")
        assert p2p.send("nobody", "hello") is False

    def test_set_callbacks(self):
        p2p = P2PConnection("u1", "Alice")
        on_msg = MagicMock()
        on_conn = MagicMock()
        on_disc = MagicMock()
        p2p.set_callbacks(on_message=on_msg, on_connect=on_conn, on_disconnect=on_disc)
        assert p2p._on_message is on_msg
        assert p2p._on_connect is on_conn
        assert p2p._on_disconnect is on_disc

    def test_close_when_not_running(self):
        p2p = P2PConnection("u1", "Alice")
        p2p.close()
        assert not p2p._running

    def test_host_and_close(self):
        p2p = P2PConnection("u1", "Alice")
        token = p2p.host_session(port=0, project_title="Test")
        assert p2p._running
        assert p2p._port > 0
        assert token.port == p2p._port
        assert token.project_title == "Test"
        assert len(p2p._session_id) > 0
        p2p.close()
        assert not p2p._running

    def test_host_creates_valid_token(self):
        p2p = P2PConnection("u1", "Alice")
        token = p2p.host_session()
        encoded = token.encode()
        decoded = ConnectionToken.decode(encoded)
        assert decoded is not None
        assert decoded.port == p2p._port
        p2p.close()

    def test_broadcast_empty(self):
        p2p = P2PConnection("u1", "Alice")
        p2p.broadcast("hello")

    def test_join_refused(self):
        p2p = P2PConnection("u1", "Alice")
        token = ConnectionToken(
            host="127.0.0.1", port=1,
            session_id="nope", user_name="Host",
        )
        assert p2p.join_session(token) is False
