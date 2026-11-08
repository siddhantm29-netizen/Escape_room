"""Run with: streamlit run app.py"""
import os
import json
from time import perf_counter
from uuid import uuid4
import streamlit as st
from escape_room.engine import ROOM, new_state, public_state
from escape_room.game import v1_turn, v2_turn
from escape_room.llm import Gemini, ModelError, DEFAULT_MODEL
from escape_room.diagnostics import record_event as record_metadata, http_status
from escape_room.github_logs import ensure_log_branch, save_log, LogSaveError, LOG_BRANCH, REPOSITORY

st.set_page_config(page_title='The Last Library | AI Escape Room', page_icon='🗝️', layout='centered')
for name, default in {'diagnostic_events': [], 'pending_github_logs': [],
                      'diagnostic_session': uuid4().hex, 'diagnostic_sequence': 0,
                      'github_log_status': ''}.items():
    if name not in st.session_state:
        st.session_state[name] = default


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


st.markdown('''<style>
:root { --ink: #29251f; --accent: #934c2e; }
h1 { font-family: Georgia, serif; letter-spacing: -0.035em; }
[data-testid="stChatMessage"] { border: 1px solid #d8d0c2; border-radius: 0.5rem; }
.stButton > button:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
</style>''', unsafe_allow_html=True)

with st.sidebar:
    st.caption('AI ESCAPE ROOM / COURSE PROJECT')
    version = st.radio('Game version', ['Version 2 · Validated', 'Version 1 · Conversational'], key='game_version')
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
    with st.expander('How to play', expanded=True):
        st.write('Explore five objects, solve the desk riddle, collect what you find, and combine the clues to unlock the exit.')
        st.write('An object name on its own examines it. With Gemini, describe one action in your own words. For example: “Look closely at the writing desk.”')
        st.code('look\nexamine desk\nsolve desk YOUR_ANSWER\ntake key\nopen drawer\nunlock door YOUR_CODE\ninventory\nhint', language=None)
    with st.expander('What changed in Version 2?'):
        st.write('Python owns inventory, locks and puzzle progress. Gemini proposes actions and chooses verified descriptions. Version 1 relies on conversation and the model’s judgment.')

is_v2 = version.startswith('Version 2')
slot = 'v2' if is_v2 else 'v1'
if 'games' not in st.session_state:
    st.session_state.games = {}
if restart or slot not in st.session_state.games:
    st.session_state.games[slot] = {'history': [], 'state': new_state(), 'escaped': False, 'warning': ''}
game = st.session_state.games[slot]
if restart:
    record_event(st.session_state.diagnostic_events, 'restart', version=slot,
                 mode='ai' if live else 'offline', outcome='restarted', stage='ui')

st.caption('THE LAST LIBRARY / AN INTERACTIVE MYSTERY')
st.title('One room. A way out.')
st.write('Follow the clues through a forgotten library. Every discovery brings the exit closer.')
st.caption(f'{version}  •  ' + ('Gemini · live API' if live else 'Offline demo'))

if is_v2:
    state = game['state']
    a, b, c = st.columns(3)
    a.metric('Clues recorded', f'{len(state["solved"])}/3')
    b.metric('Inventory', 'Brass key' if 'key' in state['inventory'] else 'Empty')
    c.metric('Exit', 'Open' if state['escaped'] else 'Locked')
    st.progress(len(state['solved']) / 3, text='Record discoveries and compare the markings scattered around the room.')
    with st.expander('Your discoveries'):
        st.write(', '.join(state['discovered']) or 'Nothing examined yet.')
else:
    st.info('Version 1 lets the AI manage the story and remember progress through chat. Enable Gemini to play this baseline.')

with st.chat_message('assistant', avatar='🗝️'):
    st.write(ROOM['intro'])
for message in game['history']:
    with st.chat_message(message['role']):
        st.write(message['content'])
if game['warning']:
    st.warning(game['warning'])
escaped = game['state']['escaped'] if is_v2 else game['escaped']
if escaped:
    st.success('You escaped the library! Restart this version to play again.')
if live and not api_key:
    st.info('Enter your Gemini API key in the sidebar to start AI play.')
turn_limit = len(game['history']) >= 120
if turn_limit:
    st.info('This session has reached 60 turns. Restart to begin another game.')
prompt = st.chat_input('What do you investigate?', max_chars=1000,
                       disabled=escaped or turn_limit or (live and not api_key) or (not is_v2 and not live))
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
                reply, game['escaped'] = v1_turn(game['history'], prompt, model)
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
    st.caption('The latest 200 events from this browser session record action types, results, timing and API status codes. Share this log when reporting a bug. Cloud administrators can also see these metadata events in server logs.')
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
st.divider()
st.caption('Built with Python, Streamlit and Gemini. Offline mode uses authored responses; AI mode requires your own API key.')
st.caption('Privacy & API use: Your key is held only in this session’s memory. This app does not save it to cookies, browser storage, files or a database, and does not share it with other players. Refreshing starts a new session without a key; Clear API key stops further requests with it. In AI mode, your messages and key are sent over HTTPS to Google to process the request. Google’s data terms, quota limits and any billing on your account apply. Do not enter sensitive personal information. Game progress is temporary and can reset when the session ends. Diagnostic logs contain action metadata and error codes, never your key, chat text or puzzle answers. When automatic saving is configured, this metadata is saved to the public GitHub repository. Browser password managers are controlled by your browser, not this app.')
