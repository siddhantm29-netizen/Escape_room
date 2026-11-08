import json
import unittest
from unittest.mock import patch
from escape_room.diagnostics import record_event, sanitize_event, safe_for_upload
from escape_room.engine import new_state
from escape_room.game import v2_turn

EXPECTED = {'timestamp_utc','event','version','mode','outcome','elapsed_ms','stage','http_status'}


class LogPrivacyTests(unittest.TestCase):
    @patch('escape_room.diagnostics.logger.info')
    def test_only_core_diagnostics_can_be_recorded(self, log):
        events=[]
        entry=record_event(events,'turn',version='v2',mode='offline',outcome='rejected',stage='validation')
        self.assertEqual(set(entry),EXPECTED)
        self.assertNotIn('drawer', str(log.call_args))
        for forbidden in ('target','action_kind','clue','inventory','solved'):
            with self.assertRaises(TypeError):
                record_event(events,'turn',**{forbidden:'private game detail'})

    def test_old_logs_are_stripped_before_download_or_upload(self):
        events=[]
        entry=record_event(events,'turn',version='v2',mode='offline',outcome='success')
        legacy=dict(entry,target='drawer',action_kind='examine',clue='secret clue',inventory=['key'])
        self.assertFalse(safe_for_upload(legacy))
        clean=sanitize_event(legacy)
        self.assertEqual(clean,entry)
        self.assertEqual(set(clean),EXPECTED)
        self.assertTrue(safe_for_upload(clean))

    def test_game_diagnostics_do_not_identify_objects_or_puzzles(self):
        state=new_state()
        for command in ('desk','solve desk book','take key','open drawer','drawer','bookshelf','painting'):
            diag={}
            v2_turn(state,[],command,diagnostics=diag)
            self.assertNotIn('action_kind',diag)
            self.assertNotIn('target',diag)
            self.assertNotIn('clue',diag)
            self.assertNotIn('book',json.dumps(diag))
