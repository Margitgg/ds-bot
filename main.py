import telebot
from telebot import types
from telebot.types import Message, InlineKeyboardButton as IKB, CallbackQuery
from config import token
from database import *
from text import *
import time, random, datetime


class Enemy:
    enemies = {
        "вурдалак": (100, 20),
        "оборотень": (80, 15),
        "зомби": (60, 25),
        "мутант": (110, 35),
        "клон": (90, 40),
        "дракон": (150, 15),
        "демон": (95, 45),
        "дикий волк": (55, 15),
    }

    def __init__(self, m: Message):
        player = db.read("user_id", m.chat.id)
        self.name = random.choice(list(self.enemies))
        self.hp = self.enemies[self.name][0] + (10 * player[5])
        self.damage = self.enemies[self.name][1] + (5 * player[5])


bot = telebot.TeleBot(token)
temp = {}
clear = types.ReplyKeyboardRemove()


@bot.message_handler(['start'])
def start(m: Message):
    if is_new_player(m):
        reg_1(m)
        temp[m.chat.id] = {"nick": None}
    else:
        menu(m)


def is_new_player(m: Message):
    result = db.read_all()
    for user in result:
        if user[0] == m.chat.id:
            return False
    return True


@bot.message_handler(['home'])
def home(m: Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row("поспать", "поесть")
    bot.send_message(m.chat.id, text="ты дома, выбери что хочешь сделать", reply_markup=kb)
    bot.register_next_step_handler(m, reg_4)


@bot.message_handler(['stats'])
def stats(m: Message):
    player = db.read("user_id", m.chat.id)
    text = (f"Вы:   {player[1]}\nваш лвл {player[5]}\nваше hp {player[3]}\nваш урон {player[4]}\nваш опыт {player[6]}\n"
            f"ваша раса {player[2]}\nваших наград {player[7]}\nваша еда ")
    _, food = heals.read('user_id', m.chat.id)

    for f in food:
        text += f'{f} hp{food[f][1]} - {food[f][0]}шт.\n'
    bot.send_message(m.chat.id, text)
    time.sleep(3)
    menu(m)


@bot.message_handler(['square'])
def square(m: Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row("пойти в бой", "тренироваться", "проверить силы")
    bot.send_message(m.chat.id, text="ты на главной площади,выбери что хочешь сделать", reply_markup=kb)
    bot.register_next_step_handler(m, reg_5)


@bot.callback_query_handler(
    func=lambda call: True)  # lambda нужна для того чтобы не возникало ошибок, при не обработке функции!
def callback(call: CallbackQuery):
    print(call.data)
    if call.data.startswith("food_"):
        a = call.data.split(sep='_')
        eating(call.message, a[1], a[2])
        kb = types.InlineKeyboardMarkup()
        id, food = heals.read("user_id", call.message.chat.id)
        if food == {}:
            bot.send_message(call.message.chat.id, text="есть нечего", reply_markup=clear)
            menu(call.message)
            return
        for key in food:
            kb.row(IKB(f"{key} {food[key][1]}hp❤️ - {food[key][0]}штук", callback_data=f"food_{key}_{food[key][1]}"))
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=kb)
    elif call.data.startswith("sleep_"):
        a = call.data.split(sep='_')
        t = int(a[1]) * 5
        bot.send_message(call.message.chat.id, f"ты лёг спать на {t} секунд")
        time.sleep(t)
        sleeping(call.message, a[1])
        menu(call.message)
    elif call.data == '0':
        menu(call.message)
    elif call.data == 'tren':
        player = db.read('user_id', call.message.chat.id)
        player[4] += player[5] / 10
        player[4] = round(player[4], 4)
        db.write(player)
        bot.answer_callback_query(call.id, "Ты тренируешься и твоя сила увеличивается! \n"
                                           f"теперь ты наносишь {player[4]}", True)


def eat(m: Message):
    kb = types.InlineKeyboardMarkup()
    id, food = heals.read("user_id", m.chat.id)
    if food == {}:
        bot.send_message(m.chat.id, text="есть нечего", reply_markup=clear)
        menu(m)
        return
    for key in food:
        if food[key][0] > 0:
            kb.row(IKB(f"{key} {food[key][1]}hp❤️ - {food[key][0]}штук", callback_data=f"food_{key}_{food[key][1]}"))
    bot.send_message(m.chat.id, "выбери что будешь есть:", reply_markup=kb)


def eating(m, ft, hp):
    id, food = heals.read("user_id", m.chat.id)
    player = db.read("user_id", m.chat.id)
    if food[ft][0] == 1:
        del food[ft]
    else:
        food[ft][0] -= 1

    heals.write([m.chat.id, food])
    player[3] += int(hp)
    db.write(player)
    print('Игрок поел')


def sleep(m: Message):
    player = db.read("user_id", m.chat.id)
    low = int(powers[player[2]][0] * player[5]) // 2 - player[3]
    high = int(powers[player[2]][0] * player[5]) - player[3]
    kb = types.InlineKeyboardMarkup()
    if low > 0:
        kb.row(IKB(f"Вздремнуть - {low}hp❤️", callback_data=f"sleep_{low}"))
    elif high > 0:
        kb.row(IKB(f"Хорошо выспаться - {high}hp❤️", callback_data=f"sleep_{high}"))
    elif len(kb.keyboard) == 0:
        kb.row(IKB('Спать не хочется', callback_data='0'))
    bot.send_message(m.chat.id, "выбери время сколько будешь отдыхать", reply_markup=kb)


def sleeping(m: Message, hp):
    player = db.read("user_id", m.chat.id)
    player[3] += int(hp)
    db.write(player)
    print("игрок поспал.")
    bot.reply_to(m, "ты поспал!")


def tren(m: Message):
    kb = types.InlineKeyboardMarkup()
    kb.row(IKB("тренироваться", callback_data='tren'))
    kb.row(IKB('назад', callback_data='0'))
    bot.send_message(m.chat.id, 'жми на кнопку чтобы тренироваться', reply_markup=kb)


def block(m: Message):
    try:
        print(temp[m.chat.id]["tren"])
    except:
        temp[m.chat.id]["tren"] = 0
    bot.send_message(m.chat.id, 'приготовься к атаке!!')
    time.sleep(2)
    sides = ["cлева", "справа", "сверху", "снизу"]
    random.shuffle(sides)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    kb.row(sides[0], sides[1])
    kb.row(sides[2], sides[3])
    side = random.choice(sides)
    bot.send_message(m.chat.id, f"Защищайся удар {side}!!!", reply_markup=kb)
    temp[m.chat.id]["start"] = datetime.datetime.now().timestamp()
    bot.register_next_step_handler(m, block_handler, side)


def block_handler(m: Message, side):
    final = datetime.datetime.now().timestamp()
    sec = 3
    if final - temp[m.chat.id]["start"] > sec or side != m.text:
        bot.send_message(m.chat.id, 'ты не успел уклониться, тренировка окончена!')
        temp[m.chat.id]["tren"] = 0
        time.sleep(3)
        menu(m)
        return
    else:
        bot.send_message(m.chat.id, 'ты успешно отразил атаку,тренировка продолжается.')
        temp[m.chat.id]["tren"] += 1
        if temp[m.chat.id]["tren"] == 5:
            bot.send_message(m.chat.id, "ты успешно справился с тренировкой")
            player = db.read('user_id', m.chat.id)
            player[7] += 1
            db.write(player)
            bot.send_message(m.chat.id, f'твоё количество наград: {player[7]}!')
            time.sleep(3)
            temp[m.chat.id]["tren"] = 0
            menu(m)
            return
        block(m)


def fight(m: Message):
    bot.send_message(m.chat.id, "ты отправился на поиски врагов")
    time.sleep(3)
    new_enemy(m)


def new_enemy(m: Message):
    enemy = Enemy(m)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row("напасть", "скрыться")
    kb.row("вернуться в город")
    txt = f"ты встретил врага: {enemy.name},его hp {enemy.hp},его damage {enemy.damage}.Что будешь делать?"
    bot.send_message(m.chat.id, txt, reply_markup=kb)
    bot.register_next_step_handler(m, fight_handler, enemy)


def fight_handler(m: Message, enemy: Enemy):
    if m.text == "напасть":
        attack(m, enemy)
    if m.text == "скрыться":
        rand = random.randint(1, 5)
        if rand <= 3:
            attack(m, enemy)
        else:
            bot.send_message(m.chat.id, 'тебе удалось сбежать от врага')
            time.sleep(1.5)
            fight(m)
    if m.text == 'вернуться в город':
        bot.send_message(m.chat.id, 'ты возвращаешься домой', reply_markup=clear)
        time.sleep(1.5)
        menu(m)


def attack(m: Message, enemy: Enemy):
    time.sleep(2)
    atk = player_attack(m, enemy)
    if atk:
        time.sleep(2)
        atk = enemy_attack(m, enemy)
        if atk:
            attack(m, enemy)
    else:
        new_enemy(m)
        return


def player_attack(m: Message, enemy: Enemy):
    player = db.read('user_id', m.chat.id)
    enemy.hp -= player[4]
    if enemy.hp <= 0:
        bot.send_message(m.chat.id, 'ты победил в этой битве, ты получил 5 опыта')
        player[6] += 5
        db.write(player)
        xp_check(m)
        return False
    if enemy.hp > 0:
        bot.send_message(m.chat.id, f'у врага осталось {enemy.hp} hp')
        return True


def enemy_attack(m: Message, enemy: Enemy):
    player = db.read('user_id', m.chat.id)
    player[3] -= enemy.damage
    db.write(player)
    if player[3] <= 0:
        bot.send_message(m.chat.id, 'ты проиграл в этой битве,твои союзники утащили тебя в город')
        player[3] = 0
        db.write(player)
        time.sleep(3)
        menu(m)
        return
    elif player[3] > 0:
        bot.send_message(m.chat.id, f'у тебя осталось {player[3]} hp')
        return True


def xp_check(m: Message):
    player = db.read("user_id", m.chat.id)
    if player[6] >= 25 * player[5] or player[6] >= 100:
        if player[6] >= 100:
            player[6] -= 100
        else:
            player[6] -= 25 * player[5]
        player[5] += 1
        player[3] += 3
        player[4] += 4
        db.write(player)
        bot.send_message(m.chat.id, 'ты повысил уровень,поздравляю вас!')
        

def reg_1(m: Message):
    bot.send_message(m.chat.id, text=start_main % m.from_user.first_name)
    bot.register_next_step_handler(m, reg_2)


def reg_2(m: Message):
    if not temp[m.chat.id]["nick"]:
        temp[m.chat.id]["nick"] = m.text
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row("эльфы", "викинги")
    kb.row("охотники", "вампиры")
    bot.send_message(m.chat.id, text="выбери расу", reply_markup=kb)
    bot.register_next_step_handler(m, reg_3)


@bot.message_handler(commands=["menu"])
def menu(m: Message):
    try:
        print(temp[m.chat.id])
    except:
        temp[m.chat.id] = {}
    bot.send_message(m.chat.id, text=text_menu, reply_markup=clear)


@bot.message_handler(commands=["add_heals"])
def add_heals(m: Message):
    _, food = heals.read("user_id", m.chat.id)
    print(food)

    food["суп из хвоста виверны"] = [5, 40]

    heals.write([m.chat.id, food])
    bot.send_message(m.chat.id, "выдали еду твоему герою")


def reg_3(m: Message):
    temp[m.chat.id]['power'] = m.text
    hp, damage = powers[m.text]
    db.write([m.chat.id, temp[m.chat.id]['nick'], temp[m.chat.id]['power'], hp, damage, 1, 0, 0])
    heals.write([m.chat.id, {}])
    print("Пользователь добавлен в базу данных")
    bot.send_message(m.chat.id, "идёт запись игрока в базу данных")
    time.sleep(2)
    menu(m)


def reg_4(m: Message):
    if m.text == "поспать":
        sleep(m)
    if m.text == "поесть":
        eat(m)


def reg_5(m: Message):
    try:
        print(temp[m.chat.id])
    except:
        temp[m.chat.id] = {}
    if m.text == "пойти в бой":
        fight(m)
    if m.text == "тренироваться":
        tren(m)
    if m.text == "проверить силы":
        block(m)


bot.infinity_polling()
