"""Only this module may change Version 2 game state."""
import json
from pathlib import Path

ROOM = json.loads(Path(__file__).with_name('room.json').read_text())
KINDS = {'look', 'examine', 'solve', 'take', 'open', 'use', 'unlock', 'inventory', 'hint', 'unknown'}


def new_state():
    return {'room': ROOM['title'], 'objects': list(ROOM['objects']), 'inventory': [],
            'discovered': [], 'solved': [], 'key_available': False,
            'drawer_open': False, 'door_open': False, 'escaped': False}


def public_state(state):
    return {k: state[k] for k in ('room', 'objects', 'inventory', 'discovered',
                                 'solved', 'drawer_open', 'door_open', 'escaped')}


def result(ok, text):
    # Both variants carry the same validated facts. The model can choose tone only.
    return {'ok': ok, 'options': [text, 'In the quiet library, you pause. ' + text]}


def apply_action(state, action):
    if (not isinstance(action, dict) or set(action) != {'kind', 'target', 'value'}
            or any(not isinstance(v, str) or len(v) > 200 for v in action.values())
            or action['kind'] not in KINDS):
        return result(False, 'That action could not be understood. Try one action at a time.')
    kind, target, value = (action[k].strip().lower() for k in ('kind', 'target', 'value'))
    if state['escaped']:
        return result(True, 'You have already escaped. Restart to play again.')
    if kind == 'look':
        return result(True, ROOM['intro'])
    if kind == 'inventory':
        return result(True, 'You carry: ' + (', '.join(state['inventory']) or 'nothing yet') + '.')
    if kind == 'hint':
        if 'riddle' not in state['solved']:
            text = 'Examine the desk. The riddle describes something you might read.'
        elif 'key' not in state['inventory']:
            text = 'Collect the brass key revealed by the desk riddle.'
        elif not state['drawer_open']:
            text = 'Use your collected key to open the drawer.'
        elif 'order' not in state['solved']:
            text = 'Examine the open drawer for a note.'
        elif 'numbers' not in state['solved']:
            text = 'Examine the bookshelf and record the numbers.'
        elif 'painting' not in state['discovered']:
            text = 'Examine the painting to learn the order of the symbols.'
        else:
            text = 'Read the book numbers in the order shown in the painting, then unlock the door.'
        return result(True, text)
    if target not in ROOM['objects'] + ['key']:
        return result(False, 'That object is not available. Explore the desk, bookshelf, painting, drawer or door.')
    if kind == 'examine':
        if target == 'drawer' and not state['drawer_open']:
            return result(False, 'The drawer is locked. You need to collect its brass key first.')
        if target == 'key' and not state['key_available']:
            return result(False, 'You have not found a key yet.')
        if target not in state['discovered']:
            state['discovered'].append(target)
        if target == 'desk':
            return result(True, 'A plaque on the desk asks: ' + ROOM['riddle'])
        if target == 'bookshelf':
            if 'numbers' not in state['solved']:
                state['solved'].append('numbers')
            return result(True, 'Four book spines show: ' + ', '.join(
                f'{symbol} = {number}' for symbol, number in ROOM['book_numbers'].items()) + '.')
        if target == 'painting':
            return result(True, 'The painting shows symbols from left to right: ' + ', '.join(ROOM['order']) + '.')
        if target == 'drawer':
            if 'order' not in state['solved']:
                state['solved'].append('order')
            return result(True, 'A note reads: Match each painted symbol to its book number. Read left to right.')
        if target == 'key':
            return result(True, 'A small brass key fits the drawer lock.')
        return result(True, 'The exit keypad needs four digits. Gather the clues before attempting to escape.')
    if kind == 'solve' and target == 'desk':
        if 'desk' not in state['discovered']:
            return result(False, 'Examine the desk before answering its riddle.')
        if value.rstrip('.!') not in ROOM['riddle_answers']:
            return result(False, 'The desk compartment stays closed. That answer does not fit the riddle.')
        if 'riddle' not in state['solved']:
            state['solved'].append('riddle')
        state['key_available'] = True
        return result(True, 'A compartment clicks open, revealing a brass key. You can take it.')
    if kind == 'take' and target == 'key':
        if not state['key_available']:
            return result(False, 'No key is available. Solve the desk riddle first.')
        if 'key' not in state['inventory']:
            state['inventory'].append('key')
        return result(True, 'The brass key is in your inventory.')
    if (kind == 'open' and target == 'drawer') or (kind == 'use' and target == 'key'):
        if 'key' not in state['inventory']:
            return result(False, 'You cannot use a key you have not collected.')
        state['drawer_open'] = True
        return result(True, 'Your brass key opens the drawer. Examine it to read the note inside.')
    if kind in {'unlock', 'open'} and target == 'door':
        if value != ROOM['door_code']:
            return result(False, 'The keypad rejects the combination. The exit remains locked.')
        if (set(state['solved']) != {'riddle', 'order', 'numbers'}
                or 'painting' not in state['discovered'] or not state['drawer_open']
                or 'key' not in state['inventory']):
            return result(False, 'The exit remains locked. Complete the desk, drawer, bookshelf and painting trail first.')
        state['door_open'] = state['escaped'] = True
        return result(True, 'The keypad glows green. The door opens and you step into the rain. You escaped!')
    return result(False, 'That action is not possible here. Examine an object, solve the desk riddle, take the key or unlock the door.')
