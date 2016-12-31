import telegram_dialog as td

from powerbank_bot.api_wrapper import ApiWrapper
from powerbank_bot.field_coroutines import BACK_BUTTON_CONTENT, text_question
from powerbank_bot.storage import Storage
from powerbank_bot.validators import PhoneNumberValidator


class MenuItem:
    def __init__(self, coroutine, description):
        self.coroutine = coroutine
        self.description = description


class Menu:
    def __init__(self, items):
        self.items = items

    @property
    def choose_list(self):
        return [item.description for item in self.items]


@td.requires_personal_chat('Идем в личный чат')
def main_menu(start_message):
    user_id = start_message['id']
    menu = Menu([MenuItem(info_menu(), 'Инфо')])

    if Storage().is_authenticated_user(user_id):
        menu.items.append(MenuItem(personal_info(), 'Личный кабинет'))
    else:
        menu.items.append(MenuItem(auth_dialog(user_id), 'Авторизоваться'))

    selected, msg = yield from td.require_choice('Привет!', menu.choose_list, 'Нужно что то выбрать')

    yield from menu.items[selected].coroutine


def info_menu():
    credits = ApiWrapper().get_credits()
    credit_names = [c['name'] for c in credits]

    while True:
        (selected, _), msg = yield from td.require_choice('Тип кредита',
                                                          [[BACK_BUTTON_CONTENT]] + [[c] for c in credit_names],
                                                          'Нужно что то выбрать')
        if selected == 0:
            return
        else:
            yield from credit_info(credits[selected - 1])


def auth_dialog(user_id):
    phone_number = yield from text_question('Введите номер телефона (375 XX XXXXXX)', [PhoneNumberValidator()], True)
    if not phone_number:
        return

    is_user_exists = False

    while not is_user_exists:
        user = ApiWrapper().get_user_by_phone_number(phone_number)
        if user:
            is_user_exists = True
        else:
            phone_number = yield from text_question(
                'Пользователь с таким номер не зарегистрирован\nВведите номер телефона',
                [PhoneNumberValidator()], True)
            if not phone_number:
                return

    verification_code = '1234'
    # send sms

    code = yield from text_question('Введите проверочный код (1234)', show_back_button=True)
    if not code:
        return

    if code != verification_code:
        is_correct_code = False
        # TODO: limit tries
        while not is_correct_code:
            code = yield from text_question('Неверный код. Попробуйте еще раз', show_back_button=True)
            if not code:
                return
            if code == verification_code:
                is_correct_code = True

    Storage().authenticate_user(user_id)


def personal_info():
    pass


def only_back():
    return td.require_choice('Только назад', [BACK_BUTTON_CONTENT], 'Только назад')


def credit_info(credit):
    answer = yield 'Кредит {name}\n{percent}%'.format(name=credit['name'], percent=credit['%']), [BACK_BUTTON_CONTENT]
    if answer['text'] == BACK_BUTTON_CONTENT:
        return
    yield from only_back()


if __name__ == '__main__':
    TOKEN = '300227038:AAEqqG_KMPhuq-eydlsT94TMY8eY46WRhjE'
    import telegram_dialog as td

    dialog_bot = td.DialogBot(TOKEN, main_menu)
    dialog_bot.start()
