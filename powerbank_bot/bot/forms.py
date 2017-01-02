from powerbank_bot.bot.field_coroutines import text_question, select_question

from powerbank_bot.bot.validators import RangeIntegerValidator


class FormField:
    def __init__(self, name, description, dtype=str, validators=None):
        self.name = name
        self.description = description
        self.dtype = dtype
        self.validators = validators or []

    def get_question_method(self, show_back_button=False):
        return text_question(self.description, self.validators, show_back_button)


class SelectFormField(FormField):
    def __init__(self, name, description, choices):
        super().__init__(name, description, int)
        self.choices = choices

    def get_question_method(self, show_back_button=False):
        return select_question(self.description, self.choices, show_back_button)


def create_credit_form(currency):
    return [
        FormField('amount', 'Укажите размер кредита, {}'.format(currency), int, [RangeIntegerValidator(100, 10000)]),
        FormField('month_income', 'Укажите среднемесячный доход за последний год', int,
                  [RangeIntegerValidator(100, 10000)])
    ]


SCORING_FORM = [
    SelectFormField('status_of_existing_checking_account', 'Статус текущего счета',
                    ['... < 0 руб.', '0 <= ... < 200 руб.', '... >= 200 руб.', 'нет счета']),
    SelectFormField('credit_history', 'Кредитная история',
                    ['кредиты не брались / все кредиты погашены',
                     'все кредиты в нашем банке выплачивались своевременно', 'текущие кредиты выплачиваются вовремя',
                     'имели место несвоевременные выплаты в прошлом', 'критический аккаунт']),
    SelectFormField('purpose', 'Цель', ['автомобиль (новый)',
                                        'автомобиль (б/у)',
                                        'мебель / оборудывание',
                                        'радио / телевидение',
                                        'бытовая техника',
                                        'ремонт',
                                        'образование',
                                        'отпуск',
                                        'переквалификация',
                                        'бизнес',
                                        'другое']),
    SelectFormField('savings_account', 'Текущий счет', ['... < 100 руб.',
                                                        '100 <= ... < 500 руб.',
                                                        '500 <= ... < 1000 руб.',
                                                        '... > 1000 руб.',
                                                        'нет данных / нет аккаунта']),
    SelectFormField('present_employment_since', 'Время на текущем месте работы', ['безработный',
                                                                                  '... < 1 года',
                                                                                  '1 <= ... < 4 года',
                                                                                  '4 <= ... < 7 лет',
                                                                                  '... >= 7 лет']),
    FormField('installment_rate', 'Процент выплат от дохода', int, [RangeIntegerValidator(1, 100)]),
    SelectFormField('personal_status', 'Семейное положение и пол', ['мужской, разведен',
                                                                    'женский, разведена / замужем',
                                                                    'мужской, холост',
                                                                    'мужской, женат',
                                                                    'женский, не замужем']),
    SelectFormField('other_debtors', 'Поручители', ['нет', 'созаявитель', 'гарант']),
    FormField('present_residence_since', 'Время проживания на текущем месте жительства (лет)', int,
              [RangeIntegerValidator(1, 100)]),
    SelectFormField('property', 'Имущество', ['недвижимость',
                                              'страхование жизни',
                                              'автомобиль',
                                              'нет данных / нет имущества']),
    FormField('age', 'Возраст (лет)', int, [RangeIntegerValidator(18, 100)]),
    SelectFormField('installment_plans', 'Другие рассрочки', ['банк', 'магазин', 'нет']),
    SelectFormField('housing', 'Жилье', ['съемное', 'собственное', 'бесплатное']),
    FormField('number_of_existing_credits', 'Количество текущих кредитов в нашем банке', int,
              [RangeIntegerValidator(0, 10)]),
    SelectFormField('job', 'Тип занятости', ['безработный / неквалифицированный - нерезидент',
                                             'неквалифицированный - резидент',
                                             'квалифицированный',
                                             'менеджмент / высококвалифицированный']),
    SelectFormField('telephone', 'Телефон', ['нет', 'есть']),
    SelectFormField('foreign_worker', 'Иностранный работник', ['да', 'нет']),
]


def create_form_dialog(schema, accept_back=True):
    form_res = {}
    for form_field in schema:
        value = yield from form_field.get_question_method(accept_back)
        if value is None:
            return
        form_res[form_field.name] = form_field.dtype(value)
    return form_res
