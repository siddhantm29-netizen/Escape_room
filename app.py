"""Run with: streamlit run app.py"""
import os
import json
from time import perf_counter
from uuid import uuid4
import streamlit as st
from escape_room.engine import ROOM, new_state, public_state
from escape_room.interface import apply_design, render_heading, render_notebook, render_conversation, render_privacy
from escape_room.game import v1_turn, v2_turn
from escape_room.llm import Gemini, ModelError, DEFAULT_MODEL
from escape_room.diagnostics import record_event as record_metadata, http_status, sanitize_event
from escape_room.github_logs import ensure_log_branch, save_log, LogSaveError, LOG_BRANCH, REPOSITORY

st.set_page_config(page_title='The Last Library | AI Escape Room', page_icon=':material/key:', layout='wide')
for name, default in {'diagnostic_events': [], 'pending_github_logs': [],
                      'diagnostic_session': uuid4().hex, 'diagnostic_sequence': 0,
                      'github_log_status': '', 'pending_actions': []}.items():
    if name not in st.session_state:
        st.session_state[name] = default

# Clean earlier sessions before any display, export or queued upload.
st.session_state.diagnostic_events = [clean for entry in st.session_state.diagnostic_events
                                      if (clean := sanitize_event(entry)) is not None]
st.session_state.pending_github_logs = [dict(item, entry=clean)
    for item in st.session_state.pending_github_logs
    if (clean := sanitize_event(item.get('entry'))) is not None]


def github_log_token():
    token = os.environ.get('GITHUB_LOG_TOKEN')
    if token is None:
        try:
            token = st.secrets.get('GITHUB_LOG_TOKEN', '')
        except FileNotFoundError:
            return ''
    return token.strip() if isinstance(token, str) else ''


def sync_github_logs():
    token = github_log_token()
    if not token:
        st.session_state.github_log_status = 'Automatic saving is not configured; you can still download the log.'
        return
    try:
        if not st.session_state.get('github_log_branch_ready'):
            ensure_log_branch(token)
            st.session_state.github_log_branch_ready = True
        # Catch up after an outage without blocking the page on a large backlog.
        for pending in st.session_state.pending_github_logs[:3]:
            save_log(token, pending['filename'], [pending['entry']])
            st.session_state.pending_github_logs.pop(0)
        st.session_state.github_log_status = 'Saved to GitHub.'
        if st.session_state.pending_github_logs:
            st.session_state.github_log_status = 'Some events are waiting to upload. Use Retry log upload.'
    except LogSaveError as error:
        st.session_state.github_log_status = str(error)


def record_event(events, event, **fields):
    entry = record_metadata(events, event, **fields)
    st.session_state.diagnostic_sequence += 1
    filename = f"session-{st.session_state.diagnostic_session}-{st.session_state.diagnostic_sequence:06d}.json"
    st.session_state.pending_github_logs.append({'filename':filename, 'entry':entry})
    # Local metadata stays bounded if GitHub is unavailable for a long time.
    del st.session_state.pending_github_logs[:-200]
    sync_github_logs()
    return entry


def clear_api_key():
    st.session_state.gemini_api_key = ''
    record_event(st.session_state.diagnostic_events, 'key_clear',
                 version='v2' if st.session_state.get('game_version', '').startswith('Version 2') else 'v1',
                 mode='ai', outcome='cleared', stage='ui')


apply_design()


def queue_action(command, version):
    st.session_state.pending_actions.append({'command':command, 'version':version})


with st.sidebar:
    st.header('Game desk')
    version = st.radio('Game version', ['Version 2 · Validated', 'Version 1 · Conversational'], key='game_version', format_func=lambda value: value.replace(' · ', ': '))
    live = st.toggle('Use Gemini', value=False)
    api_key = st.text_input('Gemini API key', type='password',
                            key='gemini_api_key', max_chars=200, autocomplete='off',
                            help='Kept only in this session. Refresh or Clear API key to stop using it.') if live else ''
    api_key = api_key.strip()
    if live:
        st.button('Clear API key', key='clear_api_key',
                  on_click=clear_api_key)
        st.caption('Your key is used only in this session. Refreshing starts without a key.')
    model_id = st.text_input('Gemini model ID', value=os.environ.get('GEMINI_MODEL', DEFAULT_MODEL)) if live else ''
    if live:
        st.caption('Your messages are sent to Google. Use an API key and model eligible for the free tier. No automatic paid fallback.')
        st.link_button('Get a key in Google AI Studio', 'https://aistudio.google.com/apikey')
        if st.button('Test Gemini connection', key='test_connection', disabled=not api_key):
            started = perf_counter()
            try:
                with st.spinner('Checking Gemini…'):
                    Gemini(api_key.strip(), model_id.strip()).generate(
                        'Reply with the word Connected.', [{'role': 'user', 'content': 'Connection check.'}])
                record_event(st.session_state.diagnostic_events, 'connection',
                             version='v2' if version.startswith('Version 2') else 'v1', mode='ai',
                             outcome='success', stage='connection', elapsed_ms=(perf_counter()-started)*1000)
                st.success('Gemini connection verified for this key and model.')
            except ModelError as error:
                record_event(st.session_state.diagnostic_events, 'connection',
                             version='v2' if version.startswith('Version 2') else 'v1', mode='ai',
                             outcome='error', stage='connection', http_status=http_status(error),
                             elapsed_ms=(perf_counter()-started)*1000)
                st.error(str(error))
    else:
        st.caption('Offline demo uses exact commands and authored responses. It makes no AI requests.')
    restart = st.button('Restart this version', key='restart_game', use_container_width=True)
    with st.expander('How to play', expanded=False):
        st.write('Explore five objects, solve the desk riddle, collect what you find, and combine the clues to unlock the exit.')
        st.write('An object name on its own examines it. With Gemini, describe one action in your own words. For example: “Look closely at the writing desk.”')
        st.caption('After reading the desk riddle, you can type your answer directly. Four digits alone attempt the exit code.')
        st.code('look\nexamine desk\nsolve desk YOUR_ANSWER\ntake key\nopen drawer\nunlock door YOUR_CODE\ninventory\nhint', language=None)
    with st.expander('What changed in Version 2?'):
        st.write('Python owns inventory, locks and puzzle progress. Gemini proposes actions and chooses verified descriptions. Version 1 relies on conversation and the model’s judgment.')

is_v2 = version.startswith('Version 2')
slot = 'v2' if is_v2 else 'v1'
if 'games' not in st.session_state:
    st.session_state.games = {}
if restart or slot not in st.session_state.games:
    st.session_state.games[slot] = {'history': [], 'state': new_state(randomize=True), 'escaped': False, 'warning': ''}
game = st.session_state.games[slot]
if restart:
    st.session_state.pending_actions = []
    st.session_state.pop('quick_action',None)
    record_event(st.session_state.diagnostic_events, 'restart', version=slot,
                 mode='ai' if live else 'offline', outcome='restarted', stage='ui')

escaped = game['state']['escaped'] if is_v2 else game['escaped']
turn_limit = len(game['history']) >= 120
input_disabled = escaped or turn_limit or (live and not api_key) or (not is_v2 and not live)
render_heading(live,is_v2)
with st.container(key='play_layout'):
    investigation,evidence = st.columns([1.25,1],gap='large')
    with investigation:
        with st.container(key='investigation_panel'):
            st.header('Investigate the room')
            with st.container(horizontal=True,gap='small',key='object_actions'):
                for target in ROOM['objects']:
                    st.button(target.capitalize(), key='inspect_'+target, disabled=input_disabled,
                              on_click=queue_action,args=('check '+target,slot))
            render_conversation(game,escaped)
            if live and not api_key:
                st.info('Enter your Gemini API key in the sidebar to start AI play.')
            if turn_limit:
                st.info('This session has reached 60 turns. Restart to begin another game.')
            prompt = st.chat_input('What do you investigate?',max_chars=1000,disabled=input_disabled,key='player_message')
            st.caption('Type an action, or choose an object above to inspect it.')
            if is_v2 and game['state']['key_available'] and 'key' not in game['state']['inventory']:
                st.button('Collect brass key',key='collect_key',type='primary',disabled=input_disabled,
                          on_click=queue_action,args=('take key',slot))
            if is_v2 and game['state']['drawer_open'] and 'drawer' not in game['state']['discovered']:
                st.button('Read the drawer note',key='read_drawer_note',type='primary',disabled=input_disabled,
                          on_click=queue_action,args=('read note',slot))
    with evidence:
        if is_v2:
            render_notebook(game['state'])
        else:
            st.subheader('Follow the conversation')
            st.write('Version 1 keeps its clues and inventory in the AI conversation. Version 2 adds a validated clue notebook.')
            st.info('Enable Gemini in the sidebar to play Version 1.')
legacy_action = st.session_state.pop('quick_action',None)
if legacy_action:
    st.session_state.pending_actions.append(legacy_action)
if prompt and not input_disabled:
    st.session_state.pending_actions.append({'command':prompt,'version':slot})
st.session_state.pending_actions = [action for action in st.session_state.pending_actions
                                     if action['version']==slot and not input_disabled]
prompt = st.session_state.pending_actions.pop(0)['command'] if st.session_state.pending_actions else None

if prompt:
    model = None
    game['warning'] = ''
    started = perf_counter()
    diagnostics = {'outcome':'success', 'stage':'complete'}
    try:
        if live:
            model = Gemini(api_key, model_id.strip(), temperature=0.0 if is_v2 else 0.2)
        with st.spinner('The library stirs…'):
            if is_v2:
                reply, game['warning'] = v2_turn(game['state'], game['history'], prompt, model, diagnostics=diagnostics)
            else:
                reply, game['escaped'] = v1_turn(game['history'], prompt, model, room=game['state']['puzzle'])
        game['history'].extend([{'role': 'user', 'content': prompt}, {'role': 'assistant', 'content': reply}])
    except ModelError as error:
        diagnostics.update(outcome='error', stage='parser', http_status=http_status(error))
        game['warning'] = str(error) + ' Your action was not recorded; try again.'
    record_event(st.session_state.diagnostic_events, 'turn', version=slot,
                 mode='ai' if live else 'offline', elapsed_ms=(perf_counter()-started)*1000, **diagnostics)
    st.rerun()

if is_v2:
    with st.expander('Session state · for the assignment demo'):
        st.json(public_state(game['state']))
with st.expander('Diagnostic log (no chat text or API keys)'):
    st.caption('The latest 200 events from this browser session record technical results, processing stages, timing and API status codes only. Share this log when reporting a bug. Cloud administrators can also see these metadata events in server logs.')
    st.download_button('Download diagnostic log', data=json.dumps(st.session_state.diagnostic_events, indent=2),
                       file_name='escape-room-diagnostics.json', mime='application/json')
    st.caption(st.session_state.github_log_status or 'Automatic GitHub saving starts with the first event when configured.')
    st.link_button('View saved GitHub logs', f'https://github.com/{REPOSITORY}/tree/{LOG_BRANCH}/logs',
                   disabled=not st.session_state.get('github_log_branch_ready', False))
    if st.button('Retry log upload', key='retry_log_upload', disabled=not st.session_state.pending_github_logs):
        sync_github_logs()
        st.rerun()
    if st.session_state.diagnostic_events:
        st.json(st.session_state.diagnostic_events[-5:])

render_privacy('Privacy & API use: Your key is held only in this session’s memory. This app does not save it to cookies, browser storage, files or a database, and does not share it with other players. Refreshing starts a new session without a key; Clear API key stops further requests with it. In AI mode, your messages and key are sent over HTTPS to Google to process the request. Google’s data terms, quota limits and any billing on your account apply. Do not enter sensitive personal information. Game progress is temporary and can reset when the session ends. Diagnostic logs contain technical results, timing and error codes only. They exclude keys, chat, action types, selected objects, clues, inventory and puzzle progress. When automatic saving is configured, this metadata is saved to the public GitHub repository. Browser password managers are controlled by your browser, not this app.')
