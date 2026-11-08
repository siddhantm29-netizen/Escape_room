import unittest
from copy import deepcopy

from escape_room.engine import apply_action, new_state, public_state


def act(state, kind, target='', value=''):
    return apply_action(state, {'kind': kind, 'target': target, 'value': value})


class EngineTests(unittest.TestCase):
    def test_complete_solution(self):
        state = new_state()
        for action in [('examine', 'desk', ''), ('solve', 'desk', 'book'),
                       ('take', 'key', ''), ('open', 'drawer', ''),
                       ('examine', 'drawer', ''), ('examine', 'bookshelf', ''),
                       ('examine', 'painting', ''), ('unlock', 'door', '7319')]:
            result = act(state, *action)
            self.assertTrue(result['ok'], result)
        self.assertTrue(state['escaped'])
        self.assertEqual(len(state['solved']), 3)

    def test_missing_key_and_locked_drawer(self):
        state = new_state()
        for kind in ('open', 'examine'):
            before = deepcopy(state)
            self.assertFalse(act(state, kind, 'drawer')['ok'])
            self.assertEqual(state, before)
        self.assertFalse(act(state, 'use', 'key')['ok'])

    def test_correct_code_cannot_skip_puzzles(self):
        state = new_state()
        self.assertFalse(act(state, 'unlock', 'door', '7319')['ok'])
        self.assertFalse(state['escaped'])

    def test_wrong_code_does_not_change_state(self):
        state = new_state()
        before = deepcopy(state)
        self.assertFalse(act(state, 'unlock', 'door', '0000')['ok'])
        self.assertEqual(before, state)

    def test_unknown_or_malformed_actions_leave_state_unchanged(self):
        for action in [None, [], {'kind': 'admin'}, {'kind': 'open', 'target': 'window', 'value': ''},
                       {'kind': 'unlock', 'target': 'door', 'value': '7319', 'escaped': True},
                       {'kind': 'solve', 'target': 'desk', 'value': 42}]:
            state = new_state()
            before = deepcopy(state)
            self.assertFalse(apply_action(state, action)['ok'])
            self.assertEqual(state, before)

    def test_inventory_and_discoveries_are_idempotent(self):
        state = new_state()
        for _ in range(2):
            act(state, 'examine', 'desk')
            act(state, 'solve', 'desk', 'book')
            act(state, 'take', 'key')
            act(state, 'open', 'drawer')
            act(state, 'examine', 'drawer')
        self.assertEqual(state['inventory'], ['key'])
        self.assertEqual(state['solved'], ['riddle', 'order'])
        self.assertTrue(state['drawer_open'])

    def test_public_state_hides_unearned_information(self):
        state = new_state()
        text = str(public_state(state))
        self.assertNotIn('7319', text)
        self.assertNotIn('book', public_state(state).get('inventory', []))
        self.assertEqual(state, new_state())
        other = new_state()
        other['inventory'].append('key')
        self.assertEqual(state['inventory'], [])


if __name__ == '__main__':
    unittest.main()
