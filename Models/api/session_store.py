"""Thread-safe in-memory store for active API sessions."""

import threading
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class APISession:
    session_id: str
    engine: Any          # NarrativeEngine instance
    conversation: Any    # ConversationSession instance
    node_id: str = "start"
    npc_file_paths: Dict[str, str] = field(default_factory=dict)  # npc_id → absolute path


class SessionStore:
    def __init__(self):
        self._sessions: Dict[str, APISession] = {}
        self._lock = threading.Lock()

    def create(self, engine: Any, conversation: Any) -> APISession:
        session_id = str(uuid.uuid4())
        api_session = APISession(
            session_id=session_id,
            engine=engine,
            conversation=conversation,
        )
        with self._lock:
            self._sessions[session_id] = api_session
        return api_session

    def get(self, session_id: str) -> Optional[APISession]:
        with self._lock:
            return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    def list_ids(self):
        with self._lock:
            return list(self._sessions.keys())


# Module-level singleton
store = SessionStore()
