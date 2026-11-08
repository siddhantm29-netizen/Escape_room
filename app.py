"""Run with: streamlit run app.py"""
import os
from pathlib import Path
import streamlit as st
from escape_room.engine import ROOM, new_state, public_state
from escape_room.game import v1_turn, v2_turn
from escape_room.llm import Gemini, ModelError

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
                            help='Stored only in this session; never saved in project files.') if live else ''
    api_key = api_key or os.environ.get('GEMINI_API_KEY', '')
    model_id = st.text_input('Gemini model ID', value=os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash-lite')) if live else ''
    if live:
        st.caption('Your messages are sent to Google. Use an API key and model eligible for the free tier. No automatic paid fallback.')
        st.link_button('Get a key in Google AI Studio', 'https://aistudio.google.com/apikey')
    else:
        st.caption('Offline demo uses exact commands and authored responses. It makes no AI requests.')
    restart = st.button('Restart this version', use_container_width=True)
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
st.caption(f'{version}  •  ' + ('Gemini connected on request' if live else 'Offline demo'))

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
            model = Gemini(api_key, model_id)
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
st.caption('Built with Python, Streamlit and Gemini. Offline mode is a deterministic demonstration; live AI play requires your own API key.')
