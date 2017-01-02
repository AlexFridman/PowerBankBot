import telegram_dialog as td

MAKE_YOUR_CHOICE_CAPTION = 'Сделайте Ваш выбор'
BACK_BUTTON_CONTENT = 'Назад'
BACK = -1


def text_question(question, validators=None, show_back_button=False):
    validators = validators or []
    error = None
    while True:
        q = question
        if error:
            q = error + '\n' + question
        if show_back_button:
            answer = yield td.HTML(q), td.Keyboard([BACK_BUTTON_CONTENT], resize_keyboard=True)
        else:
            answer = yield td.HTML(q)

        if answer['text'] == BACK_BUTTON_CONTENT:
            return

        for validator in validators:
            validation_res = validator(answer['text'])
            if not validation_res.result:
                error = validation_res.error
                break
        else:
            return answer['text']


def select_question(question, choices, show_back_button=False):
    markup = [[choice] for choice in choices]

    if show_back_button:
        markup = [[BACK_BUTTON_CONTENT]] + markup

    (selected, _), _ = yield from td.require_choice(question, markup, MAKE_YOUR_CHOICE_CAPTION)

    if selected:
        return selected
