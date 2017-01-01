from powerbank_bot.bot.field_coroutines import text_question

from powerbank_bot.bot.validators import RangeIntegerValidator


class FormField:
    def __init__(self, name, description, dtype=str, validators=None):
        self.name = name
        self.description = description
        self.dtype = dtype
        self.validators = validators or []

    def get_question_method(self, show_back_button=False):
        return text_question(self.description, self.validators, show_back_button)


CREDIT_FORM = [
    FormField('amount', 'Укажите размер кредита', int, [RangeIntegerValidator(100, 10000)]),
    FormField('month_income', 'Укажите среднемесячный доход за последний год', int, [RangeIntegerValidator(100, 10000)])
]


def create_form_dialog(schema, accept_back=True):
    form_res = {}
    for form_field in schema:
        value = yield from form_field.get_question_method(accept_back)
        if value is None:
            return
        form_res[form_field.name] = form_field.dtype(value)
    return form_res
