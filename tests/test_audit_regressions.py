"""Reproductions found during the deployment-readiness audit."""
import json
import unittest
from copy import deepcopy
from io import BytesIO
from http.client import IncompleteRead
from unittest.mock import patch

from escape_room.engine import new_state
from escape_room.game import v2_turn
from escape_room.llm import Gemini, ModelError, DEFAULT_MODEL
from test_game import FakeModel


def ready_state():
    state = new_state()
    for command in ['examine desk', 'solve desk book', 'take key', 'open drawer',
                    'examine drawer', 'examine bookshelf', 'examine painting']:
        v2_turn(state, [], command)
    return state


class AuditRegressionTests(unittest.TestCase):
    @patch('escape_room.llm.urlopen')
    def test_malformed_provider_shapes_never_crash_page(self, request):
        bodies = [[], {'candidates': [None]}, {'candidates': [{'finishReason': 'STOP',
                   'content': {'parts': [None]}}]}, {'candidates': [{'finishReason': 'STOP',
                   'content': {'parts': [{'text': ['not', 'a', 'string']}]}}]}]
        for body in bodies:
            with self.subTest(body=body):
                request.return_value.__enter__.return_value = BytesIO(json.dumps(body).encode())
                with self.assertRaises(ModelError):
                    Gemini('test-key', DEFAULT_MODEL).generate('test', [{'role':'user','content':'test'}])

    @patch('escape_room.llm.urlopen')
    def test_interrupted_response_becomes_safe_error(self, request):
        request.return_value.__enter__.return_value.read.side_effect = IncompleteRead(b'partial')
        with self.assertRaises(ModelError):
            Gemini('test-key', DEFAULT_MODEL).generate('test', [{'role':'user','content':'test'}])

    def test_model_cannot_invent_code_in_open_door_action(self):
        state = ready_state()
        before = deepcopy(state)
        model = FakeModel('{"kind":"open","target":"door","value":"8426"}', '{"choice":0}')
        v2_turn(state, [], 'Open the door.', model)
        self.assertEqual(state, before)

    def test_correct_code_must_be_a_whole_value_in_message(self):
        for kind in ('open', 'unlock'):
            state = ready_state()
            model = FakeModel(json.dumps({'kind':kind,'target':'door','value':'8426'}), '{"choice":0}')
            v2_turn(state, [], 'Try the code 184260.', model)
            self.assertFalse(state['escaped'])

    def test_riddle_answer_must_be_a_whole_word(self):
        state = new_state()
        v2_turn(state, [], 'examine desk')
        model = FakeModel('{"kind":"solve","target":"desk","value":"book"}', '{"choice":0}')
        v2_turn(state, [], 'My answer is notebook.', model)
        self.assertNotIn('riddle', state['solved'])

    def test_non_string_action_kind_does_not_crash(self):
        state = new_state()
        for kind in ([], {}, None, 12):
            text, warning = v2_turn(state, [], 'look', FakeModel(json.dumps(
                {'kind':kind,'target':'','value':''}), '{"choice":0}'))
            self.assertEqual(state, new_state())

    def test_valid_code_with_punctuation_is_accepted(self):
        state = ready_state()
        model = FakeModel('{"kind":"unlock","target":"door","value":"8426"}', '{"choice":0}')
        v2_turn(state, [], 'Try "8426", please.', model)
        self.assertTrue(state['escaped'])
