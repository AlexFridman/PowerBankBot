from multiprocessing import Process

import telegram_dialog as td

from powerbank_bot.bot.dialogs import main_menu_dialog
from powerbank_bot.bot_api import run_bot_api
from powerbank_bot.config import Telegram


def main():
    api_process = Process(target=run_bot_api)
    api_process.start()

    dialog_bot = td.DialogBot(Telegram.token, main_menu_dialog)
    dialog_bot.start()


if __name__ == '__main__':
    main()
