import unittest
from unittest.mock import patch
from escape_room.llm import ModelError
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


@patch.dict('os.environ', {'GITHUB_LOG_TOKEN': ''})
class AppTests(unittest.TestCase):
    def test_complete_offline_game_restart_and_version_isolation(self):
        app = AppTest.from_file(APP).run()
        self.assertFalse(app.exception)
        for command in ['examine desk', 'solve desk book', 'take key', 'open drawer',
                        'examine drawer', 'examine bookshelf', 'examine painting', 'unlock door 8426']:
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

    def test_session_log_explains_drawer_rejection_without_chat_or_key(self):
        app = AppTest.from_file(APP).run()
        app.chat_input[0].set_value('drawer').run()
        self.assertFalse(app.exception)
        event = app.session_state['diagnostic_events'][-1]
        self.assertNotIn('target', event)
        self.assertNotIn('action_kind', event)
        self.assertEqual(event['outcome'], 'rejected')
        self.assertNotIn('content', event)
        self.assertNotIn('api_key', event)


    def test_existing_session_gets_new_log_defaults(self):
        app = AppTest.from_file(APP)
        app.session_state['diagnostic_events'] = []
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['pending_github_logs'], [])

    @patch('escape_room.github_logs.ensure_log_branch')
    @patch('escape_room.github_logs.save_log', return_value='saved-sha')
    def test_automatic_log_saving_and_retry_never_break_game(self, save, branch):
        with patch.dict('os.environ', {'GITHUB_LOG_TOKEN':'private-test-token'}):
            app = AppTest.from_file(APP).run()
            app.chat_input[0].set_value('drawer').run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['pending_github_logs'], [])
            self.assertEqual(save.call_args[0][0], 'private-test-token')
            self.assertNotIn('private-test-token', str(save.call_args[0][2]))
            from escape_room.github_logs import LogSaveError
            save.side_effect = LogSaveError('GitHub log save failed (HTTP 403).')
            app.chat_input[0].set_value('desk').run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.session_state['pending_github_logs']), 1)
            self.assertIn('desk', app.session_state['games']['v2']['state']['discovered'])
            save.side_effect = None
            app.button(key='retry_log_upload').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['pending_github_logs'], [])

    def test_notebook_displays_earned_clues_and_clears_on_restart(self):
        from escape_room.engine import ROOM
        app = AppTest.from_file(APP).run()
        self.assertEqual(app.metric[0].value, '0/4')
        app.chat_input[0].set_value('desk').run()
        app.chat_input[0].set_value('painting').run()
        self.assertFalse(app.exception)
        notebook = next(e for e in app.expander if e.label == 'Clue notebook')
        text = ' '.join(m.value for m in notebook.markdown)
        self.assertIn(ROOM['clues']['desk']['text'], text)
        self.assertIn(ROOM['clues']['painting']['text'], text)
        self.assertNotIn(ROOM['clues']['drawer']['text'], text)
        self.assertEqual(app.metric[0].value, '2/4')
        app.sidebar.button(key='restart_game').click().run()
        notebook = next(e for e in app.expander if e.label == 'Clue notebook')
        text = ' '.join(m.value for m in notebook.markdown)
        self.assertNotIn(ROOM['clues']['desk']['text'], text)
        self.assertEqual(app.metric[0].value, '0/4')

    def test_legacy_gameplay_log_fields_are_removed_on_rerun(self):
        from escape_room.diagnostics import record_event
        events=[]
        entry=record_event(events,'turn',version='v2',mode='offline',outcome='success')
        old=dict(entry,target='drawer',action_kind='examine',clue='private clue')
        app=AppTest.from_file(APP)
        app.session_state['diagnostic_events']=[old]
        app.session_state['pending_github_logs']=[{'filename':'session-'+'a'*32+'.json','entry':old}]
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['diagnostic_events'],[entry])
        self.assertEqual(app.session_state['pending_github_logs'][0]['entry'],entry)
        app.chat_input[0].set_value('desk').run()
        app.chat_input[0].set_value('book').run()
        self.assertTrue(app.session_state['games']['v2']['state']['key_available'])
