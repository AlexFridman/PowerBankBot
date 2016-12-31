import telegram_dialog as td
from collections import namedtuple

User = namedtuple('User', ['user_id'])


class Credit(namedtuple('Credit', ['name', 'currency', 'percentage', 'duration'])):
    def to_html(self):
        return td.HTML('''<b>{0.name}</b>\n<i>{0.currency}</i>'''.format(self))


class ApiWrapper:
    def __init__(self):
        self._authorise()

    def _authorise(self):
        pass

    def get_user_by_phone_number(self, phone_number):
        return User(user_id='1234')

    def get_user_requests(self, user_id):
        pass

    def get_user_credits(self, user_id):
        pass

    def get_credits_info(self):
        return [
            Credit(
                name='кредит 1',
                currency='BYN',
                percentage='15',
                duration='24 месяца'
            ),
            Credit(
                name='кредит 2',
                currency='BYN',
                percentage='25',
                duration='24 месяца'
            ),
            Credit(
                name='кредит 3',
                currency='BYN',
                percentage='35',
                duration='24 месяца'
            )
        ]
