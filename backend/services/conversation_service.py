from collections import defaultdict, deque
from threading import Lock

_history = defaultdict(lambda: deque(maxlen=20))
_lock = Lock()

def get_history(session_id: str):
    with _lock:
        return list(_history[session_id])

def add_history(session_id: str, item: dict):
    with _lock:
        _history[session_id].append(item)

def clear_history(session_id: str):
    with _lock:
        _history.pop(session_id, None)
