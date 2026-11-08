"""Native Streamlit presentation; game authority remains in the engine."""
from pathlib import Path
import streamlit as st
from .engine import ROOM, collected_clues

STYLE = Path(__file__).resolve().parents[1] / 'assets' / 'interface.css'


def apply_design():
    st.markdown('<style>' + STYLE.read_text() + '</style>', unsafe_allow_html=True)


def render_heading(live, is_v2):
    with st.container(key='room_heading'):
        st.title(ROOM['title'])
        st.write('Search the room, collect the evidence, and find your way out.')
        st.caption(('Validated game' if is_v2 else 'Conversational game')
                   + (' with Gemini.' if live else ' in offline demo mode.'))


def render_notebook(state):
    notes = collected_clues(state)
    with st.container(key='evidence_panel'):
        st.header('Evidence board')
        a,b,c = st.columns(3)
        a.metric('Clues recorded',f'{len(notes)}/{len(ROOM["clues"])}')
        b.metric('Inventory','Brass key' if 'key' in state['inventory'] else 'Empty')
        c.metric('Exit','Open' if state['escaped'] else 'Locked')
        st.progress(len(notes)/len(ROOM['clues']))
        with st.expander('Clue notebook',expanded=True):
            st.caption('Your evidence board. Notes stay in discovery order; you work out their connection.')
            if not notes:
                st.info('No clues collected yet. Inspect an object to start your notebook.')
            for note in notes:
                with st.container(key='clue_'+note['object']):
                    st.markdown('**'+note['object'].capitalize()+'**')
                    st.write(note['text'])


def render_conversation(game, escaped):
    with st.container(height=360,border=False,key='conversation',autoscroll=True):
        with st.chat_message('assistant',avatar=':material/menu_book:'):
            st.write(ROOM['intro'])
        for index,message in enumerate(game['history']):
            with st.container(key=f"message_{message['role']}_{index}"):
                avatar = ':material/person:' if message['role']=='user' else ':material/search:'
                with st.chat_message(message['role'],avatar=avatar):
                    st.write(message['content'])
        if game['warning']:
            st.warning(game['warning'])
        if escaped:
            st.success('You escaped the library! Restart this version to play again.')


def render_privacy(disclosure):
    with st.container(key='privacy_footer'):
        st.caption('Your key stays in this session. AI messages go to Google. Diagnostic logs exclude gameplay details.')
        with st.expander('Privacy and API use'):
            st.write(disclosure)
        st.caption('Built with Python, Streamlit and Gemini for the AI Escape Room assignment.')
