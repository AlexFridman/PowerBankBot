import logging
from collections import OrderedDict

import telegram_dialog as td
from emoji import emojize

from powerbank_bot.bot.dialog_state import DialogState, UserNotFoundError, CannotSendMessageError, ApiError
from powerbank_bot.bot.field_coroutines import text_question, BACK_BUTTON_CONTENT
from powerbank_bot.bot.forms import create_form_dialog, create_credit_form, SCORING_FORM
from powerbank_bot.bot.validators import LoginValidator
from powerbank_bot.helpers.models import ScoringForm

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger('dialogs')

MAKE_YOUR_CHOICE_CAPTION = 'Сделайте Ваш выбор'
GENERAL_ERROR_CAPTION = 'Произошла ошибка. Попробуйте позже'


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

    def get_keyboard(self):
        return td.Keyboard(self.get_menu(), resize_keyboard=True)


@td.requires_personal_chat('Работаю tet-a-tet')
def main_menu_dialog(start_message):
    dialog_id = start_message.from_user.id
    dialog_state = DialogState.load(dialog_id)

    while True:
        menu = Menu([(credit_list_dialog(dialog_state), 'Информация о доступных кредитах')])

        if dialog_state.is_authenticated:
            menu.add_item(personal_account_dialog(dialog_state), 'Личный кабинет')
            menu.add_item(log_out_dialog(dialog_state), emojize('Выйти :door:', use_aliases=True))
        elif not dialog_state.is_auth_locked:
            menu.add_item(auth_dialog(dialog_state), 'Авторизация')

        selected, _ = yield from td.require_choice('Главное меню', menu.get_keyboard(), MAKE_YOUR_CHOICE_CAPTION)
        yield from menu[selected]


def only_back(message='Только назад'):
    return td.require_choice(message, td.Keyboard([BACK_BUTTON_CONTENT], resize_keyboard=True), 'Только назад')


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
            yield from only_back(GENERAL_ERROR_CAPTION)
            return
        else:
            break
    else:
        dialog_state.lock_auth()
        dialog_state.save()
        yield from only_back('Количество попыток превышено. Попробуйте позже')
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
        yield from only_back('Количество попыток превышено. Попробуйте позже')
        return


def credit_list_dialog(dialog_state):
    while True:
        menu = Menu([(credit_info_dialog(dialog_state, credit_type), credit_type.name)
                     for credit_type in dialog_state.api.get_credit_types()], back_button=True)

        selected, _ = yield from td.require_choice('Выберите тип кредита', menu.get_keyboard(),
                                                   MAKE_YOUR_CHOICE_CAPTION)

        if menu[selected] is None:
            return
        yield from menu[selected]


def credit_info_dialog(dialog_state, credit_type):
    menu = Menu(back_button=True)
    if dialog_state.is_authenticated:
        menu.add_item(create_credit_request_dialog(dialog_state, credit_type), 'Подать заявку')

    selected, _ = yield from td.require_choice(credit_type.to_html(), menu.get_keyboard(), MAKE_YOUR_CHOICE_CAPTION)

    if menu[selected] is None:
        return
    yield from menu[selected]


def create_credit_request_dialog(dialog_state, credit_type):
    form = yield from create_form_dialog(create_credit_form(credit_type.currency))
    if form is None:
        return
    else:
        try:
            request_id = dialog_state.make_credit_request(credit_type, form, return_id=True)
        except ApiError:
            yield from only_back(GENERAL_ERROR_CAPTION)
        else:
            selected, _ = yield from td.require_choice('Заявка успешно подана. Хотите заполнить скоринговую форму?',
                                                       td.Keyboard(['Да', 'Нет'], resize_keyboard=True),
                                                       MAKE_YOUR_CHOICE_CAPTION)
            if selected == 0:
                yield from fill_scoring_form(dialog_state, request_id)


def fill_scoring_form(dialog_state, request_id):
    try:
        request = dialog_state.api.get_request(dialog_state.user_id, request_id)
        credit_type = dialog_state.api.get_credit_type(request.credit_type_id)
    except:
        yield from only_back(GENERAL_ERROR_CAPTION)
        return

    form = yield from create_form_dialog(SCORING_FORM)

    form['request_id'] = request_id
    form['credit_amount'] = request.amount
    form['duration_in_month'] = credit_type.duration_in_month

    try:
        form['result'] = dialog_state.get_prediction(form)
    except ApiError:
        yield from only_back(GENERAL_ERROR_CAPTION)
    else:
        dialog_state.storage.update_scoring_form(form)
        yield from only_back(ScoringForm(form).to_html())


def log_out_dialog(dialog_state):
    dialog_state.log_out()
    dialog_state.save()
    yield from only_back('Вы успешно вышли из аккаунта')


def personal_account_dialog(dialog_state):
    while True:
        menu = Menu(
            [
                (user_credit_list_dialog(dialog_state), 'Кредиты'),
                (user_requests_dialog(dialog_state), 'Заявки'),
                (user_updates_dialog(dialog_state), 'Обновления')
            ],
            back_button=True
        )

        selected, _ = yield from td.require_choice('Личный кабинет', menu.get_keyboard(), MAKE_YOUR_CHOICE_CAPTION)

        if menu[selected] is None:
            return
        yield from menu[selected]


def user_credit_list_dialog(dialog_state):
    while True:
        try:
            menu = Menu([(only_back(credit.to_html()), credit.name)
                         for credit in dialog_state.get_credits()], back_button=True)
        except ApiError:
            yield from only_back(GENERAL_ERROR_CAPTION)
            return

        selected, _ = yield from td.require_choice('Выберите кредит', menu.get_keyboard(), MAKE_YOUR_CHOICE_CAPTION)

        if menu[selected] is None:
            return
        yield from menu[selected]

def user_requests_dialog(dialog_state):
    while True:
        try:
            menu = Menu([(user_request_info_dialog(dialog_state, request), request.name)
                         for request in dialog_state.get_requests()], back_button=True)
        except ApiError:
            yield from only_back(GENERAL_ERROR_CAPTION)
            return

        selected, _ = yield from td.require_choice('Выберите заявку', menu.get_keyboard(), MAKE_YOUR_CHOICE_CAPTION)

        if menu[selected] is None:
            return
        yield from menu[selected]


def user_request_info_dialog(dialog_state, request):
    menu = Menu(back_button=True)

    form = dialog_state.storage.get_scoring_form(request.request_id)
    if form:
        menu.add_item(only_back(form.to_html()), 'Показать скоринговую форму')
    else:
        menu.add_item(fill_scoring_form(dialog_state, request.request_id),
                      'Заполнить скоринговую форму')

    selected, _ = yield from td.require_choice(request.to_html(), menu.get_keyboard(), MAKE_YOUR_CHOICE_CAPTION)

    if menu[selected] is None:
        return
    yield from menu[selected]


def user_updates_dialog(dialog_state):
    try:
        updates = dialog_state.get_request_updates()
    except ApiError:
        yield from only_back(GENERAL_ERROR_CAPTION)
        return

    if updates:
        message = td.HTML('\n\n'.join((update.to_html() for update in updates)))
    else:
        message = 'Новых обновлений нет ¯\_(ツ)_/¯'

    for update in updates:
        dialog_state.storage.mark_request_update_as_seen(update.update_id)

    yield from only_back(message)
