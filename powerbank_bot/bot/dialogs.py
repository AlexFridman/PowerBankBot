import logging
from collections import OrderedDict

import telegram_dialog as td

from powerbank_bot.bot.dialog_state import DialogState, UserNotFoundError, CannotSendMessageError, ApiError
from powerbank_bot.bot.field_coroutines import text_question, BACK_BUTTON_CONTENT
from powerbank_bot.bot.forms import create_form_dialog, create_credit_form
from powerbank_bot.bot.validators import LoginValidator

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger('dialogs')

MAKE_YOUR_CHOICE_CAPTION = 'Сделайте Ваш выбор'


class Menu:
    def __init__(self, items=None, back_button=False):
        if back_button:
            items = [(None, BACK_BUTTON_CONTENT)] + (items or [])
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

        selected, _ = yield from td.require_choice('Главное меню', menu.get_menu(), MAKE_YOUR_CHOICE_CAPTION)
        yield from menu[selected]


def only_back(message='Только назад'):
    return td.require_choice(message, [BACK_BUTTON_CONTENT], 'Только назад')


def auth_dialog(dialog_state):
    enter_phone_number_trials_count = 3
    enter_verification_code_trials_count = 3

    login_message = 'Введите логин'

    for _ in range(enter_phone_number_trials_count):
        login = yield from text_question(
            login_message,
            [LoginValidator()],
            show_back_button=True
        )

        if not login:
            # "back" button pressed
            return

        try:
            dialog_state.start_authentication(login)
        except UserNotFoundError:
            login_message = 'Пользователь с таким логином не зарегистрирован\nВведите логин'
        except CannotSendMessageError:
            dialog_state.reset_auth_state()
            yield from only_back('Не удалось отправить код подтверждения. Попробуйте позже')
            return
        except Exception as e:
            LOGGER.exception('error')
            dialog_state.reset_auth_state()
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
            dialog_state.reset_auth_state()
            return

        if dialog_state.complete_authentication(code):
            dialog_state.save()
            break
        else:
            verification_code_message = 'Неверный код. Попробуйте еще раз'
    else:
        dialog_state.lock_auth()
        dialog_state.save()
        yield 'Количество попыток превышено. Попробуйте позже', ['Меню']
        return


def credit_list_dialog(dialog_state):
    while True:
        menu = Menu([(credit_info_dialog(dialog_state, credit_type), credit_type.name)
                     for credit_type in dialog_state.api.get_credit_types()], back_button=True)

        selected, _ = yield from td.require_choice('Выберите тип кредита', menu.get_menu(), MAKE_YOUR_CHOICE_CAPTION)

        if menu[selected] is None:
            return
        yield from menu[selected]


def credit_info_dialog(dialog_state, credit_type):
    menu = Menu(back_button=True)
    if dialog_state.is_authenticated:
        menu.add_item(create_credit_request_dialog(dialog_state, credit_type), 'Подать заявку')

    selected, _ = yield from td.require_choice(credit_type.to_html(), menu.get_menu(), MAKE_YOUR_CHOICE_CAPTION)

    if menu[selected] is None:
        return
    yield from menu[selected]


def create_credit_request_dialog(dialog_state, credit_type):
    form = yield from create_form_dialog(create_credit_form(credit_type.currency))
    if form is None:
        return
    else:
        try:
            dialog_state.make_credit_request(credit_type, form)
        except ApiError:
            yield from only_back('Произошла ошибка. Попробуйте позже')
        else:
            yield 'Заявка успешно подана'
            # TODO: scoring form should be here


def log_out_dialog(dialog_state):
    dialog_state.log_out()
    dialog_state.save()
    yield from only_back('Вы успешно вышли из аккаунта')


def personal_account_dialog(dialog_state):
    menu = Menu(
        [
            (user_credit_list_dialog(dialog_state), 'Кредиты'),
            (user_requests_dialog(dialog_state), 'Заявки'),
            (user_updates_dialog(dialog_state), 'Обновления')
        ],
        back_button=True
    )

    while True:
        selected, _ = yield from td.require_choice('Личный кабинет', menu.get_menu(), MAKE_YOUR_CHOICE_CAPTION)

        if menu[selected] is None:
            return
        yield from menu[selected]


def user_credit_list_dialog(dialog_state):
    while True:
        menu = Menu([(user_credit_info_dialog(dialog_state, credit), credit.name)
                     for credit in dialog_state.get_credits()], back_button=True)

        selected, _ = yield from td.require_choice('Выберите кредит', menu.get_menu(), MAKE_YOUR_CHOICE_CAPTION)

        if menu[selected] is None:
            return
        yield from menu[selected]


def user_credit_info_dialog(dialog_state, credit):
    yield from only_back(credit.to_html())


def user_requests_dialog(dialog_state):
    while True:
        menu = Menu([(user_request_info_dialog(dialog_state, request), request.credit_name)
                     for request in dialog_state.get_requests()], back_button=True)

        selected, _ = yield from td.require_choice('Выберите заявку', menu.get_menu(), MAKE_YOUR_CHOICE_CAPTION)

        if menu[selected] is None:
            return
        yield from menu[selected]


def user_request_info_dialog(dialog_state, request):
    yield from only_back(request.to_html())


def user_updates_dialog(dialog_state):
    updates = dialog_state.get_request_updates()

    if updates:
        message = '\n\n'.join((update.to_html() for update in updates))
    else:
        message = 'Новых обновлений нет'

    for update in updates:
        dialog_state.storage.mark_request_update_as_seen(update.update_id)

    yield from only_back(message)
