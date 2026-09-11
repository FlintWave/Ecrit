"""Collaboration protocol — message types and operations for real-time editing."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class MessageType(str, Enum):
    JOIN = "join"
    LEAVE = "leave"
    OPERATION = "operation"
    SYNC_REQUEST = "sync_request"
    SYNC_RESPONSE = "sync_response"
    CURSOR_UPDATE = "cursor_update"
    PRESENCE = "presence"
    ACK = "ack"
    ERROR = "error"


class OperationType(str, Enum):
    INSERT = "insert"
    DELETE = "delete"
    RETAIN = "retain"


@dataclass
class Operation:
    op_type: OperationType
    position: int = 0
    text: str = ""
    length: int = 0
    user_id: str = ""
    timestamp: float = 0.0
    revision: int = 0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "op_type": self.op_type.value,
            "position": self.position,
            "text": self.text,
            "length": self.length,
            "user_id": self.user_id,
            "timestamp": self.timestamp,
            "revision": self.revision,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Operation:
        return cls(
            op_type=OperationType(data.get("op_type", "insert")),
            position=data.get("position", 0),
            text=data.get("text", ""),
            length=data.get("length", 0),
            user_id=data.get("user_id", ""),
            timestamp=data.get("timestamp", 0.0),
            revision=data.get("revision", 0),
        )


@dataclass
class CollabMessage:
    msg_type: MessageType
    user_id: str = ""
    user_name: str = ""
    payload: dict = field(default_factory=dict)
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    def to_json(self) -> str:
        return json.dumps({
            "msg_type": self.msg_type.value,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "payload": self.payload,
            "timestamp": self.timestamp,
        })

    @classmethod
    def from_json(cls, data: str) -> CollabMessage:
        d = json.loads(data)
        return cls(
            msg_type=MessageType(d.get("msg_type", "error")),
            user_id=d.get("user_id", ""),
            user_name=d.get("user_name", ""),
            payload=d.get("payload", {}),
            timestamp=d.get("timestamp", 0.0),
        )

    @classmethod
    def join(cls, user_id: str, user_name: str) -> CollabMessage:
        return cls(msg_type=MessageType.JOIN, user_id=user_id, user_name=user_name)

    @classmethod
    def leave(cls, user_id: str) -> CollabMessage:
        return cls(msg_type=MessageType.LEAVE, user_id=user_id)

    @classmethod
    def operation(cls, user_id: str, op: Operation) -> CollabMessage:
        return cls(
            msg_type=MessageType.OPERATION,
            user_id=user_id,
            payload=op.to_dict(),
        )

    @classmethod
    def cursor_update(cls, user_id: str, position: int, selection_end: int = -1) -> CollabMessage:
        return cls(
            msg_type=MessageType.CURSOR_UPDATE,
            user_id=user_id,
            payload={"position": position, "selection_end": selection_end},
        )

    @classmethod
    def sync_request(cls, user_id: str) -> CollabMessage:
        return cls(msg_type=MessageType.SYNC_REQUEST, user_id=user_id)

    @classmethod
    def sync_response(cls, user_id: str, content: str, revision: int) -> CollabMessage:
        return cls(
            msg_type=MessageType.SYNC_RESPONSE,
            user_id=user_id,
            payload={"content": content, "revision": revision},
        )
