import logging

import telegram_dialog as td
from collections import OrderedDict

from powerbank_bot.bot.dialog_state import DialogState, UserNotFoundError
from powerbank_bot.bot.field_coroutines import text_question, BACK_BUTTON_CONTENT
from powerbank_bot.bot.validators import PhoneNumberValidator

logging.basicConfig(level=logging.DEBUG)


class Menu:
    def __init__(self, items=None):
        self.items = OrderedDict(enumerate(items or []))

    def add_item(self, dialog_procedure, display_name):
        self.items[len(self.items)] = (dialog_procedure, display_name)

    def __getitem__(self, index):
        row, column = index
        dialog_procedure, _ = self.items[row]
        return dialog_procedure

    def get_menu(self):
        return [[display_name] for _, (_, display_name) in self.items.items()]


@td.requires_personal_chat('Работаю tet-a-tet')
def main_menu_dialog(start_message):
    dialog_id = start_message.chat_id
    dialog_state = DialogState.load(dialog_id)

    while True:
        menu = Menu([(credit_list_dialog(dialog_state), 'Информация о доступных кредитах')])

        if dialog_state.is_authenticated:
            menu.add_item(personal_account_dialog(dialog_state), 'Личный кабинет')
            menu.add_item(log_out_dialog(dialog_state), 'Выйти')
        elif not dialog_state.is_auth_locked:
            menu.add_item(auth_dialog(dialog_state), 'Авторизация')

        selected, _ = yield from td.require_choice('Главное меню', menu.get_menu(), 'Сделайте Ваш выбор')
        yield from menu[selected]


def only_back(message='Только назад'):
    return td.require_choice(message, [BACK_BUTTON_CONTENT], 'Только назад')


def auth_dialog(dialog_state):
    enter_phone_number_trials_count = 3
    enter_verification_code_trials_count = 3

    phone_number_message = 'Введите номер телефона (375 XX XXXXXX)'

    for _ in range(enter_phone_number_trials_count):
        phone_number = yield from text_question(
            phone_number_message,
            [PhoneNumberValidator()],
            show_back_button=True
        )

        if not phone_number:
            # "back" button pressed
            return

        try:
            dialog_state.start_authentication(phone_number)
        except UserNotFoundError:
            phone_number_message = 'Пользователь с таким номерорм не зарегистрирован\nВведите номер телефона'
        except Exception:
            # TODO: call reset_auth_state
            yield from only_back('Произошла ошибка. Попробуйте позже')
            return
        else:
            break
    else:
        dialog_state.lock_auth()
        dialog_state.save()
        yield 'Количество попыток превышено. Попробуйте позже', ['Меню']
        return

    verification_code_message = 'Введите проверочный код'

    for _ in range(enter_verification_code_trials_count):
        code = yield from text_question(
            verification_code_message,
            show_back_button=True
        )

        if not code:
            # "back" button pressed
            # TODO: call reset_auth_state
            return

        if dialog_state.complete_authentication(code):
            break
        else:
            verification_code_message = 'Неверный код. Попробуйте еще раз'
    else:
        dialog_state.lock_auth()
        dialog_state.save()
        yield 'Количество попыток превышено. Попробуйте позже', ['Меню']
        return


def credit_list_dialog(dialog_state):
    answer = yield 'Список кредитов'


def log_out_dialog(dialog_state):
    answer = yield 'Выход'


def personal_account_dialog(dialog_state):
    answer = yield 'Личный кабинет'
