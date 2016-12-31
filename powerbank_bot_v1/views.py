from telepot.namedtuple import ReplyKeyboardMarkup

from powerbank_bot_v1.view_types import KeyboardViewType, ListViewType

INITIAL_MARKUP = ReplyKeyboardMarkup(one_time_keyboard=True, keyboard=[
    ['First view', 'Second view', 'List view'],
])
FIRST_VIEW_MARKUP = ReplyKeyboardMarkup(one_time_keyboard=True, keyboard=[
    ['Initial view', 'Second view'],
])
SECOND_VIEW_MARKUP = ReplyKeyboardMarkup(one_time_keyboard=True, keyboard=[
    ['Initial view', 'First view'],
])


class InitialView(KeyboardViewType):
    def __init__(self, sender):
        super(InitialView, self).__init__(sender, keyboard_markup=INITIAL_MARKUP, message='Hello')

    def get_next_view(self, msg):
        if msg['text'] == 'First view':
            return FirstView(self._sender)
        elif msg['text'] == 'Second view':
            return SecondView(self._sender)
        elif msg['text'] == 'List view':
            return ListView(self._sender, [['1', '2']])


class FirstView(KeyboardViewType):
    def __init__(self, sender, keyboard_markup=FIRST_VIEW_MARKUP):
        super(FirstView, self).__init__(sender, keyboard_markup)

    def get_next_view(self, msg):
        if msg['text'] == 'Initial view':
            return InitialView(self._sender)
        elif msg['text'] == 'Second view':
            return SecondView(self._sender)


class SecondView(KeyboardViewType):
    def __init__(self, sender, keyboard_markup=SECOND_VIEW_MARKUP):
        super(SecondView, self).__init__(sender, keyboard_markup)

    def get_next_view(self, msg):
        if msg['text'] == 'First view':
            return FirstView(self._sender, FIRST_VIEW_MARKUP)
        elif msg['text'] == 'Second view':
            return InitialView(self._sender)


class ListView(ListViewType):
    def __init__(self, *args, **kwargs):
        super(ListView, self).__init__(*args, **kwargs)

    def get_next_view(self, msg):
        if msg['text'] == 'First view':
            return FirstView(self._sender)
        elif msg['text'] == '1':
            return InitialView(self._sender)
