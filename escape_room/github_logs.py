"""Write metadata-only logs to a dedicated branch, never the deployment branch."""
import base64
from http.client import HTTPException
import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from .diagnostics import safe_for_upload

REPOSITORY = 'siddhantm29-netizen/Escape_room'
LOG_BRANCH = 'app-logs'
BASE = f'https://api.github.com/repos/{REPOSITORY}'


class LogSaveError(Exception):
    pass


def _request(token, path, method='GET', payload=None):
    req = Request(BASE + path, method=method,
                  data=json.dumps(payload).encode() if payload is not None else None,
                  headers={'Authorization':'Bearer ' + token.strip(),
                           'Accept':'application/vnd.github+json','Content-Type':'application/json',
                           'User-Agent':'EscapeRoom-Diagnostics'})
    with urlopen(req, timeout=8) as response:
        return json.loads(response.read(250_000))


def ensure_log_branch(token):
    try:
        try:
            _request(token, f'/git/ref/heads/{LOG_BRANCH}')
            return
        except HTTPError as error:
            if error.code != 404:
                raise
        source = _request(token, '/git/ref/heads/main')['object']['sha']
        try:
            _request(token, '/git/refs', 'POST', {'ref':f'refs/heads/{LOG_BRANCH}','sha':source})
        except HTTPError as error:
            if error.code != 422:
                raise
            # Another visitor may have created the branch at the same time.
            _request(token, f'/git/ref/heads/{LOG_BRANCH}')
    except HTTPError as error:
        raise LogSaveError(f'GitHub log setup failed (HTTP {error.code}). Check the token and repository permissions.') from None
    except (URLError, OSError, HTTPException, ValueError, KeyError, TypeError):
        raise LogSaveError('GitHub log setup is unavailable. The session log is still downloadable.') from None


def save_log(token, filename, events, sha=None):
    if not re.fullmatch(r'session-[a-f0-9]{32}(?:-\d{6})?\.json', filename):
        raise LogSaveError('Invalid diagnostic filename.')
    if (not isinstance(events,list) or len(events)>200
            or any(not safe_for_upload(e) for e in events)):
        raise LogSaveError('Only the diagnostic metadata schema can be uploaded.')
    payload = {'message':'Save app diagnostic log [skip ci]', 'branch':LOG_BRANCH,
               'content':base64.b64encode(json.dumps(events,indent=2).encode()).decode()}
    if sha:
        payload['sha'] = sha
    path = '/contents/logs/' + filename
    try:
        try:
            data = _request(token,path,'PUT',payload)
        except HTTPError as error:
            if error.code not in (409,422):
                raise
            try:
                payload['sha'] = _request(token,path+f'?ref={LOG_BRANCH}')['sha']
            except HTTPError as read_error:
                if read_error.code != 404:
                    raise
                payload.pop('sha',None)
            data = _request(token,path,'PUT',payload)
        return data['content']['sha']
    except HTTPError as error:
        raise LogSaveError(f'GitHub log save failed (HTTP {error.code}). Check token permissions or rate limits.') from None
    except (URLError,OSError,HTTPException,ValueError,KeyError,TypeError):
        raise LogSaveError('GitHub log saving is unavailable. The session log is still downloadable.') from None
