import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from config import comunity_token, access_token
from core import VkTools
from data_store import add_to_db, get_from_db

class BotInterface():
    def __init__(self, comunity_token, access_token):
        self.interface = vk_api.VkApi(token=comunity_token)
        self.api = VkTools(access_token)
        self.params = None

    def message_send(self, user_id, message, attachment=None):
        self.interface.method('messages.send', {
            'user_id': user_id,
            'message': message,
            'attachment': attachment,
            'random_id': get_random_id()
        })

    def handle_greeting(self, event):
        self.params = self.api.get_profile_info(event.user_id)
        if self.params['city'] is None:
            self.message_send(event.user_id, f'Здравствуй, {self.params["name"]}! Пожалуйста, укажите ваш город.')
        elif self.params['bdate'] is None:
            self.message_send(event.user_id,
                              f'Здравствуй, {self.params["name"]}! Пожалуйста, укажите вашу дату рождения или возраст.')
        else:
            self.message_send(event.user_id, f'Здравствуй, {self.params["name"]}!')

    def handle_message(self, event):
        if self.params and self.params['city'] is None:
            city = event.text.strip()
            self.params['city'] = city
            self.message_send(event.user_id, f'Спасибо, {self.params["name"]}. Город успешно обновлен.')
        elif self.params and self.params['bdate'] is None:
            bdate = event.text.strip()  # Получаем введенную дату рождения или возраст
            self.params['bdate'] = bdate
            self.message_send(event.user_id,
                              f'Спасибо, {self.params["name"]}. Дата рождения или возраст успешно обновлены.')
        else:
            self.message_send(event.user_id, 'Команда не распознана.')

    def handle_search(self, event):
        if self.params:
            if self.params['city'] is None:
                self.message_send(event.user_id, f'{self.params["name"]}, пожалуйста, укажите ваш город.')
            else:
                viewed_profiles = get_from_db(event.user_id)
                params = self.params.copy()
                # params['city'] = None  # Сброс города из параметров для поиска

                offset = 0  # Начальное значение сдвига (offset)
                count = 10  # Количество анкет для каждого поискового запроса
                total_users = []  # Общий список найденных анкет

                while len(total_users) < count:
                    params['offset'] = offset  # Установка сдвига (offset) в параметры поиска
                    users = self.api.search_users(params)
                    filtered_users = [user for user in users if user['id'] not in viewed_profiles]
                    total_users.extend(filtered_users)  # Добавление найденных анкет в общий список
                    offset += len(users)  # Увеличение сдвига (offset) на количество найденных анкет

                    if len(users) < count:
                        break  # Прерывание цикла, если количество найденных анкет меньше заданного

                if total_users:
                    user = total_users.pop(0)  # Получение первой анкеты из общего списка
                    photos_user = self.api.get_photos(user['id'])
                    photos_user = sorted(photos_user, key=lambda x: x['likes'] + x['comments'] * 10,
                                         reverse=True)  # Сортировка фото по лайкам и комментариям
                    attachment = ''
                    for photo in photos_user[:3]:  # Выводим три лучшие фото
                        photo_attachment = f'photo{photo["owner_id"]}_{photo["id"]}'
                        attachment += f'{photo_attachment},'
                    attachment = attachment.rstrip(',')
                    self.message_send(event.user_id,
                                      f'Встречайте {user["name"]}\nПрофиль: https://vk.com/id{user["id"]}',
                                      attachment=attachment)
                    add_to_db(event.user_id, user['id'])
                else:
                    self.message_send(event.user_id, 'Нет больше подходящих пользователей.')
        else:
            self.message_send(event.user_id, 'Укажите информацию о себе командой "привет".')

    def handle_goodbye(self, event):
        self.message_send(event.user_id, 'Пока! Ждем вас снова.')

    def handle_unknown_command(self, event):
        self.message_send(event.user_id, 'Команда не распознана.')

    def event_handler(self):
        longpoll = VkLongPoll(self.interface)

        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    self.handle_greeting(event)
                elif event.text.lower() == 'поиск':
                    self.handle_search(event)
                elif event.text.lower() == 'пока':
                    self.handle_goodbye(event)
                else:
                    self.handle_message(event)

if __name__ == '__main__':
    bot = BotInterface(comunity_token, access_token)
    bot.event_handler()
