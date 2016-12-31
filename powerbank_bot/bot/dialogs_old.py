import telegram_dialog as td

from powerbank_bot.bot.field_coroutines import BACK_BUTTON_CONTENT, text_question
from powerbank_bot.bot.validators import PhoneNumberValidator
from powerbank_bot.helpers.api_wrapper import ApiWrapper
from powerbank_bot.helpers.storage import Storage


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

    while True:
        menu = Menu([MenuItem(info_menu(user_id), 'Инфо')])

        if Storage().is_authenticated_user(user_id):
            menu.items.append(MenuItem(personal_info(), 'Личный кабинет'))
        else:
            menu.items.append(MenuItem(auth_dialog(user_id), 'Авторизоваться'))

        selected, msg = yield from td.require_choice('Главное меню', menu.choose_list, 'Нужно что то выбрать')

        yield from menu.items[selected].coroutine


def info_menu(user_id):
    credits = ApiWrapper().get_credits_info()
    credit_names = [c['name'] for c in credits]

    while True:
        (selected, _), msg = yield from td.require_choice('Тип кредита',
                                                          [[BACK_BUTTON_CONTENT]] + [[c] for c in credit_names],
                                                          'Нужно что то выбрать')
        if selected == 0:
            return
        else:
            yield from credit_info(credits[selected - 1], Storage().is_authenticated_user(user_id))


def auth_dialog(user_id):
    ENTER_PHONE_NUMBER_TRIALS_COUNT = 3
    ENTER_VERIFICATION_CODE_TRIALS_COUNT = 3

    PHONE_NUMBER_MESSAGE = 'Введите номер телефона (375 XX XXXXXX)'

    for _ in range(ENTER_PHONE_NUMBER_TRIALS_COUNT):
        phone_number = yield from text_question(
            PHONE_NUMBER_MESSAGE,
            [PhoneNumberValidator()],
            show_back_button=True)

        if not phone_number:
            return

        user = ApiWrapper().get_user_by_phone_number(phone_number)

        if user:
            break
        else:
            PHONE_NUMBER_MESSAGE = 'Пользователь с таким номерорм не зарегистрирован\nВведите номер телефона'
    else:
        # TODO: блокировать на время
        yield td.HTML('Кол-во попыток превышено. Блокировка'), ['Меню']
        return

    verification_code = '1234'
    # send sms

    VERIFICATION_CODE_MESSAGE = 'Введите проверочный код (1234)'

    for _ in range(ENTER_VERIFICATION_CODE_TRIALS_COUNT):
        code = yield from text_question(
            VERIFICATION_CODE_MESSAGE,
            show_back_button=True)

        if not code:
            return

        if code == verification_code:
            break
        else:
            VERIFICATION_CODE_MESSAGE = 'Неверный код. Попробуйте еще раз'
    else:
        # TODO: блокировать на время
        # yield td.HTML('Кол-во попыток превышено. Блокировка'), ['Меню']
        # return
        yield from only_back('Кол-во попыток превышено. Блокировка')
        return

    Storage().authenticate_user(user_id)


def personal_info():
    pass


def only_back(message='Только назад'):
    return td.require_choice(message, [BACK_BUTTON_CONTENT], 'Только назад')


def credit_info(credit, is_authenticated=False):
    credit_info = 'Кредит {name}\n{percent}%'.format(name=credit['name'], percent=credit['%'])
    button_list = [BACK_BUTTON_CONTENT]
    if is_authenticated:
        button_list.append('Подать заявку')
    selected, _ = yield from td.require_choice(credit_info, button_list)

    if selected == 0:
        return
    elif selected == 1 and is_authenticated:
        pass  # GO TO credit request form
    else:
        yield from only_back()
