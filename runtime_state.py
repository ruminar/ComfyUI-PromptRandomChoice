from __future__ import annotations

from dataclasses import asdict, dataclass
from threading import RLock
from time import time
from typing import Optional


MAX_RUNTIME_TEXT_BYTES = 512 * 1024
VALID_STATUSES = frozenset({"valid", "incomplete", "hard_error"})


class StaleRuntimeCandidateUpdate(ValueError):
    """Raised when one browser session sends an obsolete update."""


@dataclass(frozen=True)
class RuntimeCandidateState:
    state_key: str
    node_kind: str
    input_text: str
    input_status: str
    error: str
    accepted_text: Optional[str]
    revision: int
    client_id: str
    client_sequence: int
    updated_at: float

    def to_dict(self) -> dict:
        data = asdict(self)
        data.pop("client_id", None)
        data.pop("client_sequence", None)
        return data


class RuntimeCandidateStateStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._states: dict[str, RuntimeCandidateState] = {}
        self._client_updates: dict[tuple[str, str], tuple[int, str, str]] = {}

    @staticmethod
    def _validate(
        *,
        state_key: str,
        node_kind: str,
        text: str,
        input_status: str,
        error: str,
        client_id: str,
        client_sequence: int,
    ) -> tuple[str, str, str, str, str, str, int]:
        if not isinstance(state_key, str):
            raise TypeError("state_key must be a string")
        key = state_key.strip()
        if not key:
            raise ValueError("state_key must not be empty")
        if len(key) > 256:
            raise ValueError("state_key must be at most 256 characters")

        if node_kind not in {"flat", "ex"}:
            raise ValueError("node_kind must be 'flat' or 'ex'")
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if len(text.encode("utf-8")) > MAX_RUNTIME_TEXT_BYTES:
            raise ValueError(
                f"text must be at most {MAX_RUNTIME_TEXT_BYTES} UTF-8 bytes"
            )
        if input_status not in VALID_STATUSES:
            raise ValueError("input_status is invalid")
        if not isinstance(error, str):
            raise TypeError("error must be a string")
        message = error.strip()
        if input_status == "valid" and message:
            raise ValueError("valid input must not include an error")
        if input_status != "valid" and not message:
            raise ValueError("invalid input must include an error")

        if not isinstance(client_id, str):
            raise TypeError("client_id must be a string")
        session = client_id.strip()
        if not session:
            raise ValueError("client_id must not be empty")
        if len(session) > 128:
            raise ValueError("client_id must be at most 128 characters")
        if isinstance(client_sequence, bool) or not isinstance(client_sequence, int):
            raise TypeError("client_sequence must be an integer")
        if client_sequence < 0:
            raise ValueError("client_sequence must not be negative")

        return key, node_kind, text, input_status, message, session, client_sequence

    def update(
        self,
        *,
        state_key: str,
        node_kind: str,
        text: str,
        input_status: str,
        error: str,
        client_id: str,
        client_sequence: int,
    ) -> RuntimeCandidateState:
        key, kind, value, status, message, session, sequence = self._validate(
            state_key=state_key,
            node_kind=node_kind,
            text=text,
            input_status=input_status,
            error=error,
            client_id=client_id,
            client_sequence=client_sequence,
        )

        signature = (value, kind)
        with self._lock:
            previous = self._states.get(key)
            if previous is not None and previous.node_kind != kind:
                raise ValueError("state_key is already used by another Runtime node kind")

            previous_client_update = self._client_updates.get((key, session))
            if previous_client_update is not None:
                previous_sequence, previous_text, previous_kind = previous_client_update
                if sequence < previous_sequence:
                    raise StaleRuntimeCandidateUpdate(
                        "client_sequence is older than the accepted update"
                    )
                if sequence == previous_sequence:
                    if signature != (previous_text, previous_kind):
                        raise StaleRuntimeCandidateUpdate(
                            "client_sequence was already used for different text"
                        )
                    if (
                        previous is not None
                        and previous.client_id == session
                        and previous.input_text == value
                    ):
                        return previous
                    raise StaleRuntimeCandidateUpdate(
                        "update was already superseded by another client"
                    )

            accepted_text = previous.accepted_text if previous is not None else None
            revision = previous.revision if previous is not None else 0
            if status == "valid":
                if accepted_text != value:
                    accepted_text = value
                    revision += 1

            state = RuntimeCandidateState(
                state_key=key,
                node_kind=kind,
                input_text=value,
                input_status=status,
                error=message,
                accepted_text=accepted_text,
                revision=revision,
                client_id=session,
                client_sequence=sequence,
                updated_at=time(),
            )
            self._states[key] = state
            self._client_updates[(key, session)] = (sequence, value, kind)
            return state

    def get(self, state_key: str) -> Optional[RuntimeCandidateState]:
        if not isinstance(state_key, str):
            return None
        key = state_key.strip()
        if not key:
            return None
        with self._lock:
            return self._states.get(key)

    def clear(self, state_key: str) -> bool:
        if not isinstance(state_key, str):
            return False
        key = state_key.strip()
        if not key:
            return False
        with self._lock:
            removed = self._states.pop(key, None) is not None
            for client_key in [
                client_key
                for client_key in self._client_updates
                if client_key[0] == key
            ]:
                self._client_updates.pop(client_key, None)
            return removed


RUNTIME_CANDIDATE_STATE_STORE = RuntimeCandidateStateStore()
