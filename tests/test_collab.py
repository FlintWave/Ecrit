"""Tests for collaboration modules: protocol, CRDT, and session."""

import json
import pytest
from unittest.mock import MagicMock

from ecrit.collab.protocol import (
    CollabMessage, MessageType, Operation, OperationType,
)
from ecrit.collab.crdt import TextCRDT


class TestOperation:
    def test_to_dict_roundtrip(self):
        op = Operation(
            op_type=OperationType.INSERT, position=5, text="abc", user_id="u1",
        )
        d = op.to_dict()
        op2 = Operation.from_dict(d)
        assert op2.op_type == OperationType.INSERT
        assert op2.position == 5
        assert op2.text == "abc"
        assert op2.user_id == "u1"

    def test_delete_operation(self):
        op = Operation(op_type=OperationType.DELETE, position=3, length=4)
        d = op.to_dict()
        assert d["op_type"] == "delete"
        assert d["length"] == 4

    def test_retain_operation(self):
        op = Operation(op_type=OperationType.RETAIN, position=0, length=10)
        assert op.op_type == OperationType.RETAIN

    def test_timestamp_auto_set(self):
        op = Operation(op_type=OperationType.INSERT, position=0, text="x")
        assert op.timestamp > 0


class TestCollabMessage:
    def test_join_message(self):
        msg = CollabMessage.join("u1", "Alice")
        assert msg.msg_type == MessageType.JOIN
        assert msg.user_id == "u1"
        assert msg.user_name == "Alice"

    def test_leave_message(self):
        msg = CollabMessage.leave("u1")
        assert msg.msg_type == MessageType.LEAVE
        assert msg.user_id == "u1"

    def test_operation_message(self):
        op = Operation(op_type=OperationType.INSERT, position=0, text="hi")
        msg = CollabMessage.operation("u1", op)
        assert msg.msg_type == MessageType.OPERATION
        assert msg.payload["text"] == "hi"

    def test_cursor_update_message(self):
        msg = CollabMessage.cursor_update("u1", 42, 50)
        assert msg.msg_type == MessageType.CURSOR_UPDATE
        assert msg.payload["position"] == 42
        assert msg.payload["selection_end"] == 50

    def test_sync_request(self):
        msg = CollabMessage.sync_request("u1")
        assert msg.msg_type == MessageType.SYNC_REQUEST

    def test_sync_response(self):
        msg = CollabMessage.sync_response("u1", "hello world", 5)
        assert msg.msg_type == MessageType.SYNC_RESPONSE
        assert msg.payload["content"] == "hello world"
        assert msg.payload["revision"] == 5

    def test_json_roundtrip(self):
        msg = CollabMessage.join("u1", "Bob")
        raw = msg.to_json()
        msg2 = CollabMessage.from_json(raw)
        assert msg2.msg_type == MessageType.JOIN
        assert msg2.user_id == "u1"
        assert msg2.user_name == "Bob"

    def test_operation_json_roundtrip(self):
        op = Operation(op_type=OperationType.DELETE, position=3, length=2, user_id="u1")
        msg = CollabMessage.operation("u1", op)
        raw = msg.to_json()
        msg2 = CollabMessage.from_json(raw)
        op2 = Operation.from_dict(msg2.payload)
        assert op2.op_type == OperationType.DELETE
        assert op2.position == 3
        assert op2.length == 2


class TestTextCRDT:
    def test_set_and_get_text(self):
        crdt = TextCRDT(user_id="u1")
        crdt.set_text("hello")
        assert crdt.get_text() == "hello"

    def test_insert(self):
        crdt = TextCRDT(user_id="u1")
        crdt.set_text("hllo")
        crdt.insert(1, "e")
        assert crdt.get_text() == "hello"

    def test_delete(self):
        crdt = TextCRDT(user_id="u1")
        crdt.set_text("hello world")
        crdt.delete(5, 6)
        assert crdt.get_text() == "hello"

    def test_insert_at_start(self):
        crdt = TextCRDT(user_id="u1")
        crdt.set_text("world")
        crdt.insert(0, "hello ")
        assert crdt.get_text() == "hello world"

    def test_insert_at_end(self):
        crdt = TextCRDT(user_id="u1")
        crdt.set_text("hello")
        crdt.insert(5, " world")
        assert crdt.get_text() == "hello world"

    def test_revision_increments(self):
        crdt = TextCRDT(user_id="u1")
        assert crdt.revision == 0
        crdt.set_text("hello")
        assert crdt.revision == 1
        crdt.insert(5, "!")
        assert crdt.revision == 2
        crdt.delete(5, 1)
        assert crdt.revision == 3

    def test_apply_insert_operation(self):
        crdt = TextCRDT(user_id="u1")
        crdt.set_text("hllo")
        op = Operation(op_type=OperationType.INSERT, position=1, text="e", user_id="u2")
        crdt.apply_operation(op)
        assert crdt.get_text() == "hello"

    def test_apply_delete_operation(self):
        crdt = TextCRDT(user_id="u1")
        crdt.set_text("hello world")
        op = Operation(op_type=OperationType.DELETE, position=5, length=6, user_id="u2")
        crdt.apply_operation(op)
        assert crdt.get_text() == "hello"

    def test_transform_insert_after_insert(self):
        crdt = TextCRDT(user_id="u1")
        op1 = Operation(op_type=OperationType.INSERT, position=5, text="X")
        op2 = Operation(op_type=OperationType.INSERT, position=3, text="AB")
        transformed = crdt.transform(op1, op2)
        assert transformed.position == 7

    def test_transform_insert_before_insert(self):
        crdt = TextCRDT(user_id="u1")
        op1 = Operation(op_type=OperationType.INSERT, position=2, text="X")
        op2 = Operation(op_type=OperationType.INSERT, position=5, text="AB")
        transformed = crdt.transform(op1, op2)
        assert transformed.position == 2

    def test_transform_insert_after_delete(self):
        crdt = TextCRDT(user_id="u1")
        op1 = Operation(op_type=OperationType.INSERT, position=10, text="X")
        op2 = Operation(op_type=OperationType.DELETE, position=3, length=2)
        transformed = crdt.transform(op1, op2)
        assert transformed.position == 8

    def test_transform_insert_in_deleted_range(self):
        crdt = TextCRDT(user_id="u1")
        op1 = Operation(op_type=OperationType.INSERT, position=4, text="X")
        op2 = Operation(op_type=OperationType.DELETE, position=3, length=5)
        transformed = crdt.transform(op1, op2)
        assert transformed.position == 3

    def test_transform_preserves_other_fields(self):
        crdt = TextCRDT(user_id="u1")
        op1 = Operation(
            op_type=OperationType.INSERT, position=5, text="X",
            user_id="u2", revision=3,
        )
        op2 = Operation(op_type=OperationType.INSERT, position=3, text="AB")
        transformed = crdt.transform(op1, op2)
        assert transformed.user_id == "u2"
        assert transformed.text == "X"
        assert transformed.revision == 3

    def test_empty_text(self):
        crdt = TextCRDT(user_id="u1")
        assert crdt.get_text() == ""
        crdt.insert(0, "a")
        assert crdt.get_text() == "a"


class TestCollabSession:
    def test_session_creation(self):
        from ecrit.collab.session import CollabSession, SessionState
        session = CollabSession(user_name="TestUser")
        assert session.user_name == "TestUser"
        assert session.state == SessionState.DISCONNECTED
        assert len(session.user_id) == 8

    def test_get_participants_initially_empty(self):
        from ecrit.collab.session import CollabSession
        session = CollabSession()
        assert session.get_participants() == []

    def test_host_creates_participant(self):
        from ecrit.collab.session import CollabSession, CollabRole, SessionState
        session = CollabSession(user_name="Host")
        session._p2p.host_session = MagicMock(return_value=MagicMock())
        session._lan.set_project_title = MagicMock()
        session._lan.start = MagicMock()
        session.host("test content", project_title="Test")
        assert session.role == CollabRole.HOST
        assert session.state == SessionState.CONNECTED
        participants = session.get_participants()
        assert len(participants) == 1
        assert participants[0].user_name == "Host"

    def test_leave_clears_state(self):
        from ecrit.collab.session import CollabSession, SessionState
        session = CollabSession()
        session._p2p.host_session = MagicMock(return_value=MagicMock())
        session._lan.set_project_title = MagicMock()
        session._lan.start = MagicMock()
        session._p2p.broadcast = MagicMock()
        session._p2p.close = MagicMock()
        session._lan.stop = MagicMock()
        session.host("content")
        session.leave()
        assert session.state == SessionState.DISCONNECTED
        assert session.get_participants() == []

    def test_local_insert_broadcasts(self):
        from ecrit.collab.session import CollabSession
        session = CollabSession()
        session._crdt.set_text("hello")
        session._p2p.broadcast = MagicMock()
        session.apply_local_insert(5, " world")
        session._p2p.broadcast.assert_called_once()
        assert session._crdt.get_text() == "hello world"

    def test_update_cursor_broadcasts(self):
        from ecrit.collab.session import CollabSession
        session = CollabSession()
        session._participants[session.user_id] = MagicMock()
        session._p2p.broadcast = MagicMock()
        session.update_cursor(10, 20)
        session._p2p.broadcast.assert_called_once()

    def test_handle_join_message(self):
        from ecrit.collab.session import CollabSession
        session = CollabSession()
        msg = CollabMessage.join("peer1", "Peer")
        session._handle_message("peer1", msg.to_json())
        assert "peer1" in session._participants
        assert session._participants["peer1"].user_name == "Peer"

    def test_handle_leave_message(self):
        from ecrit.collab.session import CollabSession, Participant
        session = CollabSession()
        session._participants["peer1"] = Participant(user_id="peer1", user_name="Peer")
        msg = CollabMessage.leave("peer1")
        session._handle_message("peer1", msg.to_json())
        assert "peer1" not in session._participants

    def test_callbacks_fire(self):
        from ecrit.collab.session import CollabSession
        session = CollabSession()
        text_changes = []
        participant_changes = []
        session.set_callbacks(
            on_text_change=lambda t: text_changes.append(t),
            on_participant_change=lambda: participant_changes.append(True),
        )
        msg = CollabMessage.join("peer1", "Peer")
        session._handle_message("peer1", msg.to_json())
        assert len(participant_changes) == 1
