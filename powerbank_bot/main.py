from multiprocessing import Process

import telegram_dialog as td

from powerbank_bot.bot.dialogs import main_menu_dialog
from powerbank_bot.bot_api import bot_api_app
from powerbank_bot.config import BotApi, Telegram

if __name__ == '__main__':
    api_process = Process(target=bot_api_app.run, args=(BotApi.host, BotApi.port))
    api_process.start()

    dialog_bot = td.DialogBot(Telegram.token, main_menu_dialog)
    dialog_bot.start()
