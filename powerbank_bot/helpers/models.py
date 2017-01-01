import datetime
from collections import namedtuple

import humanize
import telegram_dialog as td
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


class RequestStatus:
    IN_PROCESS = 'Рассматривается'
    APPROVED = 'Подтверждена'
    REJECTED = 'Отклонена'


class Request(namedtuple('Request', ['request_id', 'credit_type_name', 'request_date', 'amount', 'status'])):
    # TODO: add scoring staff
    @classmethod
    def from_json(cls, json):
        return Request(
            request_id=json['Id'],
            credit_type_name=json['TypeName'],
            request_date=json['FormattedDate'][:10],
            amount=json['Amount'],
            status=json['StatusString']
        )

    def to_html(self):
        return td.HTML(('<b>{0.credit_type_name}</b>\n'
                        'сумма: <i>{0.amount}</i>\n'
                        'дата подачи: <i>{0.request_date}%</i>\n'
                        'статус: <i>{0.status}</i>').format(self))

    @property
    def credit_name(self):
        # TODO: add status dependent emoji. Maybe amount also should be added, because it is hard to distinguish
        # request only by name.
        return self.credit_type_name


class RequestUpdate(namedtuple('RequestUpdate', ['update_id', 'user_id', 'request_id', 'credit_type_name', 'timestamp',
                                                 'event_type', 'event_value', 'seen'])):
    event_type_map = {
        'status_update': 'Изменения статуса заявки',
        'comment_added': 'Добавлен комментарий'
    }

    @classmethod
    def from_json(cls, json):
        return cls(
            update_id=json['update_id'],
            user_id=json['user_id'],
            request_id=json['request_id'],
            credit_type_name=json['credit_type_name'],
            timestamp=json['timestamp'],
            event_type=cls.event_type_map[json['event_type']],
            event_value=json['event_value'],
            seen=json['seen']
        )

    def to_html(self):
        # TODO: display in different style depend on event_type
        return td.HTML(('<b>{0.event_type}</b>\n'
                        '{0.event_value}').format(self))
