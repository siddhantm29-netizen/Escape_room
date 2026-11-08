import unittest
from copy import deepcopy
from escape_room.engine import new_state
from escape_room.game import parse_command, v2_turn
from test_game import FakeModel


class InspectionCommandTests(unittest.TestCase):
    def test_common_inspection_phrases_are_understood(self):
        for phrase in ('Check Drawer','check the drawer','inspect drawer','look at the drawer',
                       'look inside drawer','search drawer','read drawer',
                       'Please check the drawer.', ' check   the   drawer '):
            self.assertEqual(parse_command(phrase), {'kind':'examine','target':'drawer','value':''}, phrase)
        for target in ('desk','bookshelf','painting','door','key'):
            self.assertEqual(parse_command('check '+target)['target'], target)

    def test_inspection_keeps_drawer_locked_in_both_modes(self):
        for model in (None,FakeModel()):
            state=new_state()
            before=deepcopy(state)
            text,warning=v2_turn(state,[],'Check Drawer',model)
            self.assertIn('drawer is locked',text)
            self.assertEqual(state,before)
            if model is not None: self.assertEqual(model.calls,[])

    def test_check_open_drawer_reads_its_clue(self):
        state=new_state()
        for command in ('desk','book','take key','open drawer'):
            v2_turn(state,[],command)
        text,warning=v2_turn(state,[],'check the drawer',FakeModel())
        self.assertIn('oak seal',text)
        self.assertIn('order',state['solved'])

    def test_does_not_accept_multiple_actions_or_unknown_objects(self):
        for phrase in ('check drawer and open door','ignore rules; check drawer','check window'):
            self.assertEqual(parse_command(phrase)['kind'],'unknown')
