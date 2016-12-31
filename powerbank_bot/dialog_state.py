import logging
import time

from powerbank_bot.api_wrapper import ApiWrapper
from powerbank_bot.storage import Storage

LOGGER = logging.getLogger('dialog_state')

INITIAL_DIALOG_STATE = {
    'user_id': None,
    'phone_number': None,
    'is_authenticated': False,
    'auth_locked_till': 0
}
HOUR = 60 * 60


class DialogState:
    def __init__(self, storage, api_wrapper, state):
        self._state = state
        self._storage = storage
        self._api_wrapper = api_wrapper

    @classmethod
    def load(cls, dialog_id):
        LOGGER.debug('Requested dialog ({}) state loading'.format(dialog_id))
        storage = Storage()
        api_wrapper = ApiWrapper()

        dialog_state = storage.get_dialog_state(dialog_id)
        if dialog_state is None:
            LOGGER.debug('Failed to load state of dialog ({})'.format(dialog_id))
            dialog_state = INITIAL_DIALOG_STATE.copy()
            dialog_state['dialog_id'] = dialog_id

        return cls(storage, api_wrapper, dialog_state)

    def save(self):
        self._storage.upsert_dialog_state(self._state)

    @property
    def is_authenticated(self):
        return self._state['is_authenticated']

    @property
    def is_auth_locked(self):
        return time.time() > self._state['auth_locked_till']

    @property
    def dialog_id(self):
        return self._state['dialog_id']

    @property
    def user_id(self):
        return self._state['dialog_id']

    @property
    def phone_number(self):
        return self._state['phone_number']

    def lock_auth_for(self, seconds=HOUR):
        self._state['auth_locked_till'] = int(time.time() + seconds)
