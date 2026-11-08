import unittest
from unittest.mock import patch
from escape_room.llm import ModelError
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


    @patch.dict('os.environ', {'GEMINI_API_KEY': ''})
    def test_whitespace_key_does_not_enable_live_requests(self):
        app = AppTest.from_file(APP).run()
        app.sidebar.toggle[0].set_value(True).run()
        app.sidebar.text_input[0].set_value('   ').run()
        self.assertTrue(app.chat_input[0].disabled)
        self.assertTrue(app.sidebar.button(key='test_connection').disabled)
        self.assertFalse(app.exception)

    @patch('escape_room.llm.Gemini.generate', return_value='The desk bears a riddle.')
    def test_live_v1_action_and_restart(self, generate):
        app = AppTest.from_file(APP).run()
        app.sidebar.radio[0].set_value('Version 1 · Conversational').run()
        app.sidebar.toggle[0].set_value(True).run()
        app.sidebar.text_input[0].set_value('test-key').run()
        app.chat_input[0].set_value('Examine the desk.').run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.session_state['games']['v1']['history']), 2)
        generate.side_effect = ModelError('Gemini HTTP 503: unavailable')
        app.chat_input[0].set_value('Look again.').run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.session_state['games']['v1']['history']), 2)
        self.assertIn('503', app.session_state['games']['v1']['warning'])
        app.sidebar.button(key='restart_game').click().run()
        self.assertEqual(app.session_state['games']['v1']['history'], [])
        self.assertEqual(app.session_state['games']['v1']['warning'], '')

    def test_live_v2_uses_zero_temperature(self):
        temperatures = []
        def respond(model, system, messages, json_mode=False):
            temperatures.append(model.temperature)
            if 'Translate' in system:
                return '{"kind":"examine","target":"desk","value":""}'
            return '{"choice":0}'
        with patch('escape_room.llm.Gemini.generate', new=respond):
            app = AppTest.from_file(APP).run()
            app.sidebar.toggle[0].set_value(True).run()
            app.sidebar.text_input[0].set_value('test-key').run()
            app.chat_input[0].set_value('Examine the desk.').run()
        self.assertFalse(app.exception)
        self.assertEqual(temperatures, [0.0, 0.0])
        self.assertIn('desk', app.session_state['games']['v2']['state']['discovered'])

    def test_visitors_have_independent_progress(self):
        first = AppTest.from_file(APP).run()
        first.chat_input[0].set_value('examine bookshelf').run()
        second = AppTest.from_file(APP).run()
        self.assertEqual(second.session_state['games']['v2']['state']['solved'], [])
        self.assertEqual(first.session_state['games']['v2']['state']['solved'], ['numbers'])

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'shared-key-must-not-be-used'})
    def test_fresh_session_cannot_reuse_a_shared_or_previous_key(self):
        first = AppTest.from_file(APP).run()
        first.sidebar.toggle[0].set_value(True).run()
        self.assertTrue(first.chat_input[0].disabled)
        first.sidebar.text_input(key='gemini_api_key').set_value('visitor-one-key').run()
        self.assertFalse(first.chat_input[0].disabled)
        fresh = AppTest.from_file(APP).run()
        fresh.sidebar.toggle[0].set_value(True).run()
        self.assertEqual(fresh.sidebar.text_input(key='gemini_api_key').value, '')
        self.assertTrue(fresh.chat_input[0].disabled)

    def test_clear_key_disables_ai_without_erasing_game_progress(self):
        app = AppTest.from_file(APP).run()
        app.chat_input[0].set_value('examine desk').run()
        app.sidebar.toggle[0].set_value(True).run()
        app.sidebar.text_input(key='gemini_api_key').set_value('test-key').run()
        app.sidebar.button(key='clear_api_key').click().run()
        self.assertEqual(app.sidebar.text_input(key='gemini_api_key').value, '')
        self.assertTrue(app.chat_input[0].disabled)
        self.assertIn('desk', app.session_state['games']['v2']['state']['discovered'])
