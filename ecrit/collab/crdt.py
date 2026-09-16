"""Simple text CRDT for conflict-free collaborative editing."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from ecrit.collab.protocol import Operation, OperationType


@dataclass
class CharItem:
    char: str
    id: tuple[float, str]
    visible: bool = True


class TextCRDT:
    def __init__(self, user_id: str = ""):
        self.user_id = user_id
        self._items: list[CharItem] = []
        self._counter = 0
        self._revision = 0

    @property
    def revision(self) -> int:
        return self._revision

    def _next_id(self) -> tuple[float, str]:
        self._counter += 1
        return (time.time() + self._counter * 0.000001, self.user_id)

    def get_text(self) -> str:
        return "".join(item.char for item in self._items if item.visible)

    def set_text(self, text: str) -> None:
        self._items = []
        for ch in text:
            self._items.append(CharItem(char=ch, id=self._next_id()))
        self._revision += 1

    def _visible_index_to_real(self, visible_idx: int) -> int:
        count = 0
        for i, item in enumerate(self._items):
            if item.visible:
                if count == visible_idx:
                    return i
                count += 1
        return len(self._items)

    def apply_operation(self, op: Operation) -> str:
        if op.op_type == OperationType.INSERT:
            real_pos = self._visible_index_to_real(op.position)
            new_items = []
            for ch in op.text:
                new_items.append(CharItem(char=ch, id=self._next_id()))
            self._items[real_pos:real_pos] = new_items
            self._revision += 1
        elif op.op_type == OperationType.DELETE:
            start = self._visible_index_to_real(op.position)
            deleted = 0
            for i in range(start, len(self._items)):
                if deleted >= op.length:
                    break
                if self._items[i].visible:
                    self._items[i].visible = False
                    deleted += 1
            self._revision += 1

        return self.get_text()

    def insert(self, position: int, text: str) -> Operation:
        op = Operation(
            op_type=OperationType.INSERT,
            position=position,
            text=text,
            user_id=self.user_id,
            revision=self._revision,
        )
        self.apply_operation(op)
        return op

    def delete(self, position: int, length: int) -> Operation:
        op = Operation(
            op_type=OperationType.DELETE,
            position=position,
            length=length,
            user_id=self.user_id,
            revision=self._revision,
        )
        self.apply_operation(op)
        return op

    def transform(self, op1: Operation, op2: Operation) -> Operation:
        """Operational transform: adjust op1 against already-applied op2."""
        if op2.op_type == OperationType.INSERT:
            insert_len = len(op2.text)
            if op1.op_type == OperationType.DELETE and op1.position < op2.position < op1.position + op1.length:
                # op2 insert splits op1's delete range — expand length to skip inserted text
                return Operation(
                    op_type=op1.op_type,
                    position=op1.position,
                    text=op1.text,
                    length=op1.length + insert_len,
                    user_id=op1.user_id,
                    timestamp=op1.timestamp,
                    revision=op1.revision,
                )
            if op1.position >= op2.position:
                return Operation(
                    op_type=op1.op_type,
                    position=op1.position + insert_len,
                    text=op1.text,
                    length=op1.length,
                    user_id=op1.user_id,
                    timestamp=op1.timestamp,
                    revision=op1.revision,
                )
        elif op2.op_type == OperationType.DELETE:
            op2_end = op2.position + op2.length
            if op1.position >= op2_end:
                # op1 is entirely after op2's deleted range
                return Operation(
                    op_type=op1.op_type,
                    position=op1.position - op2.length,
                    text=op1.text,
                    length=op1.length,
                    user_id=op1.user_id,
                    timestamp=op1.timestamp,
                    revision=op1.revision,
                )
            if op1.op_type == OperationType.DELETE:
                op1_end = op1.position + op1.length
                # Compute overlap between the two delete ranges
                overlap_start = max(op1.position, op2.position)
                overlap_end = min(op1_end, op2_end)
                overlap = max(0, overlap_end - overlap_start)
                new_length = op1.length - overlap
                if new_length <= 0:
                    # op1's delete is entirely subsumed by op2
                    return Operation(
                        op_type=op1.op_type,
                        position=max(op1.position, op2.position) - min(op1.position, op2.position)
                        if op1.position >= op2.position else op1.position,
                        text=op1.text,
                        length=0,
                        user_id=op1.user_id,
                        timestamp=op1.timestamp,
                        revision=op1.revision,
                    )
                new_pos = min(op1.position, op2.position) if op1.position < op2.position else op2.position
                return Operation(
                    op_type=op1.op_type,
                    position=new_pos,
                    text=op1.text,
                    length=new_length,
                    user_id=op1.user_id,
                    timestamp=op1.timestamp,
                    revision=op1.revision,
                )
            elif op1.position >= op2.position:
                # INSERT inside op2's deleted range — move to op2.position
                return Operation(
                    op_type=op1.op_type,
                    position=op2.position,
                    text=op1.text,
                    length=op1.length,
                    user_id=op1.user_id,
                    timestamp=op1.timestamp,
                    revision=op1.revision,
                )
        return op1
