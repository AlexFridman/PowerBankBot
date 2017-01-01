import datetime

import humanize
import telegram_dialog as td
from collections import namedtuple
from emoji import emojize

User = namedtuple('User', ['user_id'])


class CreditType(namedtuple('Credit', ['credit_id', 'name', 'description', 'currency', 'percent',
                                       'overdue_percent', 'duration'])):
    def to_html(self):
        return td.HTML(('<b>{0.name}</b>\n'
                        'валюта: <i>{0.currency}</i>\n'
                        'процент: <i>{0.percent}%</i>\n'
                        'срок: <i>{0.duration}</i>\n'
                        '<pre>{0.description}</pre>').format(self))

    @classmethod
    def from_json(cls, json):
        humanize.i18n.activate('ru_RU')
        return cls(
            credit_id=json['Id'],
            name=json['Name'],
            description=json['Description'],
            currency=json['CurrencyShort'],
            percent=round(json['Percent'] * 100),
            overdue_percent=json['OverduePercent'],
            duration=humanize.naturaldelta(datetime.timedelta(days=int(json['ReturnTerm'].split('.')[0])))
        )


class UserCredit(namedtuple('UserCredit', ['credit_type', 'is_closed', 'start_date', 'end_date', 'main_debt'])):
    @classmethod
    def from_json(cls, json):
        humanize.i18n.activate('ru_RU')
        return UserCredit(
            credit_type=CreditType.from_json(json['CreditType']),
            is_closed=json['IsClosed'],
            start_date=humanize.naturaldate(datetime.datetime.strptime(json['FormattedStartDate'][:10], '%d.%m.%Y')),
            end_date=humanize.naturaldate(datetime.datetime.strptime(json['FormattedEndDate'][:10], '%d.%m.%Y')),
            main_debt=json['MainDebt']
        )

    @property
    def name(self):
        if self.is_closed:
            return emojize(':white_check_mark: {0.credit_type.name}'.format(self), use_aliases=True)
        return self.credit_type.name

    def to_html(self):
        # TODO: replace with real template string
        return td.HTML(('<b>{0.name}</b>\n'
                        'валюта: <i>{0.currency}</i>\n'
                        'процент: <i>{0.percent}%</i>\n'
                        'срок: <i>{0.duration}</i>\n'
                        '<pre>{0.description}</pre>').format(self.credit_type))


class RequestUpdate(namedtuple('RequestUpdate', ['update_id', 'user_id', 'request_id', 'credit_type_name', 'timestamp',
                                                 'type', 'value', 'seen'])):
    @classmethod
    def from_json(cls, json):
        # TODO: implement
        pass
