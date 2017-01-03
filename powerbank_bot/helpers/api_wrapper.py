# -*- coding: utf-8 -*-

import os

import requests

from powerbank_bot.config import Api
from powerbank_bot.helpers.models import UserCredit, CreditType, User, Request, RequestStatus


class ApiWrapper:
    def get_user_by_login(self, login):
        url = os.path.join(Api.base_url, 'Users/GetUserByLogin', login)
        response = requests.get(url, auth=Api.credentials)
        if response.status_code == 200:
            return User.from_json(response.json())

    def get_user_by_phone_number(self, phone_number):
        url = os.path.join(Api.base_url, 'Users/GetUserIdByPhoneNumber', phone_number.replace('+', ''))
        response = requests.get(url, auth=Api.credentials)
        if response.status_code == 200:
            return User.from_json(response.json())

    def get_user_by_id(self, user_id):
        url = os.path.join(Api.base_url, 'Users', 'get', user_id)
        response = requests.get(url, auth=Api.credentials)
        if response.status_code == 200:
            return User.from_json(response.json())

    def get_user_requests(self, user_id):
        url = os.path.join(Api.base_url, 'Requests/GetForUsers', user_id)
        return [Request.from_json(request) for request in requests.get(url, auth=Api.credentials).json()]

    def get_request(self, request_id):
        url = os.path.join(Api.base_url, 'Requests', 'get', request_id)
        return [Request.from_json(request) for request in requests.get(url, auth=Api.credentials).json()]

    def get_user_credits(self, user_id):
        url = os.path.join(Api.base_url, 'Credits/GetForUsers', user_id)
        return [UserCredit.from_json(credit) for credit in requests.get(url, auth=Api.credentials).json()]

    def get_credit(self, user_id, credit_id):
        for credit in self.get_user_credits(user_id):
            if credit.credit_id == credit_id:
                return credit

    def get_credit_types(self):
        url = os.path.join(Api.base_url, 'CreditTypes', 'get')
        return [CreditType.from_json(credit) for credit in requests.get(url, auth=Api.credentials).json()
                if credit['IsActive']]

    def get_credit_type(self, credit_type_id):
        for credit_type in self.get_credit_types():
            if credit_type.credit_id == credit_type_id:
                return credit_type

    def send_request(self, user_id, credit_type, amount, month_income, return_id=False):
        if return_id:
            existing_ids = {r.request_id for r in self.get_user_requests(user_id)}

        payload = {
            'ClientId': user_id,
            'Type': 1,
            'State': 0,
            'Amount': amount,
            'CreditTypeId': credit_type.credit_id,
            'TypeName': credit_type.name,
            'MonthIncome': month_income,
            'StatusString': RequestStatus.IN_PROCESS
        }
        url = os.path.join(Api.base_url, 'Requests', 'post')
        requests.post(url, auth=Api.credentials, data=payload).raise_for_status()

        if return_id:
            new_ids = {r.request_id for r in self.get_user_requests(user_id)}
            return min(new_ids - existing_ids)
