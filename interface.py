# импорты
import vk_api
import requests
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
import re
from datetime import datetime
from config import community_token, access_token
from core import VkTools

from data import check_user, add_user, engine

#логика для отправки сообщений


class BotInterface():
    def __init__(self, community_token, access_token):
        self.vk = vk_api.VkApi(token=community_token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_tools = VkTools(access_token)
        self.params = {}
        self.worksheets = []
        self.keys = []
        self.offset = 0

    def message_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send',
                       {'user_id': user_id,
                        'message': message,
                        'attachment': attachment,
                        'random_id': get_random_id()}
                       )

    def _bdate_toyear(self, bdate):
        user_year = bdate.split('.')[2]
        now = datetime.now().year
        return now - int(user_year)

    def photos_for_send(self, worksheet):
        photos = self.vk_tools.get_photos(worksheet['id'])
        photo_string = ''
        for photo in photos:
            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'

        return photo_string

    # k - отличительный параметр, что именно None

    def new_message(self, k):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if k == 0:
                    # Проверка на числа
                    contains_digit = False
                    for i in event.text:
                        if i.isdigit():
                            contains_digit = True
                            break  # Прерываю цикл, если цифра нашлась
                    if contains_digit:
                        self.message_send(event.user_id, 'Пожалуйста, введите имя и фамилию без чисел:')
                    else:
                        return event.text

                if k == 1:
                    if event.text == "1" or event.text == "2":
                        return int(event.text)
                    else:
                        self.message_send(event.user_id, 'Неверный формат ввода пола. Введите 1 или 2:')

                if k == 2:
                    # Проверка на числа
                    contains_digit = False
                    for i in event.text:
                        if i.isdigit():
                            contains_digit = True
                            break  # Прерываем цикл, если найдена цифра
                    if contains_digit:
                        self.message_send(event.user_id, 'Неверно указан город. Введите название города без чисел:')
                    else:
                        return event.text

                if k == 3:
                    pattern = r'^\d{2}\.\d{2}\.\d{4}$'
                    if not re.match(pattern, event.text):
                        self.message_send(event.user_id, 'Пожалуйста, введите вашу дату '
                                                         'рождения в формате (дд.мм.гггг):')
                    else:
                        return self._bdate_toyear(event.text)

                if k == 4:
                    #проверка на семейное положение
                    user_relation = user_id.get("relation")
                    if not user_relation:
                        print("Укажите ваше семейное положение (цифрой от 1 до 8): "
                              "1 — не женат/не замужем;" 
                              "2 — есть друг/подруга; "
                              "3 — помолвлен/помолвлена; "
                              "4 — женат/замужем; "
                              "5 — всё сложно; "
                              "6 — в активном поиске; "
                              "7 — влюблён/влюблена; "
                              "8 — в гражданском браке) ")
                        user_relation = int(input())

            # если не указано имя и фамилия

    def send_mes_exc(self, event):
        if self.params['name'] is None:
            self.message_send(event.user_id, 'Введите ваше имя и фамилию:')
            return self.new_message(0)

            # если не указан пол

        if self.params['sex'] is None:
            self.message_send(event.user_id, 'Введите свой пол (1-м, 2-ж):')
            return self.new_message(1)

            # если не указан город

        elif self.params['city'] is None:
            self.message_send(event.user_id, 'Введите город:')
            return self.new_message(2)

            # если не указана дата рождения

        elif self.params['year'] is None:
            self.message_send(event.user_id, 'Введите дату рождения (дд.мм.гггг):')
            return self.new_message(3)

    def get_profile(self, worksheets, event):
        while True:
            if worksheets:
                worksheet = worksheets.pop()
                #проверка анкеты в бд в соотвествии с event.user_id
                if not check_user(engine, event.user_id, worksheet['id']):
                #добавить анкету в бд в соотвествии с event.user_id
                    add_user(engine, event.user_id, worksheet['id'])

                    yield worksheet

            else:
                worksheets = self.vk_tools.search_worksheet(
                    self.params, self.offset)

# получение сообщений
    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    '''Логика для получения данных о пользователе'''
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.message_send(
                        event.user_id, f'Привет, {self.params["name"]}')

                    # обработка данных, которые не получили
                    self.keys = self.params.keys()
                    for i in self.keys:
                        if self.params[i] is None:
                            self.params[i] = self.send_mes_exc(event)

                    self.message_send(event.user_id, 'Напиши "Поиск", чтобы подобрать анкеты!')

                elif event.text.lower() == 'поиск':
                    #Логика для поиска анкет
                    self.message_send(
                        event.user_id, 'Начинаем поиск...')

                    msg = next(iter(self.get_profile(self.worksheets, event)))
                    if msg:

                        photo_string = self.photos_for_send(msg)
                        self.offset += 10

                        self.message_send(
                            event.user_id,
                            f'имя: {msg["name"]} ссылка: vk.com/id{msg["id"]}',
                            attachment=photo_string
                        )

                elif event.text.lower() == 'пока':
                    self.message_send(
                        event.user_id, 'До новых встреч')
                elif event.text.lower() == 'начать':
                    self.message_send(
                        event.user_id, 'Добро пожаловать в тестовую версию бота для знакомств :) Напишите "Привет", чтобы начать')
                else:
                    self.message_send(
                        event.user_id, 'Неизвестная команда')


if __name__ == '__main__':
    bot_interface = BotInterface(community_token, access_token)
    bot_interface.event_handler()