import sys
from abc import abstractmethod

import telepot
from telepot.delegate import pave_event_space, per_chat_id, create_open
from telepot.namedtuple import ReplyKeyboardMarkup

from powerbank_bot_v1.view_types import KeyboardViewType, ListViewType
from powerbank_bot_v1.views import InitialView

INITIAL_MARKUP = ReplyKeyboardMarkup(one_time_keyboard=True, keyboard=[
    ['First screen', 'Second screen', 'List screen'],
])
FIRST_VIEW_MARKUP = ReplyKeyboardMarkup(one_time_keyboard=True, keyboard=[
    ['Initial view', 'Second screen'],
])
SECOND_VIEW_MARKUP = ReplyKeyboardMarkup(one_time_keyboard=True, keyboard=[
    ['Initial view', 'First screen'],
])

BUTTON_STATE_MAP = {
    'First screen': 'first_screen',
    'Second screen': 'second_screen',
    'Initial view': 'initial_view',
    'List screen': 'list_screen',
}

VIEW_CONF = {
    'initial_view': (KeyboardViewType, {'message': 'Hello!', 'keyboard_markup': INITIAL_MARKUP}, 'first_screen'),
    'first_screen': (
        KeyboardViewType, {'message': 'First screen', 'keyboard_markup': FIRST_VIEW_MARKUP}, 'second_screen'),
    'second_screen': (
        KeyboardViewType, {'message': 'First screen', 'keyboard_markup': SECOND_VIEW_MARKUP}, 'first_screen'),
    'list_screen': (ListViewType, {'message': 'chose one', 'items': ['1', '2', '3']}, 'item_info'),
    'item_info': (KeyboardViewType, {'keyboard_markup': INITIAL_MARKUP}, 'initial_view'),
}
TOKEN = '300227038:AAEqqG_KMPhuq-eydlsT94TMY8eY46WRhjE'


class Startegy(object):
    def __init__(self):
        self.end = False

    @abstractmethod
    def step(self, msg):
        pass


class TwoFieldFormStrategy(Startegy):
    def __init__(self):
        super(TwoFieldFormStrategy, self).__init__()
        self.state = 1

    def step_1(self):
        pass

    def step_2(self):
        pass

    def next_step(self, msg):
        if self.state == 1:
            pass  # display 1st field view
            self.state += 1
        elif self.state == 2:
            pass  # 2nd field view
        else:
            self.end = True


class MenuStrategy(Startegy):
    def step(self, msg):
        if msg == 'start':
            InitialView().go(msg)
        elif msg == 'Auth':
            self.end = True
            self.next_start = Auth


class PowerBankBot(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(PowerBankBot, self).__init__(*args, **kwargs)
        self._current_view = InitialView(self.sender)
        self._strategy = None

    def on_chat_message(self, msg):
        self.strat.set(msg)
        if self.strat.end:
            self.strat = self.strat.next_strat
            self.strat.step()
        # if msg['text'] == '/start':
        #     self._current_view = InitialView(self.sender)
        # else:
        #     self._current_view = self._current_view.get_next_view(msg)
        # self._current_view.go(msg)


if __name__ == '__main__':
    bot = telepot.DelegatorBot(TOKEN, [
        pave_event_space()(
            per_chat_id(), create_open, PowerBankBot, timeout=100),
    ])
    bot.message_loop(run_forever='Listening ...')
