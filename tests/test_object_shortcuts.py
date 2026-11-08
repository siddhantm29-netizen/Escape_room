import unittest
from escape_room.engine import apply_action, new_state
from escape_room.game import parse_command, v2_turn
from test_game import FakeModel


class ObjectShortcutTests(unittest.TestCase):
    def test_bare_object_names_mean_examine(self):
        for text in ('drawer', 'the drawer', 'Drawer.', 'painting', 'desk', 'bookshelf', 'door', 'key'):
            self.assertEqual(parse_command(text)['kind'], 'examine', text)

    def test_locked_drawer_is_recognized_in_offline_and_ai_mode(self):
        for model in (None, FakeModel()):
            state = new_state()
            text, warning = v2_turn(state, [], 'drawer', model)
            self.assertIn('drawer is locked', text)
            self.assertNotIn('not available', text)
            self.assertFalse(state['drawer_open'])
            if model is not None:
                self.assertEqual(model.calls, [])

    def test_open_drawer_shorthand_reveals_its_clue(self):
        state = new_state()
        for command in ('examine desk','solve desk book','take key','open drawer'):
            v2_turn(state, [], command)
        text, warning = v2_turn(state, [], 'drawer', FakeModel())
        self.assertIn('oak seal', text)
        self.assertIn('order', state['solved'])

    def test_unknown_input_has_action_guidance_not_missing_object_claim(self):
        state = new_state()
        text = apply_action(state, {'kind':'unknown','target':'','value':''})['options'][0]
        self.assertIn('examine drawer', text)
        self.assertNotIn('That object is not available', text)
        self.assertEqual(parse_command('drawer and door')['kind'], 'unknown')
