from abc import abstractmethod

from telepot.namedtuple import ReplyKeyboardMarkup


class ViewTypeBase(object):
    def __init__(self, sender):
        self._sender = sender

    @abstractmethod
    def _action(self, msg):
        pass

    def go(self, msg):
        self._action(msg)


class KeyboardViewType(ViewTypeBase):
    def __init__(self, sender, keyboard_markup, message=None):
        super(KeyboardViewType, self).__init__(sender)
        self._keyboard_markup = keyboard_markup
        self._message = message

    def _action(self, msg):
        self._sender.sendMessage(str(self._message), reply_markup=self._keyboard_markup)


class ListViewType(KeyboardViewType):
    def __init__(self, sender, items, one_time_keyboard=True, message=None):
        keyboard_markup = ReplyKeyboardMarkup(one_time_keyboard=one_time_keyboard, keyboard=items)
        super(ListViewType, self).__init__(sender, keyboard_markup, message)

    def _action(self, msg):
        self._sender.sendMessage(str(self._message), reply_markup=self._keyboard_markup)
