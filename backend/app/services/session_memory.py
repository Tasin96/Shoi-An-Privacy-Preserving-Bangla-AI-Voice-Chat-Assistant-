import time
from typing import List, Dict, Optional
from app.schemas.chat import ChatMessage

class SessionMemory:
    """
    In-memory, zero-PII session conversation buffer for multi-turn voice chat.
    Stores only the last few turns (max 4) per anonymous session in RAM.
    Entries expire automatically after 30 minutes of inactivity.
    Never persists to disk or databases to maintain strict privacy.
    """
    def __init__(self, max_turns: int = 4, ttl_seconds: int = 1800):
        self.max_turns = max_turns
        self.ttl_seconds = ttl_seconds
        self._sessions: Dict[str, Dict] = {}

    def get_history(self, session_id: str) -> List[ChatMessage]:
        if not session_id or session_id not in self._sessions:
            return []
        
        session = self._sessions[session_id]
        if time.time() - session["last_active"] > self.ttl_seconds:
            del self._sessions[session_id]
            return []
        
        session["last_active"] = time.time()
        return session["messages"]

    def add_turn(self, session_id: str, user_text: str, reply_text: str):
        if not session_id:
            return
        
        # Cleanup expired sessions periodically
        now = time.time()
        expired = [sid for sid, data in self._sessions.items() if now - data["last_active"] > self.ttl_seconds]
        for sid in expired:
            self._sessions.pop(sid, None)

        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "last_active": now,
                "messages": []
            }
        
        session = self._sessions[session_id]
        session["last_active"] = now
        session["messages"].append(ChatMessage(role="user", content=user_text))
        session["messages"].append(ChatMessage(role="assistant", content=reply_text))

        # Keep only the last max_turns (each turn is 2 messages: user + assistant)
        max_messages = self.max_turns * 2
        if len(session["messages"]) > max_messages:
            session["messages"] = session["messages"][-max_messages:]

session_memory = SessionMemory()
