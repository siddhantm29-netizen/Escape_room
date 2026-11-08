"""Small Gemini REST client; API credentials never enter a URL or prompt."""
import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_MODEL = 'gemini-3.5-flash-lite'


class ModelError(Exception):
    pass


class Gemini:
    def __init__(self, api_key, model):
        if not re.fullmatch(r'[a-zA-Z0-9._-]{1,100}', model):
            raise ModelError('Use a model ID such as gemini-3.5-flash-lite.')
        self.api_key = api_key
        self.model = model

    def generate(self, system, messages, json_mode=False):
        config = {'temperature': 0.2, 'maxOutputTokens': 1024}
        if json_mode:
            config['responseMimeType'] = 'application/json'
        payload = {'systemInstruction': {'parts': [{'text': system}]},
                   'contents': [{'role': 'model' if m['role'] == 'assistant' else 'user',
                                 'parts': [{'text': m['content']}]} for m in messages],
                   'generationConfig': config}
        request = Request(
            f'https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent',
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json', 'x-goog-api-key': self.api_key},
            method='POST')
        try:
            with urlopen(request, timeout=25) as response:
                data = json.loads(response.read(200_000))
            candidate = data['candidates'][0]
            if candidate.get('finishReason') != 'STOP':
                raise ModelError('The model did not finish its answer. Try a shorter action.')
            text = ''.join(p.get('text', '') for p in candidate['content']['parts']
                           if not p.get('thought'))
            if not text.strip():
                raise ModelError('The model returned no answer. Try again.')
            return text
        except HTTPError as error:
            reason = ''
            try:
                body = error.read(20_000) if error.fp is not None else b'{}'
                details = json.loads(body).get('error', {}).get('details', [])
                if any(isinstance(d, dict) and d.get('reason') == 'API_KEY_INVALID' for d in details):
                    reason = 'The API key is invalid. Create or copy a Gemini API key in AI Studio.'
            except (ValueError, AttributeError, TypeError, OSError):
                pass
            messages = {400: 'The model rejected this request. Check the model ID.',
                        401: 'The API key was not accepted.', 403: 'The API key lacks access.',
                        404: 'This model was not found. Check the model ID in AI Studio.',
                        429: 'The free quota or rate limit was reached. Wait or use offline demo.',
                        500: 'Google reported an internal error. Retry shortly.',
                        502: 'The API gateway could not reach Gemini. Retry shortly.',
                        503: 'Gemini is overloaded or temporarily unavailable. Retry shortly.',
                        504: 'The Gemini request timed out upstream. Retry shortly.'}
            raise ModelError(f'Gemini HTTP {error.code}: ' + (reason or messages.get(error.code, 'Unexpected API response. Check model access in AI Studio.'))) from None
        except (URLError, TimeoutError, OSError):
            raise ModelError('Could not reach Gemini. Check your connection or use offline demo.') from None
        except (ValueError, KeyError, IndexError, TypeError):
            raise ModelError('Gemini returned an unreadable or blocked answer. Try again.') from None
