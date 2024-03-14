from .session_manager import session_manager
from app.storage import cache_storage

def get_session_details(session_id, skip_cache=False):
    cache_key = f"session_details:{session_id}"
    session = None
    if not skip_cache:
        session = cache_storage.get(cache_key)
    if session is None:
        session = session_manager.get_session(session_id)
        if not skip_cache:
            cache_storage.set(cache_key, session)

    return session
