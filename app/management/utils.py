from app.storage import persistent_storage as storage
from .models import SessionState
import logging
import json

def _session_to_dict(session: SessionState) -> dict:
    """Convert SessionState object to dictionary."""
    return {"id": session.id, "tokens_used": session.tokens_used}

def _dict_to_session(data: dict) -> SessionState:
    """Convert dictionary to SessionState object."""
    return SessionState(id=data["id"], tokens_used=data["tokens_used"])

def _create_session(session_id):
    session = SessionState(id=session_id, tokens_used=0)
    session_dict = _session_to_dict(session)
    storage.set(f"session_usage:{session_id}", json.dumps(session_dict))

def get_session_tokens_used(session_id):
    session_data = storage.get(f"session_usage:{session_id}")
    if session_data is None:
        _create_session(session_id)
        return 0
    session = _dict_to_session(json.loads(session_data))
    return session.tokens_used

def increment_session_tokens_used(session_id, tokens_used):
    session_data = storage.get(f"session_usage:{session_id}")
    if session_data is None:
        _create_session(session_id)
        session_data = storage.get(f"session_usage:{session_id}")
    session = _dict_to_session(json.loads(session_data))
    session.tokens_used += tokens_used

    logging.debug(f"increment_session_tokens_used: session_id={session_id}, tokens_used={session.tokens_used}")
    storage.set(f"session_usage:{session_id}", json.dumps(_session_to_dict(session)))
