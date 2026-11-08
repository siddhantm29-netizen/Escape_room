import unittest
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError
from escape_room.llm import Gemini, ModelError, DEFAULT_MODEL


class GeminiErrorTests(unittest.TestCase):
    def test_default_supports_new_projects(self):
        self.assertEqual(DEFAULT_MODEL, 'gemini-3.5-flash-lite')

    @patch('escape_room.llm.urlopen')
    def test_service_status_is_visible_without_raw_error_or_key(self, request):
        for status in (500, 502, 503, 504):
            request.side_effect = HTTPError('test', status, 'secret', {}, BytesIO(b'secret'))
            with self.assertRaises(ModelError) as caught:
                Gemini('secret', DEFAULT_MODEL).generate('test', [])
            self.assertIn(str(status), str(caught.exception))
            self.assertNotIn('secret', str(caught.exception))

    @patch('escape_room.llm.urlopen')
    def test_invalid_key_400_is_distinguished(self, request):
        body = b'{"error":{"details":[{"reason":"API_KEY_INVALID"}]}}'
        request.side_effect = HTTPError('test', 400, 'bad', {}, BytesIO(body))
        with self.assertRaises(ModelError) as caught:
            Gemini('secret', DEFAULT_MODEL).generate('test', [])
        self.assertIn('API key', str(caught.exception))
        self.assertIn('400', str(caught.exception))
