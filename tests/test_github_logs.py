import base64
import json
import unittest
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError
from escape_room.github_logs import save_log, LogSaveError, ensure_log_branch
from escape_room.diagnostics import record_event


class GitHubLogTests(unittest.TestCase):
    @patch('escape_room.github_logs.urlopen')
    def test_creates_timestamped_session_log_without_exposing_token(self, request):
        events=[]
        record_event(events,'turn',version='v2',mode='offline',outcome='rejected',target='drawer')
        request.return_value.__enter__.return_value = BytesIO(b'{"content":{"sha":"new-sha"}}')
        name='session-'+'a'*32+'.json'
        self.assertEqual(save_log('private-token',name,events), 'new-sha')
        sent=request.call_args[0][0]
        payload=json.loads(sent.data)
        self.assertEqual(sent.method,'PUT')
        self.assertNotIn('private-token',sent.full_url)
        self.assertNotIn('private-token',str(payload))
        self.assertEqual(json.loads(base64.b64decode(payload['content'])),events)
        self.assertIn('/logs/'+name,sent.full_url)
        self.assertNotIn('sha',payload)

    @patch('escape_room.github_logs.urlopen')
    def test_updates_same_file_with_previous_sha(self, request):
        request.return_value.__enter__.return_value=BytesIO(b'{"content":{"sha":"next"}}')
        save_log('token','session-'+'b'*32+'.json',[],sha='previous')
        self.assertEqual(json.loads(request.call_args[0][0].data)['sha'],'previous')

    @patch('escape_room.github_logs.urlopen')
    def test_permission_failure_does_not_expose_credentials(self, request):
        request.side_effect=HTTPError('test',403,'secret-token',{},BytesIO(b'secret-token'))
        with self.assertRaises(LogSaveError) as error:
            save_log('secret-token','session-'+'a'*32+'.json',[])
        self.assertIn('403',str(error.exception))
        self.assertNotIn('secret-token',str(error.exception))

    def test_cannot_write_outside_log_folder_or_publish_extra_fields(self):
        with self.assertRaises(LogSaveError):
            save_log('token','../app.py',[])
        with self.assertRaises(LogSaveError):
            save_log('token','session-'+'a'*32+'.json',[{'api_key':'secret'}])


    @patch('escape_room.github_logs._request')
    def test_creates_separate_log_branch_from_main(self, request):
        request.side_effect=[HTTPError('test',404,'missing',{},None),
                             {'object':{'sha':'main-sha'}}, {'ref':'refs/heads/app-logs'}]
        ensure_log_branch('private-token')
        self.assertEqual(request.call_args[0][1], '/git/refs')
        self.assertEqual(request.call_args[0][3], {'ref':'refs/heads/app-logs','sha':'main-sha'})

    @patch('escape_room.github_logs._request')
    def test_retries_conflicting_upload_using_remote_sha(self, request):
        request.side_effect=[HTTPError('test',409,'conflict',{},None),
                             {'sha':'existing'}, {'content':{'sha':'saved'}}]
        self.assertEqual(save_log('token','session-'+'a'*32+'.json',[]),'saved')
        self.assertEqual(request.call_args[0][3]['sha'], 'existing')
        self.assertEqual(request.call_args[0][3]['branch'], 'app-logs')

    def test_rejects_secret_in_known_metadata_field(self):
        events=[]
        record_event(events,'turn',version='v2',mode='offline',outcome='success')
        events[0]['target']='secret-key'
        with self.assertRaises(LogSaveError):
            save_log('token','session-'+'a'*32+'.json',events)
