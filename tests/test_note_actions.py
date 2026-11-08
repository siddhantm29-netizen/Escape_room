import unittest
from copy import deepcopy
from escape_room.engine import apply_action, collected_clues, new_state
from escape_room.game import parse_command, v2_turn
from test_game import FakeModel


class NoteActionTests(unittest.TestCase):
    def test_note_phrasings_map_to_drawer_examination(self):
        for prompt in ('open note','read note','read the note','examine note','note',
                       'Read the note inside the drawer.'):
            self.assertEqual(parse_command(prompt), {'kind':'examine','target':'drawer','value':''})

    def test_locked_drawer_blocks_all_note_shortcuts(self):
        for model in (None, FakeModel()):
            state=new_state()
            before=deepcopy(state)
            text,warning=v2_turn(state,[],'open note',model)
            self.assertIn('drawer is locked',text)
            self.assertEqual(state,before)
            self.assertEqual(collected_clues(state),[])

    def test_open_note_reveals_and_records_clue_in_both_modes(self):
        for model in (None, FakeModel()):
            state=new_state()
            for command in ('desk','book','take key','open drawer'):
                v2_turn(state,[],command)
            text,warning=v2_turn(state,[],'open note',model)
            self.assertIn('oak seal',text)
            self.assertIn('drawer',[n['object'] for n in collected_clues(state)])
            self.assertIn('order',state['solved'])
            if model is not None:
                self.assertEqual(model.calls,[])

    def test_model_note_target_cannot_bypass_lock(self):
        state=new_state()
        action={'kind':'open','target':'note','value':''}
        result=apply_action(state,action)
        self.assertIn('drawer is locked',result['options'][0])
        state['drawer_open']=True
        self.assertTrue(apply_action(state,action)['ok'])
