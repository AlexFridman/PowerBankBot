# -*- coding: utf-8 -*-

import os
import requests

from powerbank_bot.config import Api
from powerbank_bot.helpers.models import User, UserCredit, CreditType


class ApiWrapper:
    def get_user_by_phone_number(self, phone_number):
        # TODO: implement
        return User(user_id='1234')

    def get_user_requests(self, user_id):
        pass

    def get_user_credits(self, user_id):
        # TODO: use user_id
        url = os.path.join(Api.base_url, 'Credits')
        return [UserCredit.from_json(credit) for credit in requests.get(url, auth=Api.credentials).json()]

    def get_credit_types(self):
        url = os.path.join(Api.base_url, 'CreditTypes')
        return [CreditType.from_json(credit) for credit in requests.get(url, auth=Api.credentials).json()
                if credit['IsActive']]
