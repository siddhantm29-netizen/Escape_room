import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


class AppTests(unittest.TestCase):
    def test_complete_offline_game_restart_and_version_isolation(self):
        app = AppTest.from_file(APP).run()
        self.assertFalse(app.exception)
        for command in ['examine desk', 'solve desk book', 'take key', 'open drawer',
                        'examine drawer', 'examine bookshelf', 'examine painting', 'unlock door 7319']:
            app.chat_input[0].set_value(command).run()
            self.assertFalse(app.exception)
        self.assertTrue(app.session_state['games']['v2']['state']['escaped'])
        self.assertTrue(app.chat_input[0].disabled)
        app.sidebar.radio[0].set_value('Version 1 · Conversational').run()
        self.assertEqual(app.session_state['games']['v1']['history'], [])
        self.assertTrue(app.chat_input[0].disabled)
        app.sidebar.radio[0].set_value('Version 2 · Validated').run()
        self.assertTrue(app.session_state['games']['v2']['state']['escaped'])
        app.sidebar.button[0].click().run()
        self.assertFalse(app.session_state['games']['v2']['state']['escaped'])
        self.assertEqual(app.session_state['games']['v2']['history'], [])
        self.assertFalse(app.exception)

    def test_live_mode_without_key_disables_chat(self):
        app = AppTest.from_file(APP).run()
        app.sidebar.toggle[0].set_value(True).run()
        self.assertTrue(app.chat_input[0].disabled)
        self.assertFalse(app.exception)
