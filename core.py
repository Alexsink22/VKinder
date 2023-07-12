from datetime import datetime
import vk_api

from config import access_token

class VkTools():
    def __init__(self, access_token):
        self.api = vk_api.VkApi(token=access_token)

    def get_profile_info(self, user_id):
        info = self.api.method('users.get', {
            'user_id': user_id,
            'fields': 'city,bdate,sex,relation,home_town'
        })[0]

        user_info = {
            'name': f"{info.get('first_name', '')} {info.get('last_name', '')}",
            'id': info.get('id'),
            'bdate': info.get('bdate'),  # Получаем дату рождения из профиля пользователя
            'home_town': info.get('home_town'),
            'sex': info.get('sex'),
            'city': info['city'].get('id') if 'city' in info else None
        }
        return user_info

    def search_users(self, params):
        city_name = params['city']
        city_id = self.get_city_id(city_name)  # Получение идентификатора города по названию
        if city_id is None:
            raise ValueError(f"Invalid city: {city_name}")

        sex = 1 if params['sex'] == 2 else 2
        current_year = datetime.now().year
        user_year = int(params['bdate'].split('.')[2])
        age = current_year - user_year
        age_from = age - 5
        age_to = age + 5

        users = self.api.method('users.search', {
            'count': 50,
            'offset': 0,
            'age_from': age_from,
            'age_to': age_to,
            'sex': sex,
            'city': city_id,  # Используем идентификатор города в запросе
            'status': 6,
            'is_closed': False
        }).get('items', [])

        res = [{
            'id': user['id'],
            'name': f"{user.get('first_name', '')} {user.get('last_name', '')}"
        } for user in users if not user['is_closed']]

        return res

    def get_city_id(self, city_name):
        response = self.api.method('database.getCities', {
            'country_id': 1,  # Идентификатор России, можно изменить в зависимости от страны
            'q': city_name
        })

        if response['count'] > 0:
            city = response['items'][0]
            return city['id']

        return None

    def get_photos(self, user_id):
        photos = self.api.method('photos.get', {
            'user_id': user_id,
            'album_id': 'profile',
            'extended': 1
        }).get('items', [])

        res = [{
            'owner_id': photo['owner_id'],
            'id': photo['id'],
            'likes': photo['likes']['count'],
            'comments': photo['comments']['count']
        } for photo in photos]

        res.sort(key=lambda x: x['likes'] + x['comments'] * 10, reverse=True)

        return res

# Создаем экземпляр класса VkTools
vk_tools = VkTools(access_token)
