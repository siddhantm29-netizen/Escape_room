import re
import unittest
from escape_room.engine import ROOM, new_state, apply_action, collected_clues, public_state
from escape_room.game import v1_turn


class RandomPuzzleTests(unittest.TestCase):
    def test_new_sessions_have_varied_solvable_codes_without_mutating_template(self):
        states = [new_state(randomize=True) for _ in range(30)]
        self.assertGreater(len({s['puzzle']['door_code'] for s in states}), 1)
        for state in states:
            room = state['puzzle']
            values = {c['symbol']: c['number'] for c in room['clues'].values()}
            self.assertEqual(room['door_code'], ''.join(values[s] for s in room['order']))
            for clue in room['clues'].values():
                self.assertEqual(re.findall(r'\b\d\b', clue['text']), [clue['number']])
            for kind, target, value in [('examine','desk',''), ('solve','desk','book'),
                    ('take','key',''), ('open','drawer',''), ('examine','drawer',''),
                    ('examine','bookshelf',''), ('examine','painting','')]:
                self.assertTrue(apply_action(state, dict(kind=kind,target=target,value=value))['ok'])
            notes = collected_clues(state)
            self.assertEqual(len(notes), 4)
            self.assertTrue(all(room['clues'][n['object']]['text'] in n['text'] for n in notes))
            self.assertNotIn('puzzle', public_state(state))
            self.assertTrue(apply_action(state, dict(kind='unlock',target='door',value=room['door_code']))['ok'])
        self.assertEqual(ROOM['door_code'], '8426')

    def test_v1_receives_the_session_configuration(self):
        room = new_state(randomize=True)['puzzle']
        class Model:
            def generate(self, system, history):
                self.system = system
                return 'Ready'
        model = Model()
        v1_turn([], 'look', model, room=room)
        self.assertIn(room['door_code'], model.system)
