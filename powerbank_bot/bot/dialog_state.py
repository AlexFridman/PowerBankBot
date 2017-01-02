import logging
import time
from random import randint

import requests
import sendgrid
import sendgrid.helpers.mail as sg_mail

from powerbank_bot.config import Email, BotApi
from powerbank_bot.helpers.api_wrapper import ApiWrapper
from powerbank_bot.helpers.storage import Storage

LOGGER = logging.getLogger('dialog_state')


class AuthState:
    AUTHENTICATED = 'authenticated'
    CODE_SENT = 'code_sent'
    NONE = 'node'


INITIAL_DIALOG_STATE = {
    'user_id': None,
    'login': None,
    'email': None,
    'is_authenticated': False,
    'auth_locked_till': 0,
    'auth_state': AuthState.NONE
}
HOUR = 60 * 60


class UserNotFoundError(Exception):
    pass


class CannotSendMessageError(Exception):
    pass


class ApiError(Exception):
    pass


class DialogState:
    def __init__(self, storage, api_wrapper, state):
        self._state = state
        self._storage = storage
        self._api_wrapper = api_wrapper

    @property
    def api(self):
        return self._api_wrapper

    @property
    def storage(self):
        return self._storage

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
        return self._state['user_id']

    @property
    def login(self):
        return self._state['login']

    @property
    def email(self):
        return self._state['email']

    def lock_auth(self, seconds=HOUR):
        self._state['auth_locked_till'] = int(time.time() + seconds)

    def _generate_verification_code(self):
        return str(randint(1000, 9999))

    def _send_confirmation_message(self):
        LOGGER.debug(self._state['verification_code'])
        sg = sendgrid.SendGridAPIClient(apikey=Email.api_key)
        from_email = sg_mail.Email(Email.address, Email.sender)
        subject = 'Код подтверждения'
        to_email = sg_mail.Email(self._state['email'])
        content = sg_mail.Content('text/plain', 'Ваш код подтверждения: ' + self._state['verification_code'])
        mail = sg_mail.Mail(from_email, subject, to_email, content)
        try:
            response = sg.client.mail.send.post(request_body=mail.get())
            LOGGER.debug(response.status_code)
            LOGGER.debug(response.body)
            LOGGER.debug(response.headers)
        except Exception as e:
            LOGGER.error('Failed to send message')
            raise CannotSendMessageError(e)

    def start_authentication(self, login):
        # TODO: add logging
        if self.is_auth_locked:
            raise RuntimeError('Auth locked till {}'.format(self._state['auth_locked_till']))
        elif self.is_authenticated:
            raise RuntimeError('Already authenticated')

        user = self._api_wrapper.get_user_by_login(login)
        LOGGER.debug(user)
        if user is None:
            raise UserNotFoundError('User with this login does not exist')
        self._state['user_id'] = user.user_id

        self._state['login'] = login
        self._state['email'] = user.email
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

    def make_credit_request(self, credit_type, form, return_id=False):
        try:
            return self._api_wrapper.send_request(self.user_id, credit_type, form['amount'],
                                                  form['month_income'], return_id)
        except Exception as e:
            LOGGER.exception('Failed to send request')
            raise ApiError(e)

    def get_credits(self):
        try:
            return self._api_wrapper.get_user_credits(self.user_id)
        except Exception as e:
            LOGGER.exception('Failed to get credits')
            raise ApiError(e)

    def get_requests(self):
        try:
            return self._api_wrapper.get_user_requests(self.user_id)
        except Exception as e:
            LOGGER.exception('Failed to get requests')
            raise ApiError(e)

    def get_request_updates(self):
        try:
            return self._storage.get_user_request_updates(self.user_id)
        except Exception as e:
            LOGGER.exception('Failed to get updates')
            raise ApiError(e)

    @staticmethod
    def get_prediction(form):
        try:
            # TODO: assume bot api is running on the same machine
            return requests.post('http://localhost:{port}/predict_proba'.format(port=BotApi.port),
                                 json=form).json()['prob']
        except Exception as e:
            raise ApiError(e)
