# -*- coding: utf-8 -*-

import os
import requests

from powerbank_bot.config import Api
from powerbank_bot.helpers.models import UserCredit, CreditType


class ApiWrapper:
    def get_user_by_phone_number(self, phone_number):
        url = os.path.join(Api.base_url, 'Users/GetUserIdByPhoneNumber', phone_number.replace('+', ''))
        response = requests.get(url, auth=Api.credentials)
        # TODO: proceed response. Return None if user was not found.

    def get_user_requests(self, user_id):
        pass

    def get_user_credits(self, user_id):
        url = os.path.join(Api.base_url, 'Credits/GetForUser', user_id)
        return [UserCredit.from_json(credit) for credit in requests.get(url, auth=Api.credentials).json()]

    def get_credit_types(self):
        url = os.path.join(Api.base_url, 'CreditTypes')
        return [CreditType.from_json(credit) for credit in requests.get(url, auth=Api.credentials).json()
                if credit['IsActive']]


if __name__ == '__main__':
    ApiWrapper().get_user_by_phone_number('+375291301111')
