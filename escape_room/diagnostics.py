"""Bounded technical diagnostics, independent of all puzzle content."""
from datetime import datetime, timezone
import json
import logging
import re

logger = logging.getLogger('escape_room.diagnostics')
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())

CHOICES = {
    'event': {'turn','connection','restart','key_clear','unknown'},
    'version': {'v1','v2','unknown'}, 'mode': {'ai','offline','unknown'},
    'outcome': {'success','rejected','error','fallback','restarted','cleared','unknown'},
    'stage': {'input','parser','validation','narrator','complete','connection','ui','unknown'},
}
FIELDS = set(CHOICES) | {'timestamp_utc','elapsed_ms','http_status'}


def http_status(error):
    match = re.search(r'\bHTTP ([1-5]\d{2})\b', str(error))
    return int(match[1]) if match else None


def record_event(events, event, *, version='', mode='', outcome='', elapsed_ms=0,
                 stage='', http_status=None):
    values = dict(event=event,version=version,mode=mode,outcome=outcome,stage=stage)
    entry = {k: v if isinstance(v,str) and v in CHOICES[k] else 'unknown' for k,v in values.items()}
    entry.update(timestamp_utc=datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
                 elapsed_ms=max(0,int(elapsed_ms)) if type(elapsed_ms) in (int,float) else 0,
                 http_status=http_status if type(http_status) is int and 100 <= http_status <= 599 else None)
    events.append(entry)
    del events[:-200]
    logger.info('app_diagnostic %s',json.dumps(entry,sort_keys=True))
    return entry


def safe_for_upload(entry):
    if not isinstance(entry,dict) or set(entry) != FIELDS:
        return False
    if any(not isinstance(entry[k],str) or entry[k] not in options for k,options in CHOICES.items()):
        return False
    try:
        if len(entry['timestamp_utc']) > 40 or datetime.fromisoformat(entry['timestamp_utc']).utcoffset() is None:
            return False
    except (ValueError,TypeError):
        return False
    status=entry['http_status']
    return (type(entry['elapsed_ms']) is int and 0 <= entry['elapsed_ms'] <= 1_000_000_000
            and (status is None or (type(status) is int and 100 <= status <= 599)))


def sanitize_event(entry):
    """Strip obsolete gameplay fields from logs created before this privacy change."""
    if not isinstance(entry,dict):
        return None
    clean={k:v for k,v in entry.items() if k in FIELDS}
    return clean if safe_for_upload(clean) else None
