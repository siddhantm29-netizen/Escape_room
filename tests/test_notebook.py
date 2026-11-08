import unittest
from copy import deepcopy
from escape_room.engine import ROOM, collected_clues, new_state
from escape_room.game import v2_turn


class ClueNotebookTests(unittest.TestCase):
    def test_new_session_has_no_clue_spoilers(self):
        state = new_state()
        before = deepcopy(state)
        self.assertEqual(collected_clues(state), [])
        self.assertEqual(state, before)

    def test_records_clues_once_in_discovery_order(self):
        state = new_state()
        for command in ('painting','desk','painting','bookshelf'):
            v2_turn(state,[],command)
        notes = collected_clues(state)
        self.assertEqual([note['object'] for note in notes], ['painting','desk','bookshelf'])
        self.assertIn(ROOM['riddle'], notes[1]['text'])
        for note in notes:
            self.assertIn(ROOM['clues'][note['object']]['text'], note['text'])
        self.assertNotIn(ROOM['door_code'],str(notes))

    def test_drawer_clue_requires_opening_and_examination(self):
        state = new_state()
        v2_turn(state, [], 'drawer')
        self.assertNotIn('drawer', [n['object'] for n in collected_clues(state)])
        for command in ('desk','solve desk book','take key','open drawer'):
            v2_turn(state,[],command)
        self.assertNotIn('drawer', [n['object'] for n in collected_clues(state)])
        v2_turn(state, [], 'drawer')
        self.assertIn('drawer', [n['object'] for n in collected_clues(state)])
        self.assertEqual(collected_clues(new_state()), [])
