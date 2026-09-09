"""Real-time collaboration — LAN discovery and P2P remote editing."""

from ecrit.collab.protocol import (
    CollabMessage, MessageType, Operation, OperationType,
)
from ecrit.collab.crdt import TextCRDT
from ecrit.collab.session import CollabSession, CollabRole, SessionState
from ecrit.collab.lan import LANDiscovery, LANPeer
from ecrit.collab.p2p import P2PConnection, ConnectionToken
