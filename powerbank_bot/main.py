from powerbank_bot.bot.dialogs import main_menu

if __name__ == '__main__':
    TOKEN = '300227038:AAEqqG_KMPhuq-eydlsT94TMY8eY46WRhjE'
    import telegram_dialog as td

    dialog_bot = td.DialogBot(TOKEN, main_menu)
    dialog_bot.start()
