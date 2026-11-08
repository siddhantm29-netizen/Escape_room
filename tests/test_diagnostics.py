import json
import unittest
from unittest.mock import patch
from escape_room.diagnostics import record_event
from escape_room.engine import new_state
from escape_room.game import v2_turn
from escape_room.llm import ModelError
from test_game import FakeModel


class DiagnosticsTests(unittest.TestCase):
    @patch('escape_room.diagnostics.logger.info')
    def test_records_safe_metadata_and_caps_session_log(self, log):
        events = []
        for _ in range(210):
            record_event(events, 'turn', version='v2', mode='offline', outcome='rejected',
                         elapsed_ms=12)
        self.assertEqual(len(events), 200)
        self.assertNotIn('target', events[-1])
        self.assertEqual(events[-1]['elapsed_ms'], 12)
        self.assertEqual(json.loads(log.call_args[0][1]), events[-1])

    @patch('escape_room.diagnostics.logger.info')
    def test_untrusted_fields_cannot_leak_keys_or_codes(self, log):
        events = []
        secret = 'secret-key-and-code-8426'
        record_event(events, 'turn', version=secret, mode=secret, outcome=secret,
                     stage=secret, http_status=secret)
        self.assertNotIn(secret, json.dumps(events))
        self.assertNotIn(secret, str(log.call_args))
        with self.assertRaises(TypeError):
            record_event(events, 'turn', api_key=secret)

    def test_game_diagnostics_track_rejection_and_shortcut(self):
        diag = {}
        v2_turn(new_state(), [], 'drawer', diagnostics=diag)
        self.assertEqual(diag['outcome'], 'rejected')
        self.assertNotIn('action_kind', diag)
        self.assertNotIn('target', diag)

    def test_api_failure_records_stage_and_status_without_message(self):
        diag = {}
        v2_turn(new_state(), [], 'look around', FakeModel(ModelError('Gemini HTTP 429: secret')), diagnostics=diag)
        self.assertEqual(diag['stage'], 'parser')
        self.assertEqual(diag['http_status'], 429)
        self.assertNotIn('secret', str(diag))
