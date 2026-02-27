#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║   🎰 ULTIMATE CASINO BOT — ИСПРАВЛЕННАЯ ВЕРСИЯ              ║
║   (УБРАНЫ ВСЕ ОБРАТНЫЕ СЛЕШИ ИЗ F-СТРОК)                    ║
╚══════════════════════════════════════════════════════════════╝
"""

import telebot
import random
import time
import sqlite3
import os
import json
import logging
import threading
import shutil
import glob
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from functools import wraps
from collections import defaultdict
import sys

# ============================================================
# 🔧 КОНФИГУРАЦИЯ
# ============================================================
TOKEN = '8330930174:AAE78xbihnPhNns2QlCvv81msnAEmEAz-Zk'  # ← ТВОЙ ТОКЕН
ADMIN_IDS = [6511166842]  # ← ТВОЙ ID

if not TOKEN:
    print("❌ ОШИБКА: Не задан BOT_TOKEN в переменных окружения!")
    sys.exit(1)
# База данных
DB_FILE = 'casino.db'

# Экономика
START_BALANCE = 1000
MAX_BET = 10000
MIN_BET = 1
MAX_WIN = 500000
REFERRAL_FRIEND = 500
REFERRAL_OWNER = 200
JACKPOT_BASE = 50000
JACKPOT_CONTRIBUTION = 0.05
WEEKEND_MULTIPLIER = 2.0
CURRENCY = 'КК'

# Технические настройки
BACKUP_HOURS = 6
FLOOD_MSGS = 5
FLOOD_WINDOW = 3

# ============================================================
# 📋 УРОВНИ
# ============================================================
LEVELS = {
    1:  {'name':'🥚 Новичок',    'xp':0,       'reward':0},
    2:  {'name':'🐣 Стартер',    'xp':100,     'reward':200},
    3:  {'name':'🐥 Игрок',      'xp':300,     'reward':400},
    4:  {'name':'🎮 Геймер',     'xp':600,     'reward':600},
    5:  {'name':'🎯 Меткий',     'xp':1000,    'reward':1000},
    6:  {'name':'💫 Удачливый',  'xp':1500,    'reward':1200},
    7:  {'name':'🌟 Звезда',     'xp':2200,    'reward':1500},
    8:  {'name':'🔥 Горячий',    'xp':3000,    'reward':2000},
    9:  {'name':'⚡ Молния',     'xp':4000,    'reward':2500},
    10: {'name':'💎 Бриллиант',  'xp':5500,    'reward':3000},
    15: {'name':'🏆 Чемпион',    'xp':15000,   'reward':5000},
    20: {'name':'👑 Король',     'xp':35000,   'reward':10000},
    30: {'name':'🌙 Лунатик',    'xp':80000,   'reward':20000},
    50: {'name':'☄️ Легенда',    'xp':250000,  'reward':50000},
    100:{'name':'🎭 БОГ КАЗИНО', 'xp':1000000, 'reward':200000},
}

# ============================================================
# 🏆 ДОСТИЖЕНИЯ
# ============================================================
ACHIEVEMENTS = {
    'first_game':   {'name':'🎮 Первый шаг',      'desc':'Сыграй первую игру',         'r':100},
    'first_win':    {'name':'🏆 Первая победа',    'desc':'Выиграй первый раз',          'r':150},
    'jackpot':      {'name':'💰 ДЖЕКПОТ!',         'desc':'Выбей джекпот в слотах',      'r':5000},
    'games_10':     {'name':'🎯 10 игр',           'desc':'Сыграй 10 игр',               'r':200},
    'games_100':    {'name':'💯 100 игр',          'desc':'Сыграй 100 игр',              'r':1000},
    'games_1000':   {'name':'🌊 1000 игр',         'desc':'Сыграй 1000 игр',             'r':5000},
    'win_streak_3': {'name':'🔥 Стрик x3',         'desc':'3 победы подряд',             'r':300},
    'win_streak_5': {'name':'🔥🔥 Стрик x5',      'desc':'5 побед подряд',              'r':750},
    'win_streak_10':{'name':'⚡ Стрик x10',        'desc':'10 побед подряд',             'r':2000},
    'big_bet':      {'name':'💸 Ва-банк',          'desc':'Поставь 5000+ монет',         'r':500},
    'big_win':      {'name':'💰 Большой куш',      'desc':'Выиграй 10000+ монет',        'r':1000},
    'mega_win':     {'name':'🎊 МЕГАВЫИГРЫШ',      'desc':'Выиграй 50000+ монет',        'r':5000},
    'daily_7':      {'name':'📅 Неделя',           'desc':'7 дней бонусов подряд',       'r':2000},
    'daily_30':     {'name':'🗓️ Месяц',           'desc':'30 дней бонусов подряд',      'r':10000},
    'referral_1':   {'name':'👥 Рекрутёр',         'desc':'Пригласи 1 друга',            'r':500},
    'referral_5':   {'name':'🤝 Агент',            'desc':'Пригласи 5 друзей',           'r':2000},
    'level_10':     {'name':'⭐ Уровень 10',       'desc':'Достигни 10 уровня',          'r':3000},
    'level_50':     {'name':'🌟 Уровень 50',       'desc':'Достигни 50 уровня',          'r':25000},
    'blackjack_21': {'name':'🃏 Блэкджек!',        'desc':'Натуральный блэкджек',        'r':1000},
    'roulette_0':   {'name':'🎡 Зеро!',            'desc':'Угадай зеро в рулетке',       'r':2000},
    'crash_10x':    {'name':'🚀 Краш 10x',         'desc':'Выйди на x10 в краш-игре',    'r':2000},
    'crash_100x':   {'name':'☄️ Краш 100x',        'desc':'Выйди на x100 в краш-игре',   'r':20000},
    'bowling_strike':{'name':'🎳 Страйк!',         'desc':'Выбей страйк в боулинге',     'r':500},
    'darts_bull':   {'name':'🎯 Яблочко!',         'desc':'Попади в яблочко в дартсе',   'r':1500},
    'opened_case':  {'name':'📦 Коллекционер',     'desc':'Открой первый кейс',          'r':300},
    'opened_10':    {'name':'📦📦 Кейс-мастер',   'desc':'Открой 10 кейсов',            'r':2000},
    'rich_100k':    {'name':'💎 Стотысячник',      'desc':'Баланс 100 000+',             'r':5000},
    'broke':        {'name':'😢 Банкрот',          'desc':'Потеряй весь баланс',         'r':100},
    'duel_win':     {'name':'⚔️ Дуэлянт',         'desc':'Победи в дуэли',              'r':500},
    'clan_created': {'name':'🏰 Основатель',       'desc':'Создай клан',                 'r':1000},
    'clan_joined':  {'name':'🤜 Командный игрок',  'desc':'Вступи в клан',               'r':500},
    'gift_sent':    {'name':'🎁 Щедрый',           'desc':'Отправь подарок',             'r':200},
    'combo_5':      {'name':'🔥 Комбо x5',         'desc':'5 побед подряд',              'r':1000},
    'slots_200':    {'name':'🎰 Слот-мастер',      'desc':'Сыграй 200 слотов',           'r':3000},
    'all_games':    {'name':'🎭 Всеядный',         'desc':'Сыграй во все игры',          'r':3000},
    'loss_5_row':   {'name':'😤 Несдающийся',      'desc':'Проиграй 5 раз подряд',       'r':500},
}

# ============================================================
# 📦 КЕЙСЫ
# ============================================================
CASES = {
    'starter' :{'name':'📦 Стартовый','price':300,
                'prizes':[(100,30),(200,25),(300,20),(500,15),(1000,7),(2000,2),(5000,0.9),(10000,0.1)]},
    'medium'  :{'name':'💼 Средний','price':1000,
                'prizes':[(500,30),(1000,25),(2000,20),(3000,15),(5000,7),(10000,2),(25000,0.9),(50000,0.1)]},
    'premium' :{'name':'💎 Премиум','price':5000,
                'prizes':[(2000,25),(5000,25),(8000,20),(12000,15),(25000,8),(50000,4),(100000,2),(250000,1)]},
    'legendary':{'name':'🌟 Легендарный','price':20000,
                 'prizes':[(10000,20),(25000,25),(50000,25),(100000,15),(200000,8),(500000,4),(1000000,2)]},
}

# ============================================================
# 🛒 МАГАЗИН
# ============================================================
SHOP = {
    'skin_fire'   :{'name':'🔥 Огненный ник',       'price':2000,   'type':'skin',  'val':'🔥'},
    'skin_ice'    :{'name':'❄️ Ледяной ник',         'price':2000,   'type':'skin',  'val':'❄️'},
    'skin_gold'   :{'name':'👑 Золотой ник',          'price':5000,   'type':'skin',  'val':'👑'},
    'skin_diamond':{'name':'💎 Алмазный ник',         'price':10000,  'type':'skin',  'val':'💎'},
    'skin_devil'  :{'name':'😈 Дьявольский ник',      'price':15000,  'type':'skin',  'val':'😈'},
    'vip_badge'   :{'name':'⭐ VIP значок',           'price':25000,  'type':'badge', 'val':'⭐VIP'},
    'legend_badge':{'name':'🏆 ЛЕГЕНДА значок',       'price':100000, 'type':'badge', 'val':'🏆ЛЕГЕНДА'},
    'bonus_50'    :{'name':'💰 +50% к бонусу (30д)','price':8000,   'type':'boost', 'val':'bonus50'},
    'lucky_7'     :{'name':'🍀 Талисман удачи (7д)', 'price':5000,   'type':'boost', 'val':'lucky7'},
}

# ============================================================
# 🤖 ИНИЦИАЛИЗАЦИЯ БОТА
# ============================================================
bot = telebot.TeleBot(TOKEN, parse_mode=None)

# Словари для хранения состояний игр
coin_ch = {}
bj_games = {}
crash_games = {}
roulette_bets = {}
user_states = {}

# ============================================================
# 📝 ЛОГИРОВАНИЕ
# ============================================================
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/casino.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# 💾 БАЗА ДАННЫХ
# ============================================================
def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users(
            uid INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            fname TEXT DEFAULT 'Игрок',
            balance INTEGER DEFAULT 1000,
            won INTEGER DEFAULT 0,
            lost INTEGER DEFAULT 0,
            games INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            wstreak INTEGER DEFAULT 0,
            lstreak INTEGER DEFAULT 0,
            maxstreak INTEGER DEFAULT 0,
            combo INTEGER DEFAULT 0,
            last_bonus TEXT DEFAULT '',
            bstreak INTEGER DEFAULT 0,
            ref_by INTEGER DEFAULT 0,
            ref_cnt INTEGER DEFAULT 0,
            clan_id INTEGER DEFAULT 0,
            skin TEXT DEFAULT '',
            badge TEXT DEFAULT '',
            achs TEXT DEFAULT '[]',
            inv TEXT DEFAULT '{}',
            gstats TEXT DEFAULT '{}',
            banned INTEGER DEFAULT 0,
            created TEXT DEFAULT CURRENT_TIMESTAMP,
            active TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid INTEGER,
            game TEXT,
            bet INTEGER,
            result INTEGER,
            mult REAL,
            ts TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS duels(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenger INTEGER,
            opponent INTEGER DEFAULT 0,
            bet INTEGER,
            status TEXT DEFAULT 'waiting',
            winner INTEGER DEFAULT 0,
            ts TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS clans(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            owner INTEGER,
            desc TEXT DEFAULT '',
            bank INTEGER DEFAULT 0,
            members TEXT DEFAULT '[]',
            level INTEGER DEFAULT 1,
            ts TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS jackpot(
            id INTEGER PRIMARY KEY DEFAULT 1,
            amount INTEGER DEFAULT 50000
        );
        CREATE TABLE IF NOT EXISTS transactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid INTEGER,
            amount INTEGER,
            desc TEXT,
            ts TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS tournament(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            prize INTEGER DEFAULT 10000,
            start_ts TEXT,
            end_ts TEXT,
            scores TEXT DEFAULT '{}',
            status TEXT DEFAULT 'active',
            winner INTEGER DEFAULT 0
        );
        INSERT OR IGNORE INTO jackpot(id,amount) VALUES(1,50000);
    ''')
    conn.commit()
    conn.close()
    logger.info('✅ База данных инициализирована')

def get_user(uid):
    conn = get_db()
    row = conn.execute('SELECT * FROM users WHERE uid=?', (uid,)).fetchone()
    if not row:
        conn.execute('INSERT INTO users(uid) VALUES(?)', (uid,))
        conn.commit()
        row = conn.execute('SELECT * FROM users WHERE uid=?', (uid,)).fetchone()
    conn.close()
    return dict(row)

def update_user(uid, **kwargs):
    if not kwargs:
        return
    conn = get_db()
    sets = ','.join(f'{k}=?' for k in kwargs)
    conn.execute(f'UPDATE users SET {sets} WHERE uid=?', (*kwargs.values(), uid))
    conn.commit()
    conn.close()

def update_balance(uid, amount, desc=''):
    conn = get_db()
    conn.execute('UPDATE users SET balance=balance+? WHERE uid=?', (amount, uid))
    conn.execute('INSERT INTO transactions(uid,amount,desc) VALUES(?,?,?)', (uid, amount, desc))
    bal = conn.execute('SELECT balance FROM users WHERE uid=?', (uid,)).fetchone()[0]
    conn.commit()
    conn.close()
    return bal

def get_balance(uid):
    conn = get_db()
    row = conn.execute('SELECT balance FROM users WHERE uid=?', (uid,)).fetchone()
    conn.close()
    return row['balance'] if row else 0

def add_history(uid, game, bet, result, mult):
    conn = get_db()
    conn.execute('INSERT INTO history(uid,game,bet,result,mult) VALUES(?,?,?,?,?)',
                 (uid, game, bet, result, mult))
    conn.commit()
    conn.close()

def get_jackpot():
    conn = get_db()
    val = conn.execute('SELECT amount FROM jackpot WHERE id=1').fetchone()[0]
    conn.close()
    return val

def add_to_jackpot(amount):
    conn = get_db()
    conn.execute('UPDATE jackpot SET amount=amount+? WHERE id=1', (amount,))
    conn.commit()
    conn.close()

def hit_jackpot(uid):
    conn = get_db()
    amount = conn.execute('SELECT amount FROM jackpot WHERE id=1').fetchone()[0]
    conn.execute('UPDATE jackpot SET amount=? WHERE id=1', (JACKPOT_BASE,))
    conn.commit()
    conn.close()
    return amount

# ============================================================
# 🛡️ АНТИФЛУД
# ============================================================
flood_data = defaultdict(list)
flood_lock = threading.Lock()

def check_flood(uid):
    now = time.time()
    with flood_lock:
        flood_data[uid] = [t for t in flood_data[uid] if now - t < FLOOD_WINDOW]
        flood_data[uid].append(now)
        return len(flood_data[uid]) > FLOOD_MSGS

def anti_flood(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        uid = message.from_user.id
        if check_flood(uid):
            return
        user = get_user(uid)
        if user['banned']:
            return
        return func(message, *args, **kwargs)
    return wrapper

def admin_only(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        if message.from_user.id not in ADMIN_IDS:
            bot.send_message(message.chat.id, '🚫 Нет доступа')
            return
        return func(message, *args, **kwargs)
    return wrapper

# ============================================================
# 🔧 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================
def format_number(num):
    return f"{int(num):,}".replace(',', '_')

def escape_markdown(text):
    special_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{c}' if c in special_chars else c for c in str(text))

def is_weekend():
    return datetime.now().weekday() >= 5

def get_level_from_xp(xp):
    level = 1
    for lv, data in sorted(LEVELS.items()):
        if xp >= data['xp']:
            level = lv
    return level

def get_level_name(level):
    closest = 1
    for lv in sorted(LEVELS):
        if lv <= level:
            closest = lv
    return LEVELS[closest]['name']

def add_xp(uid, xp_amount):
    user = get_user(uid)
    old_level = user['level']
    new_xp = user['xp'] + xp_amount
    new_level = get_level_from_xp(new_xp)
    
    update_user(uid, xp=new_xp, level=new_level)
    
    reward = 0
    leveled_up = False
    
    if new_level > old_level:
        leveled_up = True
        closest = 1
        for lv in sorted(LEVELS):
            if lv <= new_level:
                closest = lv
        reward = LEVELS[closest]['reward']
        if reward:
            update_balance(uid, reward, f'Уровень {new_level}')
    
    return new_level, leveled_up, reward

def update_game_stat(uid, game):
    user = get_user(uid)
    stats = json.loads(user.get('gstats', '{}'))
    stats[game] = stats.get(game, 0) + 1
    update_user(uid, gstats=json.dumps(stats))

def check_achievements(uid, chat_id=None):
    user = get_user(uid)
    earned = set(json.loads(user['achs']))
    stats = json.loads(user.get('gstats', '{}'))
    
    new_achievements = []
    
    def check(ach_id, condition):
        if condition and ach_id not in earned:
            earned.add(ach_id)
            new_achievements.append(ach_id)
            reward = ACHIEVEMENTS[ach_id]['r']
            if reward:
                update_balance(uid, reward, f'Ачивка: {ACHIEVEMENTS[ach_id]["name"]}')
            if chat_id:
                try:
                    bot.send_message(chat_id,
                        f'🏅 *{escape_markdown(ACHIEVEMENTS[ach_id]["name"])}*\n'
                        f'💎 +{format_number(reward)} {CURRENCY}',
                        parse_mode='MarkdownV2')
                except:
                    pass
    
    check('first_game', user['games'] >= 1)
    check('games_10', user['games'] >= 10)
    check('games_100', user['games'] >= 100)
    check('games_1000', user['games'] >= 1000)
    check('win_streak_3', user['wstreak'] >= 3)
    check('win_streak_5', user['wstreak'] >= 5)
    check('win_streak_10', user['wstreak'] >= 10)
    check('daily_7', user['bstreak'] >= 7)
    check('daily_30', user['bstreak'] >= 30)
    check('rich_100k', user['balance'] >= 100000)
    check('loss_5_row', user['lstreak'] >= 5)
    check('referral_1', user['ref_cnt'] >= 1)
    check('referral_5', user['ref_cnt'] >= 5)
    check('level_10', user['level'] >= 10)
    check('level_50', user['level'] >= 50)
    check('slots_200', stats.get('slots', 0) >= 200)
    check('combo_5', user['combo'] >= 5)
    check('broke', user['balance'] == 0)
    
    all_games = {'slots','dice','darts','basketball','bowling','coin','blackjack','roulette','crash'}
    check('all_games', all_games.issubset(set(stats.keys())))
    
    if new_achievements:
        update_user(uid, achs=json.dumps(list(earned)))
    
    return new_achievements

def after_game(message, uid, bet, win, game, xp_base=15):
    user = get_user(uid)
    update_game_stat(uid, game)
    
    if win > 0:
        wstreak = user['wstreak'] + 1
        combo = min(user['combo'] + 1, 10) if wstreak >= 2 else 0
        update_user(uid,
            wstreak=wstreak,
            lstreak=0,
            combo=combo,
            maxstreak=max(user['maxstreak'], wstreak),
            won=user['won'] + win,
            games=user['games'] + 1,
            active=datetime.now().isoformat()
        )
    else:
        update_user(uid,
            wstreak=0,
            lstreak=user['lstreak'] + 1,
            combo=0,
            lost=user['lost'] + bet,
            games=user['games'] + 1,
            active=datetime.now().isoformat()
        )
    
    jp_contrib = int(bet * JACKPOT_CONTRIBUTION)
    if jp_contrib:
        add_to_jackpot(jp_contrib)
    
    add_history(uid, game, bet, win, (win/bet) if bet else 0)
    
    xp_total = xp_base + (get_user(uid)['wstreak'] * 3 if win > 0 else 1)
    new_level, leveled_up, level_reward = add_xp(uid, xp_total)
    
    if leveled_up:
        bot.send_message(message.chat.id,
            f'🎉 *УРОВЕНЬ {new_level}!* — {escape_markdown(get_level_name(new_level))}\n'
            f'💎 Награда: *+{format_number(level_reward)} {CURRENCY}*',
            parse_mode='MarkdownV2')
    
    user_after = get_user(uid)
    if user_after['combo'] in (3, 5, 7, 10) and win > 0:
        combo_names = {3:'🔥 КОМБО x3', 5:'⚡ КОМБО x5', 7:'💫 КОМБО x7', 10:'🌟 УЛЬТРА x10'}
        bot.send_message(message.chat.id,
            f'*{escape_markdown(combo_names[user_after["combo"]])}!*',
            parse_mode='MarkdownV2')
    
    check_achievements(uid, message.chat.id)

# ============================================================
# 🎨 КЛАВИАТУРЫ
# ============================================================
def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.add(
        KeyboardButton('🎰 Слоты'),
        KeyboardButton('🎲 Кости'),
        KeyboardButton('🎯 Дартс'),
        KeyboardButton('🏀 Баскет'),
        KeyboardButton('🎳 Боулинг'),
        KeyboardButton('🪙 Монетка'),
        KeyboardButton('🃏 Блэкджек'),
        KeyboardButton('🎡 Рулетка'),
        KeyboardButton('🚀 Краш'),
        KeyboardButton('📦 Кейсы'),
        KeyboardButton('💰 Баланс'),
        KeyboardButton('🎁 Бонус'),
        KeyboardButton('🏆 Топ'),
        KeyboardButton('📊 Профиль'),
        KeyboardButton('🛒 Магазин'),
        KeyboardButton('⚔️ Дуэль'),
        KeyboardButton('🏰 Кланы'),
        KeyboardButton('🎀 Подарок'),
        KeyboardButton('🏅 Ачивки'),
        KeyboardButton('📜 Помощь')
    )
    return kb

def bet_keyboard(game):
    kb = InlineKeyboardMarkup(row_width=4)
    bets = [10, 50, 100, 500, 1000, 5000, 10000]
    kb.add(*[InlineKeyboardButton(f'{format_number(b)} 💎', callback_data=f'bet_{game}_{b}') for b in bets])
    kb.add(InlineKeyboardButton('✏️ Своя ставка', callback_data=f'bet_{game}_custom'))
    return kb

# ============================================================
# 🎮 ОБЩИЙ ОБРАБОТЧИК СТАВОК
# ============================================================
def make_bet_handler(game_func, game_name):
    @bot.callback_query_handler(func=lambda c: c.data.startswith(f'bet_{game_name}_'))
    @anti_flood
    def handler(call):
        uid = call.from_user.id
        val = call.data.split('_')[2]
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        if val == 'custom':
            bot.send_message(call.message.chat.id,
                '✏️ Введи сумму ставки (1–10000):',
                parse_mode='MarkdownV2')
            bot.register_next_step_handler(call.message, lambda m: custom_bet(m, uid, game_func))
        else:
            game_func(call.message, uid, int(val))
    return handler

def custom_bet(message, uid, game_func):
    try:
        game_func(message, uid, int(message.text.strip()))
    except:
        bot.send_message(message.chat.id, '❌ Введи число!')

def check_bet(message, uid, bet):
    user = get_user(uid)
    if bet < MIN_BET or bet > MAX_BET:
        bot.send_message(message.chat.id,
            f'❌ Ставка от {MIN_BET} до {format_number(MAX_BET)} {CURRENCY}')
        return False
    if user['balance'] < bet:
        bot.send_message(message.chat.id,
            f'❌ Недостаточно монет! Баланс: *{format_number(user["balance"])} {CURRENCY}*',
            parse_mode='MarkdownV2')
        return False
    return True

# ============================================================
# 🎰 СЛОТЫ
# ============================================================
@bot.message_handler(func=lambda m: m.text == '🎰 Слоты')
@bot.message_handler(commands=['slot', 'slots'])
@anti_flood
def slots_menu(message):
    user = get_user(message.from_user.id)
    bot.send_message(message.chat.id,
        f'🎰 *СЛОТЫ* 🎰\n\n'
        f'💰 Джекпот: *{format_number(get_jackpot())} {CURRENCY}*\n\n'
        f'🏆 Выплаты:\n'
        f'  777 — весь Джекпот!\n'
        f'  BAR×3 — x50\n'
        f'  🍒×3 — x20\n'
        f'  🍋×3 — x10\n'
        f'  🍊×3 — x5\n'
        f'  🍉×3 — x3\n'
        f'  ⭐×3 — x2\n\n'
        f'💎 Баланс: *{format_number(user["balance"])} {CURRENCY}*\nВыбери ставку:',
        parse_mode='MarkdownV2',
        reply_markup=bet_keyboard('slots'))

def play_slots(message, uid, bet):
    if not check_bet(message, uid, bet):
        return
    
    update_balance(uid, -bet, 'Слоты ставка')
    dice_msg = bot.send_dice(message.chat.id, emoji='🎰')
    value = dice_msg.dice.value
    time.sleep(3.5)
    
    if value == 1:
        jackpot_amount = hit_jackpot(uid)
        win_amount = min(jackpot_amount, MAX_WIN)
        update_balance(uid, win_amount, 'ДЖЕКПОТ')
        bot.send_message(message.chat.id,
            f'🎰🎰🎰\n💎 *ДЖЕКПОТ — ТРИ СЕМЁРКИ!* 💎\n\n'
            f'🏆 Выигрыш: *+{format_number(win_amount)} {CURRENCY}!\n'
            f'💎 Баланс: *{format_number(get_balance(uid))} {CURRENCY}*',
            parse_mode='MarkdownV2')
        after_game(message, uid, bet, win_amount, 'slots', 100)
        
        user = get_user(uid)
        earned = set(json.loads(user['achs']))
        if 'jackpot' not in earned:
            earned.add('jackpot')
            update_user(uid, achs=json.dumps(list(earned)))
            bot.send_message(message.chat.id,
                f'🏅 *{escape_markdown(ACHIEVEMENTS["jackpot"]["name"])}*\n💎 +{ACHIEVEMENTS["jackpot"]["r"]} {CURRENCY}',
                parse_mode='MarkdownV2')
            update_balance(uid, ACHIEVEMENTS['jackpot']['r'], 'Ачивка джекпот')
    
    else:
        if value == 64:
            mult = 50
            result_text = '🥇🥇🥇 *BAR×3! x50*'
        elif value == 43:
            mult = 20
            result_text = '🍒🍒🍒 *Три вишни! x20*'
        elif value == 22:
            mult = 10
            result_text = '🍋🍋🍋 *Три лимона! x10*'
        elif value >= 55:
            mult = 5
            result_text = '🍊🍊🍊 *Тройка! x5*'
        elif value >= 40:
            mult = 3
            result_text = '🍉🍉🍉 *Хорошо! x3*'
        elif value >= 25:
            mult = 2
            result_text = '⭐⭐⭐ *Небольшой выигрыш! x2*'
        else:
            mult = 0
            result_text = '💔 *Не повезло...* Попробуй ещё!'
        
        if mult > 0:
            win_amount = min(bet * mult, MAX_WIN)
            update_balance(uid, win_amount, f'Слоты x{mult}')
            bot.send_message(message.chat.id,
                f'{result_text}\n\n💰 Ставка: {format_number(bet)} {CURRENCY}\n'
                f'🏆 *+{format_number(win_amount)} {CURRENCY}!*\n'
                f'💎 *{format_number(get_balance(uid))} {CURRENCY}*',
                parse_mode='MarkdownV2')
            after_game(message, uid, bet, win_amount, 'slots', 15)
        else:
            bot.send_message(message.chat.id,
                f'{result_text}\n\n💸 -{format_number(bet)} {CURRENCY}\n'
                f'💎 *{format_number(get_balance(uid))} {CURRENCY}*',
                parse_mode='MarkdownV2')
            after_game(message, uid, bet, 0, 'slots', 5)

make_bet_handler(play_slots, 'slots')

# ============================================================
# 🎲 КОСТИ
# ============================================================
@bot.message_handler(func=lambda m: m.text == '🎲 Кости')
@bot.message_handler(commands=['dice'])
@anti_flood
def dice_menu(message):
    user = get_user(message.from_user.id)
    bot.send_message(message.chat.id,
        f'🎲 *КОСТИ* 🎲\n\n'
        f'🏆 Выплаты:\n'
        f'  6 — *x6* 🎯\n'
        f'  5 — *x3*\n'
        f'  4 — *x2*\n'
        f'  1-3 — проигрыш\n\n'
        f'💎 Баланс: *{format_number(user["balance"])} {CURRENCY}*\n'
        f'Выбери ставку:',
        parse_mode='MarkdownV2',
        reply_markup=bet_keyboard('dice'))

def play_dice(message, uid, bet):
    if not check_bet(message, uid, bet):
        return
    
    update_balance(uid, -bet, 'Кости ставка')
    dice_msg = bot.send_dice(message.chat.id, emoji='🎲')
    value = dice_msg.dice.value
    time.sleep(3)
    
    if value == 6:
        mult = 6
        result_text = '🎯 *ШЕСТЁРКА! x6!*'
    elif value == 5:
        mult = 3
        result_text = '✨ *Пятёрка! x3!*'
    elif value == 4:
        mult = 2
        result_text = '👍 *Четвёрка! x2!*'
    else:
        mult = 0
        result_text = f'😔 *{value}... Не повезло!*'
    
    if mult > 0:
        win_amount = min(bet * mult, MAX_WIN)
        update_balance(uid, win_amount, f'Кости x{mult}')
        bot.send_message(message.chat.id,
            f'{result_text}\n\n🏆 *+{format_number(win_amount)} {CURRENCY}!*\n'
            f'💎 *{format_number(get_balance(uid))} {CURRENCY}*',
            parse_mode='MarkdownV2')
        after_game(message, uid, bet, win_amount, 'dice', 15)
    else:
        bot.send_message(message.chat.id,
            f'{result_text}\n\n💸 -{format_number(bet)} {CURRENCY}\n'
            f'💎 *{format_number(get_balance(uid))} {CURRENCY}*',
            parse_mode='MarkdownV2')
        after_game(message, uid, bet, 0, 'dice', 5)

make_bet_handler(play_dice, 'dice')

# ============================================================
# 🎯 ДАРТС
# ============================================================
@bot.message_handler(func=lambda m: m.text == '🎯 Дартс')
@bot.message_handler(commands=['darts'])
@anti_flood
def darts_menu(message):
    user = get_user(message.from_user.id)
    bot.send_message(message.chat.id,
        f'🎯 *ДАРТС* 🎯\n\n'
        f'🏆 Выплаты:\n'
        f'  🎯 Яблочко — *x10*\n'
        f'  💫 Двойное — *x5*\n'
        f'  ✨ Хорошо — *x3*\n'
        f'  ❌ Промах — проигрыш\n\n'
        f'💎 Баланс: *{format_number(user["balance"])} {CURRENCY}*\n'
        f'Выбери ставку:',
        parse_mode='MarkdownV2',
        reply_markup=bet_keyboard('darts'))

def play_darts(message, uid, bet):
    if not check_bet(message, uid, bet):
        return
    
    update_balance(uid, -bet, 'Дартс ставка')
    dice_msg = bot.send_dice(message.chat.id, emoji='🎯')
    value = dice_msg.dice.value
    time.sleep(3)
    
    if value == 1:
        mult = 10
        result_text = '🎯 *ЯБЛОЧКО! BULLSEYE! x10!*'
        is_bull = True
    elif value == 2:
        mult = 5
        result_text = '💫 *Двойное! x5!*'
        is_bull = False
    elif value in (3, 4, 5):
        mult = 3
        result_text = '✨ *Хороший бросок! x3!*'
        is_bull = False
    else:
        mult = 0
        result_text = '💨 *Промах!*'
        is_bull = False
    
    if mult > 0:
        win_amount = min(bet * mult, MAX_WIN)
        update_balance(uid, win_amount, f'Дартс x{mult}')
        bot.send_message(message.chat.id,
            f'{result_text}\n\n🏆 *+{format_number(win_amount)} {CURRENCY}!*\n'
            f'💎 *{format_number(get_balance(uid))} {CURRENCY}*',
            parse_mode='MarkdownV2')
        after_game(message, uid, bet, win_amount, 'darts', 15)
        
        if is_bull:
            user = get_user(uid)
            earned = set(json.loads(user['achs']))
            if 'darts_bull' not in earned:
                earned.add('darts_bull')
                update_user(uid, achs=json.dumps(list(earned)))
                bot.send_message(message.chat.id,
                    f'🏅 *{escape_markdown(ACHIEVEMENTS["darts_bull"]["name"])}*\n💎 +{ACHIEVEMENTS["darts_bull"]["r"]} {CURRENCY}',
                    parse_mode='MarkdownV2')
                update_balance(uid, ACHIEVEMENTS['darts_bull']['r'], 'Ачивка яблочко')
    else:
        bot.send_message(message.chat.id,
            f'{result_text}\n\n💸 -{format_number(bet)} {CURRENCY}\n'
            f'💎 *{format_number(get_balance(uid))} {CURRENCY}*',
            parse_mode='MarkdownV2')
        after_game(message, uid, bet, 0, 'darts', 5)

make_bet_handler(play_darts, 'darts')

# ============================================================
# 🏀 БАСКЕТБОЛ
# ============================================================
@bot.message_handler(func=lambda m: m.text == '🏀 Баскет')
@bot.message_handler(commands=['basketball', 'basket'])
@anti_flood
def basketball_menu(message):
    user = get_user(message.from_user.id)
    bot.send_message(message.chat.id,
        f'🏀 *БАСКЕТБОЛ* 🏀\n\n'
        f'🏆 Выплаты:\n'
        f'  🏀 Идеально — *x4*\n'
        f'  ✨ Попал — *x2*\n'
        f'  ❌ Промах — проигрыш\n\n'
        f'💎 Баланс: *{format_number(user["balance"])} {CURRENCY}*\n'
        f'Выбери ставку:',
        parse_mode='MarkdownV2',
        reply_markup=bet_keyboard('bball'))

def play_basketball(message, uid, bet):
    if not check_bet(message, uid, bet):
        return
    
    update_balance(uid, -bet, 'Баскет ставка')
    dice_msg = bot.send_dice(message.chat.id, emoji='🏀')
    value = dice_msg.dice.value
    time.sleep(3)
    
    if value == 4:
        mult = 4
        result_text = '🏀 *ИДЕАЛЬНЫЙ БРОСОК! SWISH! x4!* 🔥'
    elif value in (1, 2, 3):
        mult = 2
        result_text = '✨ *ПОПАДАНИЕ! x2!* 🏀'
    else:
        mult = 0
        result_text = '❌ *Промах!* Мяч мимо кольца'
    
    if mult > 0:
        win_amount = min(bet * mult, MAX_WIN)
        update_balance(uid, win_amount, f'Баскет x{mult}')
        bot.send_message(message.chat.id,
            f'{result_text}\n\n🏆 *+{format_number(win_amount)} {CURRENCY}!*\n'
            f'💎 *{format_number(get_balance(uid))} {CURRENCY}*',
            parse_mode='MarkdownV2')
        after_game(message, uid, bet, win_amount, 'basketball', 15)
    else:
        bot.send_message(message.chat.id,
            f'{result_text}\n\n💸 -{format_number(bet)} {CURRENCY}\n'
            f'💎 *{format_number(get_balance(uid))} {CURRENCY}*',
            parse_mode='MarkdownV2')
        after_game(message, uid, bet, 0, 'basketball', 5)

make_bet_handler(play_basketball, 'bball')

# ============================================================
# 🎳 БОУЛИНГ
# ============================================================
@bot.message_handler(func=lambda m: m.text == '🎳 Боулинг')
@bot.message_handler(commands=['bowling'])
@anti_flood
def bowling_menu(message):
    user = get_user(message.from_user.id)
    bot.send_message(message.chat.id,
        f'🎳 *БОУЛИНГ* 🎳\n\n'
        f'🏆 Выплаты:\n'
        f'  🎳 Страйк (6) — *x5*\n'
        f'  💫 Спэр (4-5) — *x2*\n'
        f'  👍 Нормально (2-3) — *x1.5*\n'
        f'  🏚️ Гэттер (1) — проигрыш\n\n'
        f'💎 Баланс: *{format_number(user["balance"])} {CURRENCY}*\n'
        f'Выбери ставку:',
        parse_mode='MarkdownV2',
        reply_markup=bet_keyboard('bowling'))

def play_bowling(message, uid, bet):
    if not check_bet(message, uid, bet):
        return
    
    update_balance(uid, -bet, 'Боулинг ставка')
    dice_msg = bot.send_dice(message.chat.id, emoji='🎳')
    value = dice_msg.dice.value
    time.sleep(3)
    
    if value == 6:
        mult = 5.0
        result_text = '🎳 *СТРАЙК! x5!* 🔥'
        is_strike = True
    elif value >= 4:
        mult = 2.0
        result_text = '💫 *Спэр! x2!*'
        is_strike = False
    elif value >= 2:
        mult = 1.5
        result_text = '👍 *Нормально! x1.5*'
        is_strike = False
    else:
        mult = 0.0
        result_text = '🏚️ *Гэттер! Мимо...!*'
        is_strike = False
    
    if mult > 0:
        win_amount = min(int(bet * mult), MAX_WIN)
        update_balance(uid, win_amount, f'Боулинг x{mult}')
        bot.send_message(message.chat.id,
            f'{result_text}\n\n🏆 *+{format_number(win_amount)} {CURRENCY}!*\n'
            f'💎 *{format_number(get_balance(uid))} {CURRENCY}*',
            parse_mode='MarkdownV2')
        after_game(message, uid, bet, win_amount, 'bowling', 15)
        
        if is_strike:
            user = get_user(uid)
            earned = set(json.loads(user['achs']))
            if 'bowling_strike' not in earned:
                earned.add('bowling_strike')
                update_user(uid, achs=json.dumps(list(earned)))
                bot.send_message(message.chat.id,
                    f'🏅 *{escape_markdown(ACHIEVEMENTS["bowling_strike"]["name"])}*\n💎 +{ACHIEVEMENTS["bowling_strike"]["r"]} {CURRENCY}',
                    parse_mode='MarkdownV2')
                update_balance(uid, ACHIEVEMENTS['bowling_strike']['r'], 'Ачивка страйк')
    else:
        bot.send_message(message.chat.id,
            f'{result_text}\n\n💸 -{format_number(bet)} {CURRENCY}\n'
            f'💎 *{format_number(get_balance(uid))} {CURRENCY}*',
            parse_mode='MarkdownV2')
        after_game(message, uid, bet, 0, 'bowling', 5)

make_bet_handler(play_bowling, 'bowling')

# ============================================================
# 🪙 МОНЕТКА
# ============================================================
@bot.message_handler(func=lambda m: m.text == '🪙 Монетка')
@bot.message_handler(commands=['coin', 'flip'])
@anti_flood
def coin_menu(message):
    user = get_user(message.from_user.id)
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton('🦅 Орёл', callback_data='coin_eagle'),
        InlineKeyboardButton('🪙 Решка', callback_data='coin_tails')
    )
    bot.send_message(message.chat.id,
        f'🪙 *ОРЁЛ или РЕШКА?* 🪙\n\n'
        f'Угадай — получи *x2!*\n\n'
        f'💎 Баланс: *{format_number(user["balance"])} {CURRENCY}*\n\n'
        f'Выбери сторону:',
        parse_mode='MarkdownV2',
        reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data in ('coin_eagle', 'coin_tails'))
@anti_flood
def coin_choice(call):
    uid = call.from_user.id
    choice = call.data.split('_')[1]
    coin_ch[uid] = choice
    choice_emoji = '🦅 Орёл' if choice == 'eagle' else '🪙 Решка'
    try:
        bot.edit_message_text(
            f'Ты выбрал: *{choice_emoji}*\n\nВведи сумму ставки:',
            call.message.chat.id,
            call.message.message_id,
            parse_mode='MarkdownV2'
        )
    except:
        pass
    bot.register_next_step_handler(call.message, process_coin)

def process_coin(message):
    uid = message.from_user.id
    if uid not in coin_ch:
        bot.send_message(message.chat.id, '❌ Сначала выбери сторону!')
        return
    
    try:
        bet = int(message.text.strip())
        user = get_user(uid)
        
        if bet < MIN_BET or bet > MAX_BET or user['balance'] < bet:
            bot.send_message(message.chat.id, '❌ Неверная ставка!')
            del coin_ch[uid]
            return
        
        choice = coin_ch.pop(uid)
        update_balance(uid, -bet, 'Монетка ставка')
        
        result = random.choice(['eagle', 'tails'])
        result_emoji = '🦅' if result == 'eagle' else '🪙'
        choice_emoji = '🦅' if choice == 'eagle' else '🪙'
        
        anim = bot.send_message(message.chat.id, '🪙 Монета летит....', parse_mode='MarkdownV2')
        time.sleep(1.5)
        try:
            bot.delete_message(message.chat.id, anim.message_id)
        except:
            pass
        
        if result == choice:
            win_amount = min(bet * 2, MAX_WIN)
            update_balance(uid, win_amount, 'Монетка x2')
            bot.send_message(message.chat.id,
                f'{result_emoji} *УГАДАЛ!*\n\n'
                f'🏆 *+{format_number(win_amount)} {CURRENCY}!*\n'
                f'💎 *{format_number(get_balance(uid))} {CURRENCY}*',
                parse_mode='MarkdownV2')
            after_game(message, uid, bet, win_amount, 'coin', 15)
        else:
            bot.send_message(message.chat.id,
                f'{result_emoji} *НЕ УГАДАЛ.* Выпало {result_emoji}, ты выбрал {choice_emoji}\n\n'
                f'💸 -{format_number(bet)} {CURRENCY}\n'
                f'💎 *{format_number(get_balance(uid))} {CURRENCY}*',
                parse_mode='MarkdownV2')
            after_game(message, uid, bet, 0, 'coin', 5)
            
    except ValueError:
        bot.send_message(message.chat.id, '❌ Введи число!')
        coin_ch.pop(uid, None)

# ============================================================
# 🚀 КРАШ
# ============================================================
def generate_crash_point():
    r = random.random()
    if r < 0.05:
        return round(random.uniform(1.0, 1.1), 2)
    elif r < 0.3:
        return round(random.uniform(1.1, 2.0), 2)
    elif r < 0.6:
        return round(random.uniform(2.0, 5.0), 2)
    elif r < 0.8:
        return round(random.uniform(5.0, 15.0), 2)
    elif r < 0.95:
        return round(random.uniform(15.0, 50.0), 2)
    else:
        return round(random.uniform(50.0, 200.0), 2)

@bot.message_handler(func=lambda m: m.text == '🚀 Краш')
@bot.message_handler(commands=['crash'])
@anti_flood
def crash_menu(message):
    user = get_user(message.from_user.id)
    bot.send_message(message.chat.id,
        f'🚀 *КРАШ-ИГРА* 🚀\n\n'
        f'Ракета взлетает и в любой момент может крашнуться!\n\n'
        f'📖 *Как играть:*\n'
        f'1. Введи ставку\n'
        f'2. Введи целевой множитель (1.1 — 1000)\n'
        f'3. Если не крашнется раньше — ты в плюсе!\n\n'
        f'💎 Баланс: *{format_number(user["balance"])} {CURRENCY}*\n\n'
        f'Введи ставку:',
        parse_mode='MarkdownV2')
    bot.register_next_step_handler(message, crash_get_bet)

def crash_get_bet(message):
    try:
        bet = int(message.text.strip())
        user = get_user(message.from_user.id)
        if bet < MIN_BET or bet > MAX_BET or user['balance'] < bet:
            bot.send_message(message.chat.id, '❌ Неверная ставка!')
            return
        bot.send_message(message.chat.id,
            f'🎯 Ставка: *{format_number(bet)} {CURRENCY}*\n\n'
            f'Введи целевой множитель (напр: 2.5, 10, 50):',
            parse_mode='MarkdownV2')
        bot.register_next_step_handler(message, lambda m: crash_get_target(m, bet))
    except ValueError:
        bot.send_message(message.chat.id, '❌ Введи число!')

def crash_get_target(message, bet):
    try:
        target = float(message.text.strip().replace(',', '.'))
        if target < 1.1 or target > 1000:
            bot.send_message(message.chat.id, '❌ Множитель 1.1–1000')
            return
        play_crash(message, message.from_user.id, bet, target)
    except ValueError:
        bot.send_message(message.chat.id, '❌ Введи число (напр: 2.5)')

def play_crash(message, uid, bet, target):
    update_balance(uid, -bet, 'Краш ставка')
    crash_point = generate_crash_point()
    
    crash_games[uid] = {
        'bet': bet,
        'target': target,
        'crash_point': crash_point,
        'cashed_out': False
    }
    
    anim = bot.send_message(message.chat.id,
        f'🚀 *РАКЕТА ЗАПУЩЕНА!*\n\n'
        f'💰 Ставка: *{format_number(bet)} {CURRENCY}*\n'
        f'🎯 Цель: *x{target}*\n\n'
        f'⚡ Ждём...',
        parse_mode='MarkdownV2')
    
    def crash_animation():
        current = 1.0
        step = 0.1 if crash_point < 5 else 0.5
        
        while current < crash_point:
            if crash_games.get(uid, {}).get('cashed_out'):
                return
            time.sleep(0.8)
            current = round(current + step, 2)
            if current >= crash_point:
                current = crash_point
                break
            try:
                bot.edit_message_text(
                    f'🚀 *КРАШ-ИГРА*\n\n'
                    f'💰 Ставка: *{format_number(bet)} {CURRENCY}*\n'
                    f'🎯 Цель: *x{target}*\n\n'
                    f'Множитель: *x{current:.2f}*\n'
                    f'Потенциал: *+{format_number(int(bet * current))} {CURRENCY}*\n\n'
                    f'⚡ Напиши /cashout чтобы вывести!',
                    message.chat.id, anim.message_id,
                    parse_mode='MarkdownV2')
            except:
                pass
        
        if not crash_games.get(uid, {}).get('cashed_out'):
            crash_games.pop(uid, None)
            try:
                bot.edit_message_text(
                    f'💥 *КРАШ на x{crash_point:.2f}!*\n\n'
                    f'😭 Ты не успел вывести!\n'
                    f'💸 -{format_number(bet)} {CURRENCY}\n'
                    f'💎 *{format_number(get_balance(uid))} {CURRENCY}*',
                    message.chat.id, anim.message_id,
                    parse_mode='MarkdownV2')
                after_game(message, uid, bet, 0, 'crash', 5)
            except:
                pass
    
    threading.Thread(target=crash_animation, daemon=True).start()

@bot.message_handler(commands=['cashout'])
@anti_flood
def crash_cashout(message):
    uid = message.from_user.id
    game = crash_games.get(uid)
    
    if not game or game['cashed_out']:
        bot.send_message(message.chat.id, '❌ У тебя нет активной игры в краш!')
        return
    
    game['cashed_out'] = True
    win_mult = min(game['target'], game['crash_point'] - 0.01)
    win_amount = min(int(game['bet'] * win_mult), MAX_WIN)
    
    update_balance(uid, win_amount, 'Краш выигрыш')
    after_game(message, uid, game['bet'], win_amount, 'crash', 20)
    
    if win_mult >= 10:
        user = get_user(uid)
        earned = set(json.loads(user['achs']))
        if 'crash_10x' not in earned:
            earned.add('crash_10x')
            update_user(uid, achs=json.dumps(list(earned)))
            bot.send_message(message.chat.id,
                f'🏅 *{escape_markdown(ACHIEVEMENTS["crash_10x"]["name"])}*\n💎 +{ACHIEVEMENTS["crash_10x"]["r"]} {CURRENCY}',
                parse_mode='MarkdownV2')
            update_balance(uid, ACHIEVEMENTS['crash_10x']['r'], 'Ачивка краш 10x')
    
    if win_mult >= 100:
        user = get_user(uid)
        earned = set(json.loads(user['achs']))
        if 'crash_100x' not in earned:
            earned.add('crash_100x')
            update_user(uid, achs=json.dumps(list(earned)))
            bot.send_message(message.chat.id,
                f'🏅 *{escape_markdown(ACHIEVEMENTS["crash_100x"]["name"])}*\n💎 +{ACHIEVEMENTS["crash_100x"]["r"]} {CURRENCY}',
                parse_mode='MarkdownV2')
            update_balance(uid, ACHIEVEMENTS['crash_100x']['r'], 'Ачивка краш 100x')
    
    crash_games.pop(uid, None)
    bot.send_message(message.chat.id,
        f'✅ *ВЫВЕЛ ВОВРЕМЯ!*\n\n'
        f'📈 Множитель: *x{win_mult:.2f}*\n'
        f'💰 Выигрыш: *+{format_number(win_amount)} {CURRENCY}*\n'
        f'💎 Баланс: *{format_number(get_balance(uid))} {CURRENCY}*',
        parse_mode='MarkdownV2')

# ============================================================
# 🎡 РУЛЕТКА
# ============================================================
ROULETTE_COLORS = {
    0: 'g', 1: 'r', 2: 'b', 3: 'r', 4: 'b', 5: 'r', 6: 'b', 7: 'r', 8: 'b', 9: 'r', 10: 'b',
    11: 'b', 12: 'r', 13: 'b', 14: 'r', 15: 'b', 16: 'r', 17: 'b', 18: 'r', 19: 'r', 20: 'b',
    21: 'r', 22: 'b', 23: 'r', 24: 'b', 25: 'r', 26: 'b', 27: 'r', 28: 'b', 29: 'b', 30: 'r',
    31: 'b', 32: 'r', 33: 'b', 34: 'r', 35: 'b', 36: 'r'
}

def roulette_color_emoji(num):
    if num == 0:
        return '🟢'
    return '🔴' if ROULETTE_COLORS[num] == 'r' else '⚫'

@bot.message_handler(func=lambda m: m.text == '🎡 Рулетка')
@bot.message_handler(commands=['roulette'])
@anti_flood
def roulette_menu(message):
    user = get_user(message.from_user.id)
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton('🔴 Красное (x2)', callback_data='rl_red'),
        InlineKeyboardButton('⚫ Чёрное (x2)', callback_data='rl_black'),
        InlineKeyboardButton('🟢 Зеро (x36)', callback_data='rl_zero'),
        InlineKeyboardButton('🔢 Чётное (x2)', callback_data='rl_even'),
        InlineKeyboardButton('🔢 Нечётное (x2)', callback_data='rl_odd'),
        InlineKeyboardButton('⬇️ 1–18 (x2)', callback_data='rl_low'),
        InlineKeyboardButton('⬆️ 19–36 (x2)', callback_data='rl_high'),
        InlineKeyboardButton('🎯 Число 0–36 (x36)', callback_data='rl_number'),
        InlineKeyboardButton('🎰 Дюжина 1/2/3 (x3)', callback_data='rl_dozen'),
    )
    bot.send_message(message.chat.id,
        f'🎡 *ЕВРОПЕЙСКАЯ РУЛЕТКА* 🎡\n\n'
        f'Числа: 0–36\n'
        f'🔴 17 красных  ⚫ 18 чёрных  🟢 1 зелёное\n\n'
        f'💎 Баланс: *{format_number(user["balance"])} {CURRENCY}*\n\n'
        f'Выбери тип ставки:',
        parse_mode='MarkdownV2',
        reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('rl_'))
@anti_flood
def roulette_type(call):
    uid = call.from_user.id
    bet_type = call.data[3:]
    roulette_bets[uid] = {'type': bet_type}
    
    type_names = {
        'red': '🔴 Красное',
        'black': '⚫ Чёрное',
        'zero': '🟢 Зеро',
        'even': 'Чётное',
        'odd': 'Нечётное',
        'low': '1–18',
        'high': '19–36',
        'number': 'Число (0–36)',
        'dozen': 'Дюжина (1/2/3)'
    }
    
    if bet_type == 'number':
        bot.edit_message_text(
            'Введи: *СТАВКА ЧИСЛО* (напр: `500 17`)',
            call.message.chat.id, call.message.message_id,
            parse_mode='MarkdownV2')
    elif bet_type == 'dozen':
        bot.edit_message_text(
            'Введи: *СТАВКА ДЮЖИНА* (1=1–12, 2=13–24, 3=25–36). Напр: `500 2`',
            call.message.chat.id, call.message.message_id,
            parse_mode='MarkdownV2')
    else:
        bot.edit_message_text(
            f'Ставка на *{type_names.get(bet_type, bet_type)}*\n\nВведи сумму ставки:',
            call.message.chat.id, call.message.message_id,
            parse_mode='MarkdownV2')
    
    bot.register_next_step_handler(call.message, process_roulette)

def process_roulette(message):
    uid = message.from_user.id
    if uid not in roulette_bets:
        bot.send_message(message.chat.id, '❌ Начни заново!')
        return
    
    bet_data = roulette_bets.pop(uid)
    bet_type = bet_data['type']
    
    try:
        parts = message.text.strip().split()
        bet = int(parts[0])
        extra = None
        
        if bet_type == 'number':
            if len(parts) < 2:
                bot.send_message(message.chat.id, '❌ Введи: СТАВКА ЧИСЛО')
                return
            extra = int(parts[1])
            if extra < 0 or extra > 36:
                bot.send_message(message.chat.id, '❌ Число 0–36')
                return
        elif bet_type == 'dozen':
            if len(parts) < 2:
                bot.send_message(message.chat.id, '❌ Введи: СТАВКА ДЮЖИНА')
                return
            extra = int(parts[1])
            if extra not in (1, 2, 3):
                bot.send_message(message.chat.id, '❌ Дюжина 1, 2 или 3')
                return
        
        user = get_user(uid)
        if bet < MIN_BET or bet > MAX_BET or user['balance'] < bet:
            bot.send_message(message.chat.id, '❌ Неверная ставка!')
            return
        
        spin_roulette(message, uid, bet, bet_type, extra)
        
    except (ValueError, IndexError):
        bot.send_message(message.chat.id, '❌ Неверный формат!')

def spin_roulette(message, uid, bet, bet_type, extra):
    update_balance(uid, -bet, 'Рулетка ставка')
    anim = bot.send_message(message.chat.id, '🎡 Шарик катится....', parse_mode='MarkdownV2')
    
    result = random.randint(0, 36)
    color = ROULETTE_COLORS.get(result, 'g')
    color_emoji = roulette_color_emoji(result)
    
    preview_numbers = [random.randint(0, 36) for _ in range(4)] + [result]
    for num in preview_numbers[:-1]:
        time.sleep(0.35)
        try:
            bot.edit_message_text(
                f'🎡 {roulette_color_emoji(num)} *{num}*',
                anim.message.chat.id, anim.message_id,
                parse_mode='MarkdownV2')
        except:
            pass
    time.sleep(0.8)
    
    multiplier = 0
    won = False
    
    if bet_type == 'red' and color == 'r':
        multiplier = 2
        won = True
    elif bet_type == 'black' and color == 'b':
        multiplier = 2
        won = True
    elif bet_type == 'zero' and result == 0:
        multiplier = 36
        won = True
    elif bet_type == 'even' and result > 0 and result % 2 == 0:
        multiplier = 2
        won = True
    elif bet_type == 'odd' and result > 0 and result % 2 == 1:
        multiplier = 2
        won = True
    elif bet_type == 'low' and 1 <= result <= 18:
        multiplier = 2
        won = True
    elif bet_type == 'high' and 19 <= result <= 36:
        multiplier = 2
        won = True
    elif bet_type == 'number' and result == extra:
        multiplier = 36
        won = True
    elif bet_type == 'dozen':
        dozens = {1: range(1, 13), 2: range(13, 25), 3: range(25, 37)}
        if result in dozens.get(extra, []):
            multiplier = 3
            won = True
    
    if result == 0 and bet_type != 'zero':
        won = False
        multiplier = 0
    
    if won:
        win_amount = min(bet * multiplier, MAX_WIN)
        update_balance(uid, win_amount, f'Рулетка x{multiplier}')
        try:
            bot.edit_message_text(
                f'🎡 *РЕЗУЛЬТАТ:* {color_emoji} *{result}*\n\n'
                f'✅ *ВЫИГРЫШ! x{multiplier}*\n\n'
                f'🏆 *+{format_number(win_amount)} {CURRENCY}!*\n'
                f'💎 *{format_number(get_balance(uid))} {CURRENCY}*',
                message.chat.id, anim.message_id,
                parse_mode='MarkdownV2')
        except:
            pass
        after_game(message, uid, bet, win_amount, 'roulette', 20)
        
        if result == 0:
            user = get_user(uid)
            earned = set(json.loads(user['achs']))
            if 'roulette_0' not in earned:
                earned.add('roulette_0')
                update_user(uid, achs=json.dumps(list(earned)))
                bot.send_message(message.chat.id,
                    f'🏅 *{escape_markdown(ACHIEVEMENTS["roulette_0"]["name"])}*\n💎 +{ACHIEVEMENTS["roulette_0"]["r"]} {CURRENCY}',
                    parse_mode='MarkdownV2')
                update_balance(uid, ACHIEVEMENTS['roulette_0']['r'], 'Ачивка зеро')
    else:
        try:
            bot.edit_message_text(
                f'🎡 *РЕЗУЛЬТАТ:* {color_emoji} *{result}*\n\n'
                f'❌ *ПРОИГРЫШ*\n\n'
                f'💸 -{format_number(bet)} {CURRENCY}\n'
                f'💎 *{format_number(get_balance(uid))} {CURRENCY}*',
                message.chat.id, anim.message_id,
                parse_mode='MarkdownV2')
        except:
            pass
        after_game(message, uid, bet, 0, 'roulette', 5)

# ============================================================
# 🃏 БЛЭКДЖЕК
# ============================================================
SUITS = ['♠️', '♥️', '♦️', '♣️']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

def card_value(rank):
    if rank in ('J', 'Q', 'K'):
        return 10
    if rank == 'A':
        return 11
    return int(rank)

def hand_value(hand):
    total = sum(card_value(rank) for rank, _ in hand)
    aces = sum(1 for rank, _ in hand if rank == 'A')
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

def hand_string(hand):
    return '  '.join(f'{rank}{suit}' for rank, suit in hand)

def new_deck():
    deck = [(rank, suit) for rank in RANKS for suit in SUITS]
    random.shuffle(deck)
    return deck

@bot.message_handler(func=lambda m: m.text == '🃏 Блэкджек')
@bot.message_handler(commands=['blackjack', 'bj'])
@anti_flood
def blackjack_menu(message):
    uid = message.from_user.id
    if uid in bj_games:
        bot.send_message(message.chat.id, '❌ У тебя активная игра! Используй кнопки.')
        return
    
    user = get_user(uid)
    bot.send_message(message.chat.id,
        f'🃏 *БЛЭКДЖЕК* 🃏\n\n'
        f'📖 Правила:\n'
        f'• Набери 21 или ближе чем дилер\n'
        f'• Туз=11 или 1\n'
        f'• J,Q,K=10\n'
        f'• Блэкджек=x2.5!\n\n'
        f'💎 Баланс: *{format_number(user["balance"])} {CURRENCY}*\n'
        f'Введи ставку:',
        parse_mode='MarkdownV2')
    bot.register_next_step_handler(message, blackjack_bet)

def blackjack_bet(message):
    uid = message.from_user.id
    try:
        bet = int(message.text.strip())
        user = get_user(uid)
        if bet < MIN_BET or bet > MAX_BET or user['balance'] < bet:
            bot.send_message(message.chat.id, '❌ Неверная ставка!')
            return
        
        update_balance(uid, -bet, 'Блэкджек ставка')
        deck = new_deck()
        player = [deck.pop(), deck.pop()]
        dealer = [deck.pop(), deck.pop()]
        
        bj_games[uid] = {
            'deck': deck,
            'player': player,
            'dealer': dealer,
            'bet': bet
        }
        
        if hand_value(player) == 21:
            blackjack_finish(message, uid, 'blackjack')
            return
        
        send_blackjack(message, uid)
        
    except ValueError:
        bot.send_message(message.chat.id, '❌ Введи число!')

def send_blackjack(message, uid):
    game = bj_games.get(uid)
    if not game:
        return
    
    player_value = hand_value(game['player'])
    dealer_show = f'{game["dealer"][0][0]}{game["dealer"][0][1]}  🂠'
    
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton('🃏 Ещё', callback_data='bj_hit'),
        InlineKeyboardButton('✋ Стоп', callback_data='bj_stand'),
        InlineKeyboardButton('💰 Удвоить', callback_data='bj_double')
    )
    
    text = (f'🃏 *БЛЭКДЖЕК* 🃏\n\n'
            f'🤖 Дилер: `{dealer_show}`\n\n'
            f'👤 Ты: `{hand_string(game["player"])}` = *{player_value}*\n\n'
            f'💰 Ставка: *{format_number(game["bet"])} {CURRENCY}*')
    
    if player_value > 21:
        blackjack_finish(message, uid, 'bust')
    else:
        try:
            bot.send_message(message.chat.id, text, parse_mode='MarkdownV2', reply_markup=kb)
        except:
            bot.send_message(message.chat.id,
                f'Твои карты: {hand_string(game["player"])}, очков: {player_value}',
                reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data in ('bj_hit', 'bj_stand', 'bj_double'))
@anti_flood
def blackjack_action(call):
    uid = call.from_user.id
    game = bj_games.get(uid)
    if not game:
        bot.answer_callback_query(call.id, 'Нет активной игры!')
        return
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    action = call.data[3:]
    
    if action == 'hit':
        game['player'].append(game['deck'].pop())
        player_value = hand_value(game['player'])
        if player_value > 21:
            blackjack_finish(call.message, uid, 'bust')
        elif player_value == 21:
            blackjack_finish(call.message, uid, 'stand')
        else:
            send_blackjack(call.message, uid)
    
    elif action == 'stand':
        blackjack_finish(call.message, uid, 'stand')
    
    elif action == 'double':
        user = get_user(uid)
        if user['balance'] < game['bet']:
            bot.send_message(call.message.chat.id, '❌ Нет монет для удвоения!')
            send_blackjack(call.message, uid)
            return
        update_balance(uid, -game['bet'], 'Удвоение блэкджек')
        game['bet'] *= 2
        game['player'].append(game['deck'].pop())
        blackjack_finish(call.message, uid, 'stand')

def blackjack_finish(message, uid, reason):
    game = bj_games.pop(uid, None)
    if not game:
        return
    
    player_value = hand_value(game['player'])
    
    if reason != 'bust':
        while hand_value(game['dealer']) < 17:
            game['dealer'].append(game['deck'].pop())
    
    dealer_value = hand_value(game['dealer'])
    bet = game['bet']
    win = 0
    
    if reason == 'blackjack':
        win = int(bet * 2.5)
        result_text = '🃏 *БЛЭКДЖЕК! x2.5!*'
    elif reason == 'bust':
        result_text = f'💥 *ПЕРЕБОР ({player_value})*'
    elif dealer_value > 21:
        win = bet * 2
        result_text = f'🎉 *Дилер перебрал ({dealer_value})! Ты победил!*'
    elif player_value > dealer_value:
        win = bet * 2
        result_text = f'✅ *Ты победил! {player_value} > {dealer_value}*'
    elif player_value == dealer_value:
        win = bet
        result_text = f'🤝 *Ничья! {player_value} = {dealer_value}*'
    else:
        result_text = f'❌ *Дилер победил! {dealer_value} > {player_value}*'
    
    if win:
        win = min(win, MAX_WIN)
        update_balance(uid, win, 'Блэкджек выигрыш')
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton('🃏 Ещё раз', callback_data='bj_replay'))
    
    try:
        bot.send_message(message.chat.id,
            f'🃏 *КОНЕЦ ИГРЫ* 🃏\n\n'
            f'🤖 Дилер: `{hand_string(game["dealer"])}` = *{dealer_value}*\n'
            f'👤 Ты: `{hand_string(game["player"])}` = *{player_value}*\n\n'
            f'{result_text}\n\n'
            f'{"🏆 +" + format_number(win) + " " + CURRENCY if win > 0 else "💸 -" + format_number(bet) + " " + CURRENCY}\n'
            f'💎 *{format_number(get_balance(uid))} {CURRENCY}*',
            parse_mode='MarkdownV2',
            reply_markup=kb)
    except:
        bot.send_message(message.chat.id,
            f'Игра окончена. {"Выигрыш: +" + str(win) if win else "Проигрыш"}')
    
    after_game(message, uid, bet, win - bet if win > 0 else 0, 'blackjack', 25)
    
    if reason == 'blackjack':
        user = get_user(uid)
        earned = set(json.loads(user['achs']))
        if 'blackjack_21' not in earned:
            earned.add('blackjack_21')
            update_user(uid, achs=json.dumps(list(earned)))
            bot.send_message(message.chat.id,
                f'🏅 *{escape_markdown(ACHIEVEMENTS["blackjack_21"]["name"])}*\n💎 +{ACHIEVEMENTS["blackjack_21"]["r"]} {CURRENCY}',
                parse_mode='MarkdownV2')
            update_balance(uid, ACHIEVEMENTS['blackjack_21']['r'], 'Ачивка блэкджек')

@bot.callback_query_handler(func=lambda c: c.data == 'bj_replay')
@anti_flood
def blackjack_replay(call):
    blackjack_menu(call.message)

# ============================================================
# 📦 КЕЙСЫ
# ============================================================
@bot.message_handler(func=lambda m: m.text == '📦 Кейсы')
@bot.message_handler(commands=['cases'])
@anti_flood
def cases_menu(message):
    user = get_user(message.from_user.id)
    kb = InlineKeyboardMarkup(row_width=1)
    for case_id, case_data in CASES.items():
        kb.add(InlineKeyboardButton(
            f'{case_data["name"]} — {format_number(case_data["price"])} {CURRENCY}',
            callback_data=f'case_{case_id}'))
    
    bot.send_message(message.chat.id,
        f'📦 *КЕЙСЫ* 📦\n\n'
        f'Открывай кейсы и выигрывай монеты!\n\n'
        f'💎 Баланс: *{format_number(user["balance"])} {CURRENCY}*\n\n'
        f'Выбери кейс:',
        parse_mode='MarkdownV2',
        reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('case_'))
@anti_flood
def open_case(call):
    uid = call.from_user.id
    case_id = call.data[5:]
    case_data = CASES.get(case_id)
    
    if not case_data:
        return
    
    user = get_user(uid)
    if user['balance'] < case_data['price']:
        bot.answer_callback_query(call.id,
            f'❌ Нужно {format_number(case_data["price"])} {CURRENCY}!',
            show_alert=True)
        return
    
    update_balance(uid, -case_data['price'], f'Кейс {case_id}')
    
    prizes = [p for p, _ in case_data['prizes']]
    weights = [w for _, w in case_data['prizes']]
    total_weight = sum(weights)
    norm_weights = [w / total_weight for w in weights]
    
    prize = min(random.choices(prizes, weights=norm_weights, k=1)[0], MAX_WIN)
    
    if is_weekend():
        prize = int(prize * WEEKEND_MULTIPLIER)
    
    update_balance(uid, prize, f'Приз кейс {case_id}')
    
    anim = bot.send_message(call.message.chat.id, f'📦 Открываем....', parse_mode='MarkdownV2')
    
    for _ in range(4):
        time.sleep(0.5)
        try:
            bot.edit_message_text(
                f'📦 🎲 *{format_number(random.choice(prizes))} {CURRENCY}*...',
                call.message.chat.id, anim.message_id,
                parse_mode='MarkdownV2')
        except:
            pass
    
    time.sleep(0.7)
    
    prize_percent = dict(zip(prizes, weights)).get(prize, 0) / total_weight * 100
    if prize_percent < 1:
        rarity = '🌟 ЛЕГЕНДАРНЫЙ'
    elif prize_percent < 5:
        rarity = '💎 ЭПИЧЕСКИЙ'
    elif prize_percent < 15:
        rarity = '🔵 РЕДКИЙ'
    else:
        rarity = '⚪ ОБЫЧНЫЙ'
    
    try:
        bot.edit_message_text(
            f'📦 *КЕЙС ОТКРЫТ!*\n\n'
            f'{case_data["name"]}\n\n'
            f'{rarity}\n'
            f'💰 *+{format_number(prize)} {CURRENCY}!*\n\n'
            f'💎 *{format_number(get_balance(uid))} {CURRENCY}*',
            call.message.chat.id, anim.message_id,
            parse_mode='MarkdownV2')
    except:
        pass
    
    user = get_user(uid)
    earned = set(json.loads(user['achs']))
    
    if 'opened_case' not in earned:
        earned.add('opened_case')
        update_user(uid, achs=json.dumps(list(earned)))
        bot.send_message(call.message.chat.id,
            f'🏅 *{escape_markdown(ACHIEVEMENTS["opened_case"]["name"])}*\n💎 +{ACHIEVEMENTS["opened_case"]["r"]} {CURRENCY}',
            parse_mode='MarkdownV2')
        update_balance(uid, ACHIEVEMENTS['opened_case']['r'], 'Ачивка открытие кейса')
    
    update_game_stat(uid, 'cases')
    
    cases_opened = json.loads(get_user(uid).get('gstats', '{}')).get('cases', 0)
    if cases_opened >= 10 and 'opened_10' not in earned:
        earned.add('opened_10')
        update_user(uid, achs=json.dumps(list(earned)))
        bot.send_message(call.message.chat.id,
            f'🏅 *{escape_markdown(ACHIEVEMENTS["opened_10"]["name"])}*\n💎 +{ACHIEVEMENTS["opened_10"]["r"]} {CURRENCY}',
            parse_mode='MarkdownV2')
        update_balance(uid, ACHIEVEMENTS['opened_10']['r'], 'Ачивка 10 кейсов')
    
    after_game(call.message, uid, case_data['price'], prize - case_data['price'], 'cases', 15)

# ============================================================
# 💰 БАЛАНС
# ============================================================
@bot.message_handler(func=lambda m: m.text == '💰 Баланс')
@bot.message_handler(commands=['balance'])
@anti_flood
def balance_command(message):
    user = get_user(message.from_user.id)
    bot.send_message(message.chat.id,
        f'💰 *БАЛАНС* 💰\n\n'
        f'💎 *{format_number(user["balance"])} {CURRENCY}*\n\n'
        f'✅ Выиграно: {format_number(user["won"])} {CURRENCY}\n'
        f'❌ Проиграно: {format_number(user["lost"])} {CURRENCY}\n'
        f'🎮 Игр: {format_number(user["games"])}\n\n'
        f'🎰 Джекпот: *{format_number(get_jackpot())} {CURRENCY}*',
        parse_mode='MarkdownV2',
        reply_markup=main_keyboard())

# ============================================================
# 📊 ПРОФИЛЬ
# ============================================================
@bot.message_handler(func=lambda m: m.text == '📊 Профиль')
@bot.message_handler(commands=['profile'])
@anti_flood
def profile_command(message):
    uid = message.from_user.id
    user = get_user(uid)
    bot_info = bot.get_me()
    
    earned_achs = set(json.loads(user['achs']))
    
    next_levels = [lvl for lvl in sorted(LEVELS) if LEVELS[lvl]['xp'] > user['xp']]
    if next_levels:
        next_xp = LEVELS[next_levels[0]]['xp']
        progress = min(user['xp'] / next_xp, 1.0)
    else:
        next_xp = 0
        progress = 1.0
    
    bar = '█' * int(10 * progress) + '░' * (10 - int(10 * progress))
    
    ref_link = f'https://t.me/{bot_info.username}?start=ref_{uid}'
    
    name = f'{user.get("skin", "")} {user["fname"]} {user.get("badge", "")}'.strip()
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton('🏅 Ачивки', callback_data='profile_achs'),
        InlineKeyboardButton('📜 История', callback_data='profile_history'),
        InlineKeyboardButton('👕 Скины', callback_data='profile_skins'),
        InlineKeyboardButton('👥 Рефералы', callback_data='profile_refs'),
    )
    
    bot.send_message(message.chat.id,
        f'📊 *ПРОФИЛЬ* 📊\n\n'
        f'👤 *{escape_markdown(name)}*  `{uid}`\n\n'
        f'💎 Баланс: *{format_number(user["balance"])} {CURRENCY}*\n'
        f'⭐ Уровень: *{user["level"]}* — {escape_markdown(get_level_name(user["level"]))}\n'
        f'📈 XP: *{format_number(user["xp"])}* [{bar}]\n'
        f'{"До следующего: " + format_number(next_xp - user["xp"]) + " XP" if next_xp else "Макс уровень!"}\n\n'
        f'🏆 Выиграно: *{format_number(user["won"])} {CURRENCY}*\n'
        f'📉 Проиграно: *{format_number(user["lost"])} {CURRENCY}*\n'
        f'🎮 Игр: *{format_number(user["games"])}*\n'
        f'🔥 Стрик: *{user["wstreak"]}* побед подряд\n'
        f'📅 Дней подряд: *{user["bstreak"]}*\n'
        f'🏅 Ачивок: *{len(earned_achs)}/{len(ACHIEVEMENTS)}*\n'
        f'👥 Рефералов: *{user["ref_cnt"]}*\n\n'
        f'🔗 Реф ссылка:\n`{ref_link}`',
        parse_mode='MarkdownV2',
        reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('profile_'))
@anti_flood
def profile_callbacks(call):
    uid = call.from_user.id
    action = call.data[8:]
    
    if action == 'achs':
        user = get_user(uid)
        earned = set(json.loads(user['achs']))
        text = f'🏅 *ДОСТИЖЕНИЯ* — {len(earned)}/{len(ACHIEVEMENTS)}\n\n'
        
        for ach_id, ach_data in ACHIEVEMENTS.items():
            status = '✅' if ach_id in earned else '🔒'
            text += f'{status} {escape_markdown(ach_data["name"])} — _{escape_markdown(ach_data["desc"])}_\n'
            if len(text) > 3500:
                text += '\n...ещё больше!'
                break
        
        bot.send_message(call.message.chat.id, text, parse_mode='MarkdownV2')
    
    elif action == 'history':
        conn = get_db()
        rows = conn.execute(
            'SELECT * FROM history WHERE uid=? ORDER BY ts DESC LIMIT 15',
            (uid,)
        ).fetchall()
        conn.close()
        
        if not rows:
            bot.answer_callback_query(call.id, 'Нет истории!')
            return
        
        game_emojis = {
            'slots': '🎰', 'dice': '🎲', 'darts': '🎯', 'basketball': '🏀',
            'bowling': '🎳', 'coin': '🪙', 'blackjack': '🃏', 'roulette': '🎡',
            'crash': '🚀', 'cases': '📦'
        }
        
        text = '📜 *ИСТОРИЯ ИГР* (последние 15)\n\n'
        for row in rows:
            emoji = game_emojis.get(row['game'], '🎮')
            result_icon = '✅' if row['result'] > 0 else '❌'
            result_str = f'+{format_number(row["result"])}' if row['result'] > 0 else f'-{format_number(row["bet"])}'
            text += f'{result_icon} {emoji} {escape_markdown(row["game"])} | {format_number(row["bet"])} → {result_str} {CURRENCY}\n'
        
        bot.send_message(call.message.chat.id, text, parse_mode='MarkdownV2')
    
    elif action == 'skins':
        user = get_user(uid)
        inventory = json.loads(user.get('inv', '{}'))
        
        if not inventory:
            bot.answer_callback_query(call.id, 'Нет предметов! Зайди в 🛒 Магазин')
            return
        
        kb = InlineKeyboardMarkup(row_width=1)
        for item_id in inventory:
            if item_id in SHOP:
                kb.add(InlineKeyboardButton(
                    f'👕 {SHOP[item_id]["name"]}',
                    callback_data=f'equip_{item_id}'))
        
        bot.send_message(call.message.chat.id, '👕 *МОИ ПРЕДМЕТЫ*', parse_mode='MarkdownV2', reply_markup=kb)
    
    elif action == 'refs':
        user = get_user(uid)
        bot_info = bot.get_me()
        bot.send_message(call.message.chat.id,
            f'👥 *РЕФЕРАЛЬНАЯ СИСТЕМА*\n\n'
            f'Приглашено: *{user["ref_cnt"]}* друзей\n\n'
            f'Друг получает: *{REFERRAL_FRIEND} {CURRENCY}*\n'
            f'Ты получаешь: *{REFERRAL_OWNER} {CURRENCY}*\n\n'
            f'🔗 Твоя ссылка:\n`https://t.me/{bot_info.username}?start=ref_{uid}`',
            parse_mode='MarkdownV2')

# ============================================================
# 🎁 БОНУС
# ============================================================
@bot.message_handler(func=lambda m: m.text == '🎁 Бонус')
@bot.message_handler(commands=['bonus'])
@anti_flood
def bonus_command(message):
    uid = message.from_user.id
    user = get_user(uid)
    now = datetime.now()
    
    if user['last_bonus']:
        last = datetime.fromisoformat(user['last_bonus'])
        diff = now - last
        if diff < timedelta(hours=24):
            remaining = timedelta(hours=24) - diff
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            bot.send_message(message.chat.id,
                f'⏰ Следующий бонус через *{hours}ч {minutes}м*\n'
                f'📅 Стрик: *{user["bstreak"]}* дней',
                parse_mode='MarkdownV2')
            return
        
        new_streak = user['bstreak'] + 1 if diff < timedelta(hours=48) else 1
    else:
        new_streak = 1
    
    base_bonus = random.randint(100, 500)
    multiplier = min(new_streak, 7)
    bonus = base_bonus * multiplier
    
    inventory = json.loads(user.get('inv', '{}'))
    if 'bonus_50' in inventory:
        bonus = int(bonus * 1.5)
    
    update_balance(uid, bonus, 'Ежедневный бонус')
    update_user(uid, last_bonus=now.isoformat(), bstreak=new_streak)
    
    streak_emojis = ['', '⭐', '⭐⭐', '🌟', '🌟🌟', '💫', '💫💫', '🏆']
    
    bot.send_message(message.chat.id,
        f'🎁 *ЕЖЕДНЕВНЫЙ БОНУС!* 🎁\n\n'
        f'{streak_emojis[min(new_streak, 7)]} Стрик: *{new_streak}* дней (×{multiplier})\n'
        f'💰 Базовый: {base_bonus} {CURRENCY}\n'
        f'💎 Итого: *+{format_number(bonus)} {CURRENCY}!*\n\n'
        f'Новый баланс: *{format_number(get_balance(uid))} {CURRENCY}*',
        parse_mode='MarkdownV2',
        reply_markup=main_keyboard())
    
    check_achievements(uid, message.chat.id)
    add_xp(uid, 10)

# ============================================================
# 🏆 ТОП
# ============================================================
@bot.message_handler(func=lambda m: m.text == '🏆 Топ')
@bot.message_handler(commands=['top'])
@anti_flood
def top_command(message):
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton('💎 Баланс', callback_data='top_balance'),
        InlineKeyboardButton('🏆 Выигрыши', callback_data='top_won'),
        InlineKeyboardButton('🎮 Игры', callback_data='top_games'),
        InlineKeyboardButton('📅 Стрик', callback_data='top_streak'),
        InlineKeyboardButton('⭐ Уровень', callback_data='top_level'),
    )
    bot.send_message(message.chat.id,
        '🏆 *ТОП ИГРОКОВ* 🏆\n\nВыбери категорию:',
        parse_mode='MarkdownV2',
        reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('top_'))
@anti_flood
def show_top(call):
    category = call.data[4:]
    
    categories = {
        'balance': ('balance', 'Баланс', '💎'),
        'won': ('won', 'Выигрыши', '🏆'),
        'games': ('games', 'Игр', '🎮'),
        'streak': ('bstreak', 'Дней подряд', '📅'),
        'level': ('level', 'Уровень', '⭐'),
    }
    
    field, title, emoji = categories.get(category, ('balance', 'Баланс', '💎'))
    
    conn = get_db()
    rows = conn.execute(
        f'SELECT uid, fname, {field}, badge FROM users ORDER BY {field} DESC LIMIT 10'
    ).fetchall()
    conn.close()
    
    medals = ['🥇', '🥈', '🥉'] + ['▫️'] * 7
    text = f'🏆 *ТОП 10 — {emoji} {title}* 🏆\n\n'
    
    for i, player in enumerate(rows):
        name = player['fname'] or f'Игрок{str(player["uid"])[-4:]}'
        badge = player['badge'] or ''
        text += f'{medals[i]} *{escape_markdown(name)}* {escape_markdown(badge)} — *{format_number(player[field])}*\n'
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='MarkdownV2')
    except:
        bot.send_message(call.message.chat.id, text, parse_mode='MarkdownV2')

# ============================================================
# 🛒 МАГАЗИН
# ============================================================
@bot.message_handler(func=lambda m: m.text == '🛒 Магазин')
@bot.message_handler(commands=['shop'])
@anti_flood
def shop_command(message):
    uid = message.from_user.id
    user = get_user(uid)
    inventory = json.loads(user.get('inv', '{}'))
    
    kb = InlineKeyboardMarkup(row_width=1)
    for item_id, item_data in SHOP.items():
        owned = item_id in inventory
        label = f'{"✅" if owned else "🛒"} {item_data["name"]} — {"Куплено" if owned else format_number(item_data["price"]) + " " + CURRENCY}'
        kb.add(InlineKeyboardButton(
            label,
            callback_data=f'{"equip" if owned else "buy"}_{item_id}'))
    
    bot.send_message(message.chat.id,
        f'🛒 *МАГАЗИН* 🛒\n\n'
        f'💎 Баланс: *{format_number(user["balance"])} {CURRENCY}*\n'
        f'✅=куплено (нажми чтобы надеть)\n\n'
        f'Выбери:',
        parse_mode='MarkdownV2',
        reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('buy_'))
@anti_flood
def shop_buy(call):
    uid = call.from_user.id
    item_id = call.data[4:]
    item_data = SHOP.get(item_id)
    
    if not item_data:
        return
    
    user = get_user(uid)
    inventory = json.loads(user.get('inv', '{}'))
    
    if item_id in inventory:
        bot.answer_callback_query(call.id, '✅ Уже куплено!')
        return
    
    if user['balance'] < item_data['price']:
        bot.answer_callback_query(call.id,
            f'❌ Нужно {format_number(item_data["price"])} {CURRENCY}!',
            show_alert=True)
        return
    
    update_balance(uid, -item_data['price'], f'Покупка {item_id}')
    inventory[item_id] = datetime.now().isoformat()
    update_user(uid, inv=json.dumps(inventory))
    
    bot.answer_callback_query(call.id, f'✅ Куплено! {item_data["name"]}')
    bot.send_message(call.message.chat.id,
        f'✅ *Куплено!* {escape_markdown(item_data["name"])}\n'
        f'Нажми ещё раз чтобы надеть!',
        parse_mode='MarkdownV2')

@bot.callback_query_handler(func=lambda c: c.data.startswith('equip_'))
@anti_flood
def shop_equip(call):
    uid = call.from_user.id
    item_id = call.data[6:]
    item_data = SHOP.get(item_id)
    
    if not item_data:
        return
    
    if item_data['type'] == 'skin':
        update_user(uid, skin=item_data['val'])
        bot.answer_callback_query(call.id, f'✅ Скин надет: {item_data["val"]}')
    elif item_data['type'] == 'badge':
        update_user(uid, badge=item_data['val'])
        bot.answer_callback_query(call.id, f'✅ Бейдж надет!')
    else:
        bot.answer_callback_query(call.id, f'✅ Буст активен!')

# ============================================================
# 🏅 АЧИВКИ
# ============================================================
@bot.message_handler(func=lambda m: m.text == '🏅 Ачивки')
@bot.message_handler(commands=['achievements'])
@anti_flood
def achievements_command(message):
    uid = message.from_user.id
    user = get_user(uid)
    earned = set(json.loads(user['achs']))
    
    text = f'🏅 *ДОСТИЖЕНИЯ* — *{len(earned)}/{len(ACHIEVEMENTS)}*\n\n'
    
    for ach_id, ach_data in ACHIEVEMENTS.items():
        status = '✅' if ach_id in earned else '🔒'
        text += f'{status} {escape_markdown(ach_data["name"])} — _{escape_markdown(ach_data["desc"])}_\n'
        if len(text) > 3500:
            text += '\n... ещё больше!'
            break
    
    bot.send_message(message.chat.id, text, parse_mode='MarkdownV2', reply_markup=main_keyboard())

# ============================================================
# 📜 ПОМОЩЬ
# ============================================================
@bot.message_handler(func=lambda m: m.text == '📜 Помощь')
@bot.message_handler(commands=['help'])
@anti_flood
def help_command(message):
    bot.send_message(message.chat.id,
        '📜 *ULTIMATE CASINO — ПОМОЩЬ* 📜\n\n'
        '🎮 *Игры:*\n'
        '🎰 Слоты — джекпот/x50/x20/x10/x5/x3/x2\n'
        '🎲 Кости — 6=x6, 5=x3, 4=x2\n'
        '🎯 Дартс — яблочко=x10, x5, x3\n'
        '🏀 Баскет — x4 или x2\n'
        '🎳 Боулинг — страйк=x5, спэр=x2\n'
        '🪙 Монетка — угадай=x2\n'
        '🃏 Блэкджек — натуральный=x2.5\n'
        '🎡 Рулетка — число=x36, зеро=x36\n'
        '🚀 Краш — выбери множитель и не крашнись!\n\n'
        '💰 *Экономика:*\n'
        f'• Старт: {START_BALANCE} {CURRENCY}\n'
        '• Бонус: каждые 24ч (стрик ×1–×7)\n'
        '• Уровни 1–100 с наградами\n'
        f'• Рефералы: +{REFERRAL_FRIEND}/+{REFERRAL_OWNER} {CURRENCY}\n\n'
        '🏰 *Социальное:*\n'
        '• Дуэли между игроками\n'
        '• Кланы с казной\n'
        '• Подарки (/send)\n\n'
        '📦 Кейсы | 🛒 Магазин | 🏅 50+ достижений\n\n'
        f'🔥 *Выходные = x{WEEKEND_MULTIPLIER} выигрыши!*\n\n'
        '💬 *Просто пиши что угодно — я понимаю!*',
        parse_mode='MarkdownV2',
        reply_markup=main_keyboard())

# ============================================================
# 🎀 ПОДАРОК
# ============================================================
@bot.message_handler(func=lambda m: m.text == '🎀 Подарок')
@bot.message_handler(commands=['gift'])
@anti_flood
def gift_command(message):
    bot.send_message(message.chat.id,
        '🎀 *ПОДАРОК ДРУГУ* 🎀\n\n'
        'Отправь монеты другому игроку!\n\n'
        'Команда:\n`/send @username сумма`\n'
        'или\n`/send user_id сумма`\n\n'
        'Пример: `/send @friend 1000`',
        parse_mode='MarkdownV2')

@bot.message_handler(commands=['send'])
@anti_flood
def send_command(message):
    uid = message.from_user.id
    parts = message.text.split()
    
    if len(parts) < 3:
        bot.send_message(message.chat.id, '❌ Формат: /send @username сумма')
        return
    
    try:
        amount = int(parts[2])
        if amount < 1:
            bot.send_message(message.chat.id, '❌ Минимум 1 {CURRENCY}')
            return
        
        user = get_user(uid)
        if user['balance'] < amount:
            bot.send_message(message.chat.id, '❌ Недостаточно монет!')
            return
        
        target = parts[1].replace('@', '')
        
        conn = get_db()
        if target.isdigit():
            target_user = conn.execute('SELECT * FROM users WHERE uid=?', (int(target),)).fetchone()
        else:
            target_user = conn.execute('SELECT * FROM users WHERE username=?', (target,)).fetchone()
        conn.close()
        
        if not target_user:
            bot.send_message(message.chat.id, '❌ Пользователь не найден! Он должен запустить бота.')
            return
        
        target_id = target_user['uid']
        if target_id == uid:
            bot.send_message(message.chat.id, '❌ Нельзя отправить себе!')
            return
        
        update_balance(uid, -amount, f'Подарок для {target_id}')
        update_balance(target_id, amount, f'Подарок от {uid}')
        
        bot.send_message(message.chat.id,
            f'🎀 *Подарок отправлен!*\n\n'
            f'👤 Для: *{escape_markdown(target_user["fname"] or target)}*\n'
            f'💰 *{format_number(amount)} {CURRENCY}*\n\n'
            f'❤️ Ты такой щедрый!',
            parse_mode='MarkdownV2')
        
        try:
            bot.send_message(target_id,
                f'🎁 *ТЫ ПОЛУЧИЛ ПОДАРОК!*\n\n'
                f'👤 От: *{escape_markdown(message.from_user.first_name)}*\n'
                f'💰 *+{format_number(amount)} {CURRENCY}*! 🙏',
                parse_mode='MarkdownV2')
        except:
            pass
        
        user = get_user(uid)
        earned = set(json.loads(user['achs']))
        if 'gift_sent' not in earned:
            earned.add('gift_sent')
            update_user(uid, achs=json.dumps(list(earned)))
            bot.send_message(message.chat.id,
                f'🏅 *{escape_markdown(ACHIEVEMENTS["gift_sent"]["name"])}*\n💎 +{ACHIEVEMENTS["gift_sent"]["r"]} {CURRENCY}',
                parse_mode='MarkdownV2')
            update_balance(uid, ACHIEVEMENTS['gift_sent']['r'], 'Ачивка подарок')
        
    except ValueError:
        bot.send_message(message.chat.id, '❌ Неверная сумма!')

# ============================================================
# 🏰 КЛАНЫ (упрощённо)
# ============================================================
@bot.message_handler(func=lambda m: m.text == '🏰 Кланы')
@bot.message_handler(commands=['clan', 'clans'])
@anti_flood
def clans_command(message):
    uid = message.from_user.id
    user = get_user(uid)
    
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton('🏗️ Создать клан (1000 КК)', callback_data='clan_create'),
        InlineKeyboardButton('👥 Мой клан', callback_data='clan_my'),
    )
    
    bot.send_message(message.chat.id,
        f'🏰 *КЛАНЫ* 🏰\n\n'
        f'Сражайтесь за топ вместе!\n\n'
        f'💎 Баланс: *{format_number(user["balance"])} {CURRENCY}*\n'
        f'{"🏰 В клане: "+str(user["clan_id"]) if user["clan_id"] else "🔓 Без клана"}\n\n'
        f'Выбери:',
        parse_mode='MarkdownV2',
        reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == 'clan_create')
@anti_flood
def clan_create(call):
    uid = call.from_user.id
    user = get_user(uid)
    
    if user['clan_id']:
        bot.answer_callback_query(call.id, '❌ Ты уже в клане!')
        return
    
    if user['balance'] < 1000:
        bot.answer_callback_query(call.id, '❌ Нужно 1000 КК!', show_alert=True)
        return
    
    try:
        bot.edit_message_text(
            '🏗️ *Создать клан*\n\nВведи название (2–20 символов):',
            call.message.chat.id,
            call.message.message_id,
            parse_mode='MarkdownV2')
    except:
        pass
    
    bot.register_next_step_handler(call.message, process_clan_create)

def process_clan_create(message):
    uid = message.from_user.id
    clan_name = message.text.strip()
    
    if len(clan_name) < 2 or len(clan_name) > 20:
        bot.send_message(message.chat.id, '❌ Название 2–20 символов!')
        return
    
    user = get_user(uid)
    if user['balance'] < 1000:
        bot.send_message(message.chat.id, '❌ Нужно 1000 КК!')
        return
    
    conn = get_db()
    existing = conn.execute('SELECT id FROM clans WHERE name=?', (clan_name,)).fetchone()
    if existing:
        conn.close()
        bot.send_message(message.chat.id, '❌ Клан с таким именем уже есть!')
        return
    
    conn.execute(
        'INSERT INTO clans(name, owner, members) VALUES(?,?,?)',
        (clan_name, uid, json.dumps([uid])))
    clan_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.commit()
    conn.close()
    
    update_balance(uid, -1000, f'Создание клана {clan_name}')
    update_user(uid, clan_id=clan_id)
    
    user = get_user(uid)
    earned = set(json.loads(user['achs']))
    if 'clan_created' not in earned:
        earned.add('clan_created')
        update_user(uid, achs=json.dumps(list(earned)))
        bot.send_message(message.chat.id,
            f'🏅 *{escape_markdown(ACHIEVEMENTS["clan_created"]["name"])}*\n💎 +{ACHIEVEMENTS["clan_created"]["r"]} {CURRENCY}',
            parse_mode='MarkdownV2')
        update_balance(uid, ACHIEVEMENTS['clan_created']['r'], 'Ачивка создание клана')
    
    bot.send_message(message.chat.id,
        f'🏰 *Клан создан!*\n\n'
        f'🏷️ *{escape_markdown(clan_name)}*\n'
        f'🆔 {clan_id}\n\n'
        f'Приглашай друзей!',
        parse_mode='MarkdownV2',
        reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda c: c.data == 'clan_my')
@anti_flood
def clan_my(call):
    uid = call.from_user.id
    user = get_user(uid)
    
    if not user['clan_id']:
        bot.answer_callback_query(call.id, 'Ты не в клане!')
        return
    
    conn = get_db()
    clan = conn.execute('SELECT * FROM clans WHERE id=?', (user['clan_id'],)).fetchone()
    conn.close()
    
    if not clan:
        update_user(uid, clan_id=0)
        bot.answer_callback_query(call.id, 'Клан удалён!')
        return
    
    members = json.loads(clan['members'])
    
    kb = InlineKeyboardMarkup()
    if clan['owner'] == uid:
        kb.add(InlineKeyboardButton('💣 Удалить клан', callback_data='clan_delete'))
    else:
        kb.add(InlineKeyboardButton('🚪 Покинуть', callback_data='clan_leave'))
    
    try:
        bot.edit_message_text(
            f'🏰 *{escape_markdown(clan["name"])}*\n\n'
            f'👑 Владелец: `{clan["owner"]}`\n'
            f'👥 Участников: {len(members)}\n'
            f'💰 Казна: {format_number(clan["bank"])} {CURRENCY}\n'
            f'⭐ Уровень: {clan["level"]}',
            call.message.chat.id,
            call.message.message_id,
            parse_mode='MarkdownV2',
            reply_markup=kb)
    except:
        pass

@bot.callback_query_handler(func=lambda c: c.data == 'clan_leave')
@anti_flood
def clan_leave(call):
    uid = call.from_user.id
    user = get_user(uid)
    
    if not user['clan_id']:
        return
    
    conn = get_db()
    clan = conn.execute('SELECT * FROM clans WHERE id=?', (user['clan_id'],)).fetchone()
    
    if clan:
        members = json.loads(clan['members'])
        if uid in members:
            members.remove(uid)
            conn.execute(
                'UPDATE clans SET members=? WHERE id=?',
                (json.dumps(members), user['clan_id']))
    
    conn.commit()
    conn.close()
    
    update_user(uid, clan_id=0)
    bot.answer_callback_query(call.id, '👋 Ты покинул клан!')
    bot.send_message(call.message.chat.id, 'Ты покинул клан.', reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda c: c.data == 'clan_delete')
@anti_flood
def clan_delete(call):
    uid = call.from_user.id
    user = get_user(uid)
    
    if not user['clan_id']:
        return
    
    conn = get_db()
    clan = conn.execute('SELECT * FROM clans WHERE id=? AND owner=?', (user['clan_id'], uid)).fetchone()
    
    if clan:
        members = json.loads(clan['members'])
        for member_id in members:
            if member_id != uid:
                update_user(member_id, clan_id=0)
        conn.execute('DELETE FROM clans WHERE id=?', (user['clan_id'],))
        conn.commit()
        
        update_user(uid, clan_id=0)
        bot.answer_callback_query(call.id, '💥 Клан удалён!')
        bot.send_message(call.message.chat.id, 'Клан удалён.', reply_markup=main_keyboard())
    else:
        bot.answer_callback_query(call.id, '❌ Ты не владелец!')
    
    conn.close()

# ============================================================
# ⚔️ ДУЭЛИ (упрощённо)
# ============================================================
@bot.message_handler(func=lambda m: m.text == '⚔️ Дуэль')
@bot.message_handler(commands=['duel'])
@anti_flood
def duel_command(message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton('⚔️ Создать дуэль', callback_data='duel_create'),
        InlineKeyboardButton('📋 Открытые дуэли', callback_data='duel_list'),
    )
    bot.send_message(message.chat.id,
        '⚔️ *ДУЭЛИ* ⚔️\n\n'
        'Брось вызов другим игрокам!\n'
        'Победитель забирает весь банк!\n\n'
        'Выбери:',
        parse_mode='MarkdownV2',
        reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == 'duel_create')
@anti_flood
def duel_create(call):
    bot.edit_message_text(
        '⚔️ *Создать дуэль*\n\nВведи сумму ставки:',
        call.message.chat.id,
        call.message.message_id,
        parse_mode='MarkdownV2')
    bot.register_next_step_handler(call.message, process_duel_create)

def process_duel_create(message):
    uid = message.from_user.id
    try:
        bet = int(message.text.strip())
        user = get_user(uid)
        
        if bet < 10 or bet > MAX_BET or user['balance'] < bet:
            bot.send_message(message.chat.id, '❌ Неверная ставка (мин 10)!')
            return
        
        update_balance(uid, -bet, 'Создание дуэли')
        
        conn = get_db()
        conn.execute(
            'INSERT INTO duels(challenger, bet) VALUES(?,?)',
            (uid, bet))
        duel_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.commit()
        conn.close()
        
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(
            InlineKeyboardButton(
                f'⚔️ Принять дуэль ({format_number(bet)} {CURRENCY})',
                callback_data=f'duel_accept_{duel_id}'),
            InlineKeyboardButton('❌ Отменить', callback_data=f'duel_cancel_{duel_id}'))
        
        bot.send_message(message.chat.id,
            f'⚔️ *ДУЭЛЬ СОЗДАНА!* #{duel_id}\n\n'
            f'💰 Ставка: *{format_number(bet)} {CURRENCY}*\n'
            f'🎲 Игра: Кости\n\n'
            f'Поделись этим сообщением чтобы найти соперника!',
            parse_mode='MarkdownV2',
            reply_markup=kb)
    except ValueError:
        bot.send_message(message.chat.id, '❌ Введи число!')

@bot.callback_query_handler(func=lambda c: c.data.startswith('duel_accept_'))
@anti_flood
def duel_accept(call):
    uid = call.from_user.id
    duel_id = int(call.data[12:])
    
    conn = get_db()
    duel = conn.execute(
        'SELECT * FROM duels WHERE id=?', (duel_id,)
    ).fetchone()
    
    if not duel or duel['status'] != 'waiting':
        conn.close()
        bot.answer_callback_query(call.id, '❌ Дуэль недоступна!')
        return
    
    if duel['challenger'] == uid:
        conn.close()
        bot.answer_callback_query(call.id, '❌ Нельзя принять свою дуэль!')
        return
    
    user = get_user(uid)
    if user['balance'] < duel['bet']:
        conn.close()
        bot.answer_callback_query(call.id,
            f'❌ Нужно {format_number(duel["bet"])} {CURRENCY}!',
            show_alert=True)
        return
    
    update_balance(uid, -duel['bet'], 'Участие в дуэли')
    
    roll1 = random.randint(1, 6)
    roll2 = random.randint(1, 6)
    
    while roll1 == roll2:
        roll1 = random.randint(1, 6)
        roll2 = random.randint(1, 6)
    
    winner_id = duel['challenger'] if roll1 > roll2 else uid
    prize = duel['bet'] * 2
    
    update_balance(winner_id, prize, f'Победа в дуэли #{duel_id}')
    
    conn.execute(
        'UPDATE duels SET status=?, opponent=?, winner=? WHERE id=?',
        ('finished', uid, winner_id, duel_id))
    conn.commit()
    conn.close()
    
    challenger = get_user(duel['challenger'])
    opponent = get_user(uid)
    
    try:
        bot.edit_message_text(
            f'⚔️ *ДУЭЛЬ #{duel_id} ЗАВЕРШЕНА!* ⚔️\n\n'
            f'🎲 {escape_markdown(challenger["fname"])} бросил: *{roll1}*\n'
            f'🎲 {escape_markdown(opponent["fname"])} бросил: *{roll2}*\n\n'
            f'🏆 Победитель: *{escape_markdown(get_user(winner_id)["fname"])}*\n'
            f'💰 Приз: *+{format_number(prize)} {CURRENCY}*',
            call.message.chat.id,
            call.message.message_id,
            parse_mode='MarkdownV2')
    except:
        pass
    
    winner = get_user(winner_id)
    earned = set(json.loads(winner['achs']))
    if 'duel_win' not in earned:
        earned.add('duel_win')
        update_user(winner_id, achs=json.dumps(list(earned)))
        bot.send_message(call.message.chat.id,
            f'🏅 *{escape_markdown(ACHIEVEMENTS["duel_win"]["name"])}*\n💎 +{ACHIEVEMENTS["duel_win"]["r"]} {CURRENCY}',
            parse_mode='MarkdownV2')
        update_balance(winner_id, ACHIEVEMENTS['duel_win']['r'], 'Ачивка дуэль')

@bot.callback_query_handler(func=lambda c: c.data.startswith('duel_cancel_'))
@anti_flood
def duel_cancel(call):
    uid = call.from_user.id
    duel_id = int(call.data[12:])
    
    conn = get_db()
    duel = conn.execute(
        'SELECT * FROM duels WHERE id=? AND challenger=?',
        (duel_id, uid)
    ).fetchone()
    
    if not duel or duel['status'] != 'waiting':
        conn.close()
        bot.answer_callback_query(call.id, '❌ Нельзя отменить!')
        return
    
    update_balance(uid, duel['bet'], 'Отмена дуэли — возврат')
    
    conn.execute(
        "UPDATE duels SET status='cancelled' WHERE id=?",
        (duel_id,))
    conn.commit()
    conn.close()
    
    try:
        bot.edit_message_text(
            f'❌ Дуэль #{duel_id} отменена. Ставка возвращена.',
            call.message.chat.id,
            call.message.message_id,
            parse_mode='MarkdownV2')
    except:
        pass

@bot.callback_query_handler(func=lambda c: c.data == 'duel_list')
@anti_flood
def duel_list(call):
    conn = get_db()
    duels = conn.execute(
        "SELECT * FROM duels WHERE status='waiting' ORDER BY ts DESC LIMIT 10"
    ).fetchall()
    conn.close()
    
    if not duels:
        bot.answer_callback_query(call.id, 'Нет открытых дуэлей!')
        return
    
    kb = InlineKeyboardMarkup(row_width=1)
    for duel in duels:
        challenger = get_user(duel['challenger'])
        name = challenger.get('fname', 'Игрок')
        kb.add(InlineKeyboardButton(
            f'⚔️ #{duel["id"]} — {name} — {format_number(duel["bet"])} {CURRENCY}',
            callback_data=f'duel_accept_{duel["id"]}'))
    
    try:
        bot.edit_message_text(
            '⚔️ *ОТКРЫТЫЕ ДУЭЛИ*\n\nНажми чтобы принять:',
            call.message.chat.id,
            call.message.message_id,
            parse_mode='MarkdownV2',
            reply_markup=kb)
    except:
        pass

# ============================================================
# 💬 ЧАТ-БОТ
# ============================================================
CHAT_RESPONSES = {
    ('привет', 'хай', 'хэй', 'здарова', 'дарова', 'hello', 'hi', 'ку'): [
        'Привет! 🎰 Готов испытать удачу?',
        'Хэй! 👋 Сегодня твой счастливый день!',
        'Привет, игрок! Джекпот уже ждёт тебя!',
    ],
    ('как дела', 'как ты', 'что делаешь'): [
        'Отлично — слежу как растёт джекпот! 💰',
        'В порядке! Жду когда ты сорвёшь куш 🎰',
        'Жду тебя в игре! 🎮',
    ],
    ('дай денег', 'хочу денег', 'нет денег', 'беден', 'банкрот'): [
        'Лови /bonus — там 100–500 КК!',
        'Ежедневный бонус уже ждёт тебя 🎁 /bonus',
        'Попробуй краш или слоты — может повезёт!',
    ],
    ('скучно', 'нечего делать'): [
        'Скучно?! А ну быстро в краш-игру! 🚀',
        'Открой кейс или кинь дуэль кому-нибудь! ⚔️',
    ],
    ('спасибо', 'благодарю', 'thanks'): [
        'Пожалуйста! 🙏 Удачи в игре!',
        'Всегда рад помочь! 😊',
    ],
    ('помоги', 'не понимаю', 'что делать'): [
        'Жми 📜 Помощь — там всё написано!',
        'Попробуй /help — объясню всё!',
    ],
    ('выигрыш', 'выиграл', 'выиграло'): [
        'Поздравляю! 🎉 Давай ещё раз!',
        'Удача на твоей стороне! 🍀 Не останавливайся!',
    ],
    ('проиграл', 'не везёт', 'отстой'): [
        'Бывает... Удача циклична! Попробуй другую игру 🎲',
        'Не опускай руки! Блэкджек требует стратегии 🃏',
        'Возьми бонус и попробуй снова! 🎁',
    ],
    ('молодец', 'ты лучший', 'топ'): [
        'Ты льстишь 😊 Держи бонус — /bonus!',
        'Лучший — это ты когда сорвёшь джекпот! 🏆',
    ],
}

def get_chat_reply(text):
    text_lower = text.lower().strip()
    
    for keywords, replies in CHAT_RESPONSES.items():
        if any(keyword in text_lower for keyword in keywords):
            return random.choice(replies)
    
    if '?' in text:
        return random.choice([
            'Хороший вопрос! Попробуй сам в слотах 🎰',
            'Не знаю 😄 Зато знаю как выиграть! /help',
            'Загадочно... Лучше иди играть! 🎮',
        ])
    
    return None

# ============================================================
# 🎯 ГЛАВНЫЙ ОБРАБОТЧИК
# ============================================================
MENU_HANDLERS = {
    '🎰 Слоты': slots_menu,
    '🎲 Кости': dice_menu,
    '🎯 Дартс': darts_menu,
    '🏀 Баскет': basketball_menu,
    '🎳 Боулинг': bowling_menu,
    '🪙 Монетка': coin_menu,
    '🃏 Блэкджек': blackjack_menu,
    '🎡 Рулетка': roulette_menu,
    '🚀 Краш': crash_menu,
    '📦 Кейсы': cases_menu,
    '💰 Баланс': balance_command,
    '🎁 Бонус': bonus_command,
    '🏆 Топ': top_command,
    '📊 Профиль': profile_command,
    '🛒 Магазин': shop_command,
    '⚔️ Дуэль': duel_command,
    '🏰 Кланы': clans_command,
    '🎀 Подарок': gift_command,
    '🏅 Ачивки': achievements_command,
    '📜 Помощь': help_command,
}

@bot.message_handler(func=lambda m: True)
@anti_flood
def handle_all_messages(message):
    uid = message.from_user.id
    text = message.text or ''
    
    update_user(uid,
        fname=message.from_user.first_name or 'Игрок',
        username=message.from_user.username or '',
        active=datetime.now().isoformat())
    
    if text in MENU_HANDLERS:
        MENU_HANDLERS[text](message)
        return
    
    reply = get_chat_reply(text)
    if reply:
        bot.send_message(message.chat.id, reply, parse_mode='MarkdownV2', reply_markup=main_keyboard())
        return
    
    defaults = [
        'Хм, не понял, но рад тебя видеть! Жми 📜 Помощь или выбирай игру 🎮',
        'Пиши /help чтобы узнать всё о боте!',
        'Может ты ищешь джекпот? Иди в 🎰 Слоты!',
        'Загадочно... Но лучше сыграй в 🃏 Блэкджек!',
    ]
    bot.send_message(message.chat.id, random.choice(defaults), parse_mode='MarkdownV2', reply_markup=main_keyboard())

# ============================================================
# 👑 АДМИН-КОМАНДЫ
# ============================================================
@bot.message_handler(commands=['give'])
@admin_only
def admin_give(message):
    parts = message.text.split()
    if len(parts) < 3:
        bot.send_message(message.chat.id, '❌ /give user_id amount')
        return
    
    try:
        target_id = int(parts[1])
        amount = int(parts[2])
        new_balance = update_balance(target_id, amount, f'Admin give by {message.from_user.id}')
        bot.send_message(message.chat.id,
            f'✅ Выдано {format_number(amount)} {CURRENCY} пользователю {target_id}. '
            f'Новый баланс: {format_number(new_balance)} {CURRENCY}',
            parse_mode='MarkdownV2')
        try:
            bot.send_message(target_id,
                f'🎁 Администратор выдал тебе *{format_number(amount)} {CURRENCY}!*',
                parse_mode='MarkdownV2')
        except:
            pass
    except ValueError:
        bot.send_message(message.chat.id, '❌ Неверные параметры')

@bot.message_handler(commands=['take'])
@admin_only
def admin_take(message):
    parts = message.text.split()
    if len(parts) < 3:
        bot.send_message(message.chat.id, '❌ /take user_id amount')
        return
    
    try:
        target_id = int(parts[1])
        amount = int(parts[2])
        new_balance = update_balance(target_id, -amount, f'Admin take by {message.from_user.id}')
        bot.send_message(message.chat.id,
            f'✅ Забрано {format_number(amount)} {CURRENCY} у {target_id}. '
            f'Новый баланс: {format_number(new_balance)} {CURRENCY}',
            parse_mode='MarkdownV2')
    except ValueError:
        bot.send_message(message.chat.id, '❌ Неверные параметры')

@bot.message_handler(commands=['ban'])
@admin_only
def admin_ban(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, '❌ /ban user_id')
        return
    
    try:
        target_id = int(parts[1])
        update_user(target_id, banned=1)
        bot.send_message(message.chat.id, f'✅ Пользователь {target_id} забанен')
    except ValueError:
        bot.send_message(message.chat.id, '❌ Неверный ID')

@bot.message_handler(commands=['unban'])
@admin_only
def admin_unban(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, '❌ /unban user_id')
        return
    
    try:
        target_id = int(parts[1])
        update_user(target_id, banned=0)
        bot.send_message(message.chat.id, f'✅ Пользователь {target_id} разбанен')
    except ValueError:
        bot.send_message(message.chat.id, '❌ Неверный ID')

@bot.message_handler(commands=['broadcast'])
@admin_only
def admin_broadcast(message):
    text = message.text[len('/broadcast '):].strip()
    if not text:
        bot.send_message(message.chat.id, '❌ /broadcast текст')
        return
    
    conn = get_db()
    users = conn.execute('SELECT uid FROM users WHERE banned=0').fetchall()
    conn.close()
    
    sent = 0
    failed = 0
    
    for user in users:
        try:
            bot.send_message(user['uid'],
                f'📢 *ОБЪЯВЛЕНИЕ*\n\n{escape_markdown(text)}',
                parse_mode='MarkdownV2')
            sent += 1
            time.sleep(0.05)
        except:
            failed += 1
    
    bot.send_message(message.chat.id,
        f'✅ Отправлено: {sent} | Не доставлено: {failed}')

@bot.message_handler(commands=['stats'])
@admin_only
def admin_stats(message):
    conn = get_db()
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    total_games = conn.execute('SELECT SUM(games) FROM users').fetchone()[0] or 0
    total_won = conn.execute('SELECT SUM(won) FROM users').fetchone()[0] or 0
    total_lost = conn.execute('SELECT SUM(lost) FROM users').fetchone()[0] or 0
    active_today = conn.execute(
        "SELECT COUNT(*) FROM users WHERE active>datetime('now','-1 day')"
    ).fetchone()[0]
    jackpot = get_jackpot()
    conn.close()
    
    bot.send_message(message.chat.id,
        f'📊 *СТАТИСТИКА БОТА*\n\n'
        f'👥 Пользователей: {total_users}\n'
        f'🟢 Активных сегодня: {active_today}\n'
        f'🎮 Всего игр: {format_number(total_games)}\n'
        f'✅ Выиграно: {format_number(total_won)} {CURRENCY}\n'
        f'❌ Проиграно: {format_number(total_lost)} {CURRENCY}\n'
        f'📈 Профит казино: {format_number(total_lost - total_won)} {CURRENCY}\n'
        f'💰 Джекпот: {format_number(jackpot)} {CURRENCY}',
        parse_mode='MarkdownV2')

# ============================================================
# ⏰ ФОНОВЫЕ ЗАДАЧИ
# ============================================================
def backup_loop():
    while True:
        time.sleep(BACKUP_HOURS * 3600)
        try:
            os.makedirs('backups', exist_ok=True)
            backup_name = f'backups/casino_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            shutil.copy2(DB_FILE, backup_name)
            
            backups = sorted(glob.glob('backups/casino_*.db'))
            for old_backup in backups[:-10]:
                os.remove(old_backup)
            
            logger.info(f'✅ Бэкап создан: {backup_name}')
        except Exception as e:
            logger.error(f'❌ Ошибка бэкапа: {e}')

# ============================================================
# 🚀 ЗАПУСК
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("   🎰 ULTIMATE CASINO BOT v3.0")
    print("=" * 60)
    
    init_db()
    
    threading.Thread(target=backup_loop, daemon=True).start()
    
    logger.info('=' * 55)
    logger.info('🎰  ULTIMATE CASINO BOT v3.0 ЗАПУЩЕН!')
    logger.info(f'💾  БД: {DB_FILE}')
    logger.info(f'⚡  Антифлуд: {FLOOD_MSGS} сообщений/{FLOOD_WINDOW}с')
    logger.info(f'💾  Бэкап каждые {BACKUP_HOURS} часов')
    logger.info('🚀  Открывай Telegram и пиши /start!')
    logger.info('=' * 55)
    
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=5)
        except Exception as e:
            logger.error(f'❌ Ошибка: {e}')
            time.sleep(5)
            logger.info('🔄 Перезапуск...')
