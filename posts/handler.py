import datetime as dt
import subprocess
import sqlite3

from collections import defaultdict

sessionStorage = {}
newsStorage = {}
modeStorage = defaultdict(tuple)
DB_NAME = 'news.sqlite'


def handle_dialog(req, res):
    user_id = req['session']['user_id']
    subprocess.Popen(['python3', 'news_grabber.py'])
    if req['session']['new']:
        sessionStorage[user_id] = {
            'suggests': [
                "Да",
                "Нет",
                "Отстань!",
            ]
        }
        newsStorage[user_id] = 0
        modeStorage[user_id] = False, dt.date.today().weekday()
        res['response']['text'] = 'Привет! Рассказать новости?'
        res['response']['buttons'] = get_suggests(user_id)
        return

    if req['request']['original_utterance'].lower() in [
        'нет',
        'отстань',
    ]:
        # Пользователь отказался, прощаемся.
        res['response'][
            'text'] = 'Хорошо, если захотите узнать - сообщите мне!'
        res['response']['end_session'] = True
        return

    if req['request']['original_utterance'].lower() in [
        'понедельник',
        'вторник',
        'среда',
        'четверг',
        'пятница',
        'суббота',
        'воскресенье'
    ]:
        weekdays = ['воскресенье', 'понедельник', 'вторник',
                    'среда', 'четверг', 'пятница', 'суббота', ]
        weekday = weekdays.index(
            req['request']['original_utterance'].lower())
        current_mode, current_weekday = modeStorage[user_id]
        if not current_mode or weekday != current_weekday:
            newsStorage[user_id] = 0
        modeStorage[user_id] = True, weekday

    if req['request']['original_utterance'].lower() in [
        'назад ко всем новостям'
    ]:
        newsStorage[user_id] = 0
        modeStorage[user_id] = False, dt.date.today().weekday()

    is_future_request = False
    if req['request']['original_utterance'].lower() in [
        'есть что поновее?']:
        if newsStorage[user_id] - 6 < 0:
            is_future_request = True
            res['response']['text'] = 'Я - не машина времени, ' \
                                      'новости из будущего не получаю :)'
            res['response']['buttons'] = get_suggests(user_id)
        newsStorage[user_id] = max(0, newsStorage[user_id] - 6)
    if not is_future_request:
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        offset = max(0, newsStorage[user_id])
        is_weekday_mode, weekday = modeStorage[user_id]
        que = 'SELECT message FROM news '
        if is_weekday_mode:
            que += f"WHERE strftime('%w',pub_date) = '{weekday}' AND " \
                "pub_date BETWEEN datetime('now','-6 days') AND datetime('now') "
        que += 'ORDER BY id DESC ' \
            f'LIMIT 3 OFFSET {offset}'
        data = cur.execute(que).fetchall()
        answ = [str(offset + i) + ': ' + msg[0][:335]
                for i, msg in enumerate(data, 1)]
        newsStorage[user_id] += 3
        answ = '\n'.join(answ) if answ else 'И тут новости кончаются...'
        res['response']['text'] = answ
        res['response']['buttons'] = get_suggests(user_id)


def get_suggests(user_id):
    # если режим поиска по дням недели
    if modeStorage[user_id][0]:
        sessionStorage[user_id] = {
            'suggests': [
                "Ещё из этого дня",
                "Назад ко всем новостям",
            ]
        }
    else:
        sessionStorage[user_id] = {
            'suggests': [
                "Да",
                "Отстань",
                "Есть что поновее?",
                "Предыдущие новости",
                "Понедельник",
                "Вторник",
                "Среда",
                "Четверг",
                "Пятница",
                "Суббота",
                "Воскресенье",
            ]
        }
    session = sessionStorage[user_id]
    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in session['suggests']
    ]

    return suggests
