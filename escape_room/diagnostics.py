"""Bounded, metadata-only diagnostics; never accept chat text or credentials."""
from datetime import datetime, timezone
import json
import logging
import re
from .engine import KINDS, ROOM

logger = logging.getLogger('escape_room.diagnostics')
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())


def http_status(error):
    match = re.search(r'\bHTTP ([1-5]\d{2})\b', str(error))
    return int(match[1]) if match else None


def record_event(events, event, *, version='', mode='', outcome='', elapsed_ms=0,
                 action_kind='', target='', stage='', http_status=None):
    def allowed(value, choices):
        return value if isinstance(value, str) and value in choices else 'unknown'
    entry = {
        'timestamp_utc': datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
        'event': allowed(event, {'turn','connection','restart','key_clear'}),
        'version': allowed(version, {'v1','v2'}),
        'mode': allowed(mode, {'ai','offline'}),
        'outcome': allowed(outcome, {'success','rejected','error','fallback','restarted','cleared'}),
        'elapsed_ms': max(0, int(elapsed_ms)) if type(elapsed_ms) in (int, float) else 0,
        'action_kind': allowed(action_kind, KINDS),
        'target': allowed(target, ROOM['objects'] + ['key']),
        'stage': allowed(stage, {'input','parser','validation','narrator','complete','connection','ui'}),
        'http_status': http_status if type(http_status) is int and 100 <= http_status <= 599 else None,
    }
    events.append(entry)
    del events[:-200]
    logger.info('app_diagnostic %s', json.dumps(entry, sort_keys=True))
    return entry


def safe_for_upload(entry):
    """Reject any export that does not consist solely of known metadata values."""
    choices = {
        'event': {'turn','connection','restart','key_clear','unknown'},
        'version': {'v1','v2','unknown'}, 'mode': {'ai','offline','unknown'},
        'outcome': {'success','rejected','error','fallback','restarted','cleared','unknown'},
        'action_kind': KINDS | {'unknown'}, 'target': set(ROOM['objects']) | {'key','unknown'},
        'stage': {'input','parser','validation','narrator','complete','connection','ui','unknown'},
    }
    if not isinstance(entry, dict) or set(entry) != set(choices) | {'timestamp_utc','elapsed_ms','http_status'}:
        return False
    if any(not isinstance(entry[k],str) or entry[k] not in options for k,options in choices.items()):
        return False
    try:
        if len(entry['timestamp_utc']) > 40 or datetime.fromisoformat(entry['timestamp_utc']).utcoffset() is None:
            return False
    except (ValueError,TypeError):
        return False
    status = entry['http_status']
    return (type(entry['elapsed_ms']) is int and 0 <= entry['elapsed_ms'] <= 1_000_000_000
            and (status is None or (type(status) is int and 100 <= status <= 599)))
