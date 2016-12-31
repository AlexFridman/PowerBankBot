import logging
import time

from powerbank_bot.helpers.api_wrapper import ApiWrapper
from powerbank_bot.helpers.storage import Storage

LOGGER = logging.getLogger('dialog_state')


class AuthState:
    AUTHENTICATED = 'authenticated'
    CODE_SENT = 'code_sent'
    NONE = 'node'


INITIAL_DIALOG_STATE = {
    'user_id': None,
    'phone_number': None,
    'is_authenticated': False,
    'auth_locked_till': 0,
    'auth_state': AuthState.NONE
}
HOUR = 60 * 60


class UserNotFoundError(Exception):
    pass


class DialogState:
    def __init__(self, storage, api_wrapper, state):
        self._state = state
        self._storage = storage
        self._api_wrapper = api_wrapper

    @property
    def api(self):
        return self._api_wrapper

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
        return self._state['auth_state'] == AuthState.AUTHENTICATED

    @property
    def is_auth_locked(self):
        return time.time() < self._state['auth_locked_till']

    @property
    def dialog_id(self):
        return self._state['dialog_id']

    @property
    def user_id(self):
        return self._state['dialog_id']

    @property
    def phone_number(self):
        return self._state['phone_number']

    def lock_auth(self, seconds=HOUR):
        self._state['auth_locked_till'] = int(time.time() + seconds)

    def _generate_verification_code(self):
        return '1234'

    def _send_confirmation_message(self):
        pass

    def start_authentication(self, phone_number):
        # TODO: add logging
        if self.is_auth_locked:
            raise RuntimeError('Auth locked till {}'.format(self._state['auth_locked_till']))
        elif self.is_authenticated:
            raise RuntimeError('Already authenticated')

        user = self._api_wrapper.get_user_by_phone_number(phone_number)
        if user is None:
            raise UserNotFoundError('User with this number does not exist')
        self._state['user_id'] = user.user_id

        self._state['phone_number'] = phone_number
        self._state['verification_code'] = self._generate_verification_code()
        self._send_confirmation_message()
        self._state['auth_state'] = AuthState.CODE_SENT

    def complete_authentication(self, verification_code):
        # TODO: add logging
        if not self._state['auth_state'] == AuthState.CODE_SENT:
            raise RuntimeError('Call start_authentication first')
        elif verification_code != self._state['verification_code']:
            return False

        self._state['auth_state'] = AuthState.AUTHENTICATED
        return True

    def reset_auth_state(self):
        self._state['auth_state'] = AuthState.NONE
        self._state['phone_number'] = None

    def log_out(self):
        if not self.is_authenticated:
            raise RuntimeError('Can not perform log out procedure. Not authenticated')
        self.reset_auth_state()

    def create_credit_request(self, credit):
        # TODO: implement
        pass
