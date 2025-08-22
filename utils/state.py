import json, os, threading

_LOCK = threading.Lock()
_STATE_PATH = "state.json"

_DEFAULT = {
    "auto_enabled": False,
    "selected_symbol": "BTCUSDT",
    "selected_strategy": "sma_crossover",
    "scan_result": [],
}

def _read():
    if not os.path.exists(_STATE_PATH):
        return _DEFAULT.copy()
    with open(_STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_state():
    with _LOCK:
        s = _read()
    return s

def set_state(**kwargs):
    with _LOCK:
        s = _read()
        s.update(kwargs)
        with open(_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
    return s