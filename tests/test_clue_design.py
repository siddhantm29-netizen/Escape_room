import itertools
import re
import unittest
from escape_room.engine import ROOM, apply_action, new_state


def act(state, kind, target='', value=''):
    return apply_action(state, {'kind':kind,'target':target,'value':value})


class ClueDesignTests(unittest.TestCase):
    def test_digits_are_distributed_across_four_objects(self):
        state = new_state()
        act(state, 'examine', 'desk')
        act(state, 'solve', 'desk', 'book')
        act(state, 'take', 'key')
        act(state, 'open', 'drawer')
        found = []
        for target in ('desk','bookshelf','painting','drawer'):
            text = act(state,'examine',target)['options'][0]
            digits = re.findall(r'\b\d\b', text)
            self.assertEqual(len(digits),1, (target,text))
            self.assertNotIn(ROOM['door_code'],text)
            found += digits
        self.assertEqual(sorted(found),sorted(ROOM['door_code']))

    def test_order_constraints_have_one_solution(self):
        candidates = [p for p in itertools.permutations(('oak','sun','star','moon'))
                      if p[0]=='oak' and p[-1]=='moon' and p.index('sun')+1==p.index('star')]
        self.assertEqual(candidates,[tuple(ROOM['order'])])
        values = {c['symbol']:c['number'] for c in ROOM['clues'].values()}
        self.assertEqual(''.join(values[s] for s in candidates[0]), ROOM['door_code'])

    def test_hints_never_supply_digits_or_the_final_sequence(self):
        state = new_state()
        actions = [('examine','desk',''),('solve','desk','book'),('take','key',''),
                   ('open','drawer',''),('examine','drawer',''),
                   ('examine','bookshelf',''),('examine','painting','')]
        for action in [None]+actions:
            if action: act(state,*action)
            hint = act(state,'hint')['options'][0]
            self.assertFalse(re.search(r'\d',hint))
            self.assertNotIn(', '.join(ROOM['order']),hint)
            self.assertNotIn('something you might read',hint)

    def test_previous_code_does_not_work(self):
        state = new_state()
        for action in [('examine','desk',''),('solve','desk','book'),('take','key',''),
                       ('open','drawer',''),('examine','drawer',''),
                       ('examine','bookshelf',''),('examine','painting','')]:
            act(state,*action)
        self.assertFalse(act(state,'unlock','door','7319')['ok'])
        self.assertFalse(state['escaped'])
