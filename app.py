"""Run with: streamlit run app.py"""
import os
import streamlit as st
from escape_room.engine import ROOM, new_state, public_state
from escape_room.game import v1_turn, v2_turn
from escape_room.llm import Gemini, ModelError, DEFAULT_MODEL

st.set_page_config(page_title='The Last Library | AI Escape Room', page_icon='🗝️', layout='centered')
st.markdown('''<style>
:root { --ink: #29251f; --accent: #934c2e; }
h1 { font-family: Georgia, serif; letter-spacing: -0.035em; }
[data-testid="stChatMessage"] { border: 1px solid #d8d0c2; border-radius: 0.5rem; }
.stButton > button:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
</style>''', unsafe_allow_html=True)

with st.sidebar:
    st.caption('AI ESCAPE ROOM / COURSE PROJECT')
    version = st.radio('Game version', ['Version 2 · Validated', 'Version 1 · Conversational'])
    live = st.toggle('Use Gemini', value=False)
    api_key = st.text_input('Gemini API key', type='password',
                            key='gemini_api_key', max_chars=200, autocomplete='off',
                            help='Kept only in this session. Refresh or Clear API key to stop using it.') if live else ''
    api_key = api_key.strip()
    if live:
        st.button('Clear API key', key='clear_api_key',
                  on_click=lambda: st.session_state.update(gemini_api_key=''))
        st.caption('Your key is used only in this session. Refreshing starts without a key.')
    model_id = st.text_input('Gemini model ID', value=os.environ.get('GEMINI_MODEL', DEFAULT_MODEL)) if live else ''
    if live:
        st.caption('Your messages are sent to Google. Use an API key and model eligible for the free tier. No automatic paid fallback.')
        st.link_button('Get a key in Google AI Studio', 'https://aistudio.google.com/apikey')
        if st.button('Test Gemini connection', key='test_connection', disabled=not api_key):
            try:
                with st.spinner('Checking Gemini…'):
                    Gemini(api_key.strip(), model_id.strip()).generate(
                        'Reply with the word Connected.', [{'role': 'user', 'content': 'Connection check.'}])
                st.success('Gemini connection verified for this key and model.')
            except ModelError as error:
                st.error(str(error))
    else:
        st.caption('Offline demo uses exact commands and authored responses. It makes no AI requests.')
    restart = st.button('Restart this version', key='restart_game', use_container_width=True)
    with st.expander('How to play', expanded=True):
        st.write('Explore five objects, solve the desk riddle, collect what you find, and combine the clues to unlock the exit.')
        st.write('With Gemini, describe one action in your own words. For example: “Look closely at the writing desk.”')
        st.code('look\nexamine desk\nsolve desk YOUR_ANSWER\ntake key\nopen drawer\nexamine drawer\nexamine bookshelf\nexamine painting\nunlock door YOUR_CODE\ninventory\nhint', language=None)
    with st.expander('What changed in Version 2?'):
        st.write('Python owns inventory, locks and puzzle progress. Gemini proposes actions and chooses verified descriptions. Version 1 relies on conversation and the model’s judgment.')

is_v2 = version.startswith('Version 2')
slot = 'v2' if is_v2 else 'v1'
if 'games' not in st.session_state:
    st.session_state.games = {}
if restart or slot not in st.session_state.games:
    st.session_state.games[slot] = {'history': [], 'state': new_state(), 'escaped': False, 'warning': ''}
game = st.session_state.games[slot]

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
    st.progress(len(state['solved']) / 3, text='Desk riddle → drawer note → book numbers; inspect the painting for their order.')
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
    try:
        if live:
            model = Gemini(api_key, model_id.strip(), temperature=0.0 if is_v2 else 0.2)
        with st.spinner('The library stirs…'):
            if is_v2:
                reply, game['warning'] = v2_turn(game['state'], game['history'], prompt, model)
            else:
                reply, game['escaped'] = v1_turn(game['history'], prompt, model)
        game['history'].extend([{'role': 'user', 'content': prompt}, {'role': 'assistant', 'content': reply}])
    except ModelError as error:
        game['warning'] = str(error) + ' Your action was not recorded; try again.'
    st.rerun()

if is_v2:
    with st.expander('Session state · for the assignment demo'):
        st.json(public_state(game['state']))
st.divider()
st.caption('Built with Python, Streamlit and Gemini. Offline mode uses authored responses; AI mode requires your own API key.')
st.caption('Privacy & API use: Your key is held only in this session’s memory. This app does not save it to cookies, browser storage, files or a database, and does not share it with other players. Refreshing starts a new session without a key; Clear API key stops further requests with it. In AI mode, your messages and key are sent over HTTPS to Google to process the request. Google’s data terms, quota limits and any billing on your account apply. Do not enter sensitive personal information. Game progress is temporary and can reset when the session ends. Browser password managers are controlled by your browser, not this app.')
