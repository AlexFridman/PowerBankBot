import datetime
import html
import math
from collections import namedtuple

import humanize
import telegram_dialog as td
from babel.dates import format_date, parse_date
from emoji import emojize

from powerbank_bot.bot.forms import SCORING_FORM, SelectFormField, FormField


class User(namedtuple('Credit', ['user_id', 'login', 'email'])):
    @classmethod
    def from_json(cls, json):
        return cls(
            user_id=str(json['UserId']),
            login=json['Login'],
            email=json['Email']
        )


class CreditType(namedtuple('Credit', ['credit_id', 'name', 'description', 'currency', 'percent',
                                       'overdue_percent', 'duration', 'duration_in_month'])):
    def to_html(self):
        return td.HTML(('<b>{0.name}</b>\n'
                        'валюта: <i>{0.currency}</i>\n'
                        'процент: <i>{0.percent}%</i>\n'
                        # do not show loan, because api is shitty 'срок: <i>{0.duration}</i>\n'
                        '<pre>{0.description}</pre>').format(self))

    @classmethod
    def from_json(cls, json):
        humanize.i18n.activate('ru_RU')
        return cls(
            credit_id=str(json['Id']),
            name=json['Name'],
            description=json['Description'],
            currency=json['CurrencyShort'],
            percent=round(json['Percent'] * 100),
            overdue_percent=json['OverduePercent'],
            duration=humanize.naturaldelta(datetime.timedelta(days=int(json['ReturnTerm'].split('.')[0]))),
            duration_in_month=math.ceil(datetime.timedelta(days=int(json['ReturnTerm'].split('.')[0])).days / 30.5)
        )


class UserCredit(namedtuple('UserCredit', ['credit_type', 'is_closed', 'start_date', 'end_date', 'main_debt',
                                           'start_amount', 'monthly_payment', 'monthly_main_debt',
                                           'monthly_percentage_debt', 'penalty_fee', 'credit_id'])):
    @classmethod
    def from_json(cls, json):
        return UserCredit(
            credit_id=str(json['Id']),
            credit_type=CreditType.from_json(json['CreditType']),
            is_closed=json['IsClosed'],
            start_date=format_date(parse_date(json['FormattedStartDate'][:10], locale='de_DE'), locale='ru_RU'),
            end_date=format_date(parse_date(json['FormattedEndDate'][:10], locale='de_DE'), locale='ru_RU'),
            main_debt=json['MainDebt'],
            start_amount=json['StartAmount'],
            monthly_payment=json['CalculatedMonthlyPayment'],
            monthly_main_debt=json['MonthlyMainDebt'],
            monthly_percentage_debt=json['MonthlyPercentageDebt'],
            penalty_fee=json['PenaltyFee']
        )

    @property
    def name(self):
        loan_term = '{0.start_date} - {0.end_date}  '.format(self)

        if self.is_closed:
            return loan_term + emojize('{0.credit_type.name} :white_check_mark:'.format(self), use_aliases=True)
        return loan_term + self.credit_type.name

    def to_html(self):
        return td.HTML(('<b>{0.name}</b>\n'
                        'валюта: <i>{0.credit_type.currency}</i>\n'
                        'процент: <i>{0.credit_type.percent}%</i>\n'
                        'открыт: <i>{0.start_date}</i>\n'
                        'дата завершения: <i>{0.end_date}</i>\n'
                        'взятая сумма: <code>{0.start_amount:.2f}</code>\n'
                        'ежемесячный платеж: <code>{0.monthly_payment:.2f}</code>\n'
                        'остаток основного долга: <code>{0.main_debt:.2f}</code>\n'
                        'к оплате: <code>{1:.2f}</code> '
                        '(Основной долг - <code>{0.monthly_main_debt:.2f}</code>, '
                        'Проценты - <code>{0.monthly_percentage_debt:.2f}</code>, '
                        'Пеня - <code>{0.penalty_fee:.2f}</code>)\n'
                        '<pre>{0.credit_type.description}</pre>').format(self, self.monthly_main_debt +
                                                                         self.monthly_percentage_debt +
                                                                         self.penalty_fee))


class RequestStatus:
    IN_PROCESS = 'Рассматривается'
    APPROVED = 'Подтверждена'
    REJECTED = 'Отклонена'

    @classmethod
    def status_to_emoji(cls, status):
        status_emoji_map = {
            cls.IN_PROCESS: ':clock3:',
            cls.APPROVED: ':white_check_mark:',
            cls.REJECTED: ':x:'
        }
        return status_emoji_map[status]


class Request(namedtuple('Request', ['request_id', 'credit_type_name', 'credit_type_id', 'request_date',
                                     'amount', 'status'])):
    @classmethod
    def from_json(cls, json):
        return Request(
            request_id=str(json['Id']),
            credit_type_name=json['TypeName'],
            credit_type_id=str(json['CreditTypeId']),
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
        return emojize('{} {}'.format(self.credit_type_name, RequestStatus.status_to_emoji(self.status)),
                       use_aliases=True)

    @property
    def name(self):
        return emojize('{} {} {}'.format(self.request_date, self.credit_type_name,
                                         RequestStatus.status_to_emoji(self.status)), use_aliases=True)


class RequestUpdate(namedtuple('RequestUpdate', ['update_id', 'user_id', 'request_id', 'credit_type_name', 'timestamp',
                                                 'date_time', 'event_type', 'event_value', 'seen'])):
    @classmethod
    def from_json(cls, json):
        return cls(
            update_id=json['update_id'],
            user_id=json['user_id'],
            request_id=json['request_id'],
            credit_type_name=json['credit_type_name'],
            timestamp=json['timestamp'],
            date_time=datetime.datetime.utcfromtimestamp(json['timestamp']),
            event_type=json['event_type'],
            event_value=json['event_value'],
            seen=json['seen']
        )

    def to_html(self):
        print(self.event_type)
        humanize.i18n.activate('ru_RU')
        humanized_time = humanize.naturaltime(self.date_time)
        if self.event_type == 'comment_added':
            return emojize(('<b>Добавлен комментарий</b> :speech_balloon:\n'
                            'к завке на кредит "{0.credit_type_name}":\n'
                            '<pre>{0.event_value}</pre>\n'
                            '{1}').format(self, humanized_time), use_aliases=True)
        elif self.event_type == 'status_update':
            return emojize(('<b>Обновлён статус заявки</b> {0}\n'
                            'на кредит "{1.credit_type_name}"\n'
                            '{2}').format(RequestStatus.status_to_emoji(self.event_value), self,
                                          humanized_time), use_aliases=True)
        raise NotImplementedError()


class ScoringForm(dict):
    def __init__(self, form):
        super().__init__(**form)

    def to_html(self):
        template = '<b>{field}</b>:\t<code>{value}</code>'
        rows = []
        for field in SCORING_FORM:
            if isinstance(field, SelectFormField):
                value = field.choices[self[field.name]]
            elif isinstance(field, FormField):
                value = self[field.name]
            else:
                raise NotImplementedError()
            rows.append(template.format(field=html.escape(field.description), value=html.escape(str(value))))

        return td.HTML('Скоринговая форма\n' +
                       '\n'.join(rows) +
                       '\n-----------------\n' +
                       template.format(field='Результат', value='{:.0%}'.format(self['result'])))
