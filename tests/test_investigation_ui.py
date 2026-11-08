import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


@patch.dict('os.environ', {'GITHUB_LOG_TOKEN':''})
class InvestigationUITests(unittest.TestCase):
    def test_quick_inspection_records_one_action_and_earned_note(self):
        app=AppTest.from_file(APP).run()
        self.assertEqual(app.title[0].value,'The Last Library')
        app.button(key='inspect_desk').click().run()
        self.assertFalse(app.exception)
        self.assertIn('desk',app.session_state['games']['v2']['state']['discovered'])
        self.assertEqual(len(app.session_state['games']['v2']['history']),2)
        app.run()
        self.assertEqual(len(app.session_state['games']['v2']['history']),2)
        event=app.session_state['diagnostic_events'][-1]
        self.assertNotIn('target',event)
        self.assertNotIn('action_kind',event)

    def test_context_actions_use_existing_inventory_and_drawer_rules(self):
        app=AppTest.from_file(APP).run()
        app.button(key='inspect_drawer').click().run()
        self.assertFalse(app.session_state['games']['v2']['state']['drawer_open'])
        app.button(key='inspect_desk').click().run()
        app.chat_input[0].set_value('book').run()
        app.button(key='collect_key').click().run()
        self.assertEqual(app.session_state['games']['v2']['state']['inventory'],['key'])
        app.chat_input[0].set_value('open drawer').run()
        app.button(key='read_drawer_note').click().run()
        self.assertIn('drawer',app.session_state['games']['v2']['state']['discovered'])
        self.assertFalse(app.exception)

    def test_live_without_key_disables_quick_inspection(self):
        app=AppTest.from_file(APP).run()
        app.sidebar.toggle[0].set_value(True).run()
        self.assertTrue(app.chat_input[0].disabled)
        for name in ('desk','bookshelf','painting','drawer','door'):
            self.assertTrue(app.button(key='inspect_'+name).disabled)

    def test_quick_action_is_not_lost_when_chat_is_submitted_immediately(self):
        app=AppTest.from_file(APP).run()
        app.button(key='inspect_desk').click().run()
        app.chat_input[0].set_value('book').run()
        app.button(key='collect_key').click()
        app.chat_input[0].set_value('open drawer').run()
        self.assertFalse(app.exception)
        state=app.session_state['games']['v2']['state']
        self.assertEqual(state['inventory'],['key'])
        self.assertTrue(state['drawer_open'])
        commands=[m['content'] for m in app.session_state['games']['v2']['history'] if m['role']=='user']
        self.assertLess(commands.index('take key'),commands.index('open drawer'))
