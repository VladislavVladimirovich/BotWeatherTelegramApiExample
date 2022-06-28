import time
from keys import WEATHER_API_KEY, TOKEN_BOT
from logging_settings import logger

from weather import Weather
from telegram import TelegramApi
from db import session as db_session, Users


class SettingsBot:
    TIME_BETWEEN_REQUESTS = 5   # пауза между запросами сообщений getUpdates


class BotWeather(SettingsBot):
    def __init__(self, telegram_api: TelegramApi, weather_api: Weather):
        self.telegram_api = telegram_api
        self.weather_api = weather_api
        self.status_work_bot = False
        self.db_users = db_session.query(Users)

    def run_bot(self):
        self.status_work_bot = True
        self.__loop()

    def stop_bot(self):
        self.status_work_bot = False

    def __loop(self):
        while self.status_work_bot:
            all_messages = self.__get_messages()
            if all_messages:
                filter_messages = self.__filter_messages(all_messages)
                if filter_messages:
                    self.__response_handler(filter_messages)
            time.sleep(self.TIME_BETWEEN_REQUESTS)

    def __get_messages(self) -> list:
        """ Получение всех сообщений """
        return self.telegram_api.update()

    def __filter_messages(self, messages: list) -> list:
        """ Отфильтровать сообщения """
        filter_messages = list()
        for message in messages[::-1]:
            d_user = self.db_users.filter_by(id=message['message']['from']['id']).first()
            if not d_user:
                logger.info(f"unknown user : {message['message']['from']}")
                continue

            if message['update_id'] <= d_user.updateId:
                continue

            if not d_user.updateId == 0:
                filter_messages.append(message)

            d_user.updateId = message['update_id']
            db_session.commit()

        return filter_messages

    @staticmethod
    def __form_response(message: dict, weather: dict) -> dict:
        """ Формирование ответа на запрос """
        data = dict(chat_id=message['message']['chat']['id'], reply_to_message_id=message['message']['message_id'])
        if not weather['cod'] == 200:
            logger.info(f"runBot.__form_response : data error: {weather['message']}")
            data.update({'text': weather['message']})
            return data
        text = f'{weather["weather"][0]["description"].capitalize()}\n' \
               f'🌏 ({weather["sys"]["country"]}){weather["name"]}({weather["id"]})\n' \
               f'🌡 {weather["main"]["temp_min"]} < {weather["main"]["temp"]} > {weather["main"]["temp_max"]} ℃\n' \
               f'💨 {weather["wind"]["speed"]} метр/сек., ☁️ {weather["clouds"]["all"]}%'
        data.update({'caption': text})
        return data

    @staticmethod
    def __define_data_type(message: dict) -> str | int | tuple:
        """ Определение типа запрашиваемых данных (str city, int city_id, coordinates tuple(lat, lon)) """
        if message.get('location'):
            return message['location']['latitude'], message['location']['longitude']
        elif message.get('text'):
            if message['text'].isdigit():
                return int(message['text'])
            else:
                return message['text']
        else:
            return ""

    def __get_weather(self, message: dict) -> dict:
        """ Получить погоду """
        return self.weather_api.get_weather(self.__define_data_type(message['message']))

    @staticmethod
    def __get_photo_path(path):
        with open(path, 'rb') as f:
            file_ = f.read()
        return file_

    def __response_handler(self, messages: list):
        """ Отправка ответа"""
        for message in messages:
            data_weather = self.__get_weather(message)

            # Если ошибка ответа сервера погоды
            if not data_weather['cod'] == 200:
                data = self.__form_response(message=message, weather=data_weather)
                self.telegram_api.send_message(data=data)
                continue
            # Если ошибка получения icon
            if data_weather['weather'][0]['icon'] is None:
                data = self.__form_response(message=message, weather=data_weather)
                self.telegram_api.send_message(data=data)
                continue
            # Если icon ранее не был загружен в telegram
            if data_weather['weather'][0]['icon'].telegram_key is None:
                data = self.__form_response(message=message, weather=data_weather)
                str_photo = self.__get_photo_path(data_weather['weather'][0]['icon'].path)
                response = self.telegram_api.send_photo(data, files={'photo': str_photo})
                if not response:
                    continue
                response = response.json()
                if response.get('ok'):
                    data_weather['weather'][0]['icon'].telegram_key = response['result']['photo'][1]['file_id']
                    db_session.commit()
                continue
            # Если все ОК
            else:
                data = self.__form_response(message=message, weather=data_weather)
                data.update({'photo': data_weather['weather'][0]['icon'].telegram_key})
                self.telegram_api.send_photo(data, files={'photo': data_weather['weather'][0]['icon'].path})

    def set_user(self, id_: int, userName: str = None, lastName: str = None, firstName: str = None, updateId: int = 0):
        """ Добавить пользователя для доступа к боту, id - пользователя в телеге"""
        new_user = Users(id_, userName, lastName, firstName, updateId)
        db_session.add(new_user)
        db_session.commit()
        self.db_users = db_session.query(Users)


if __name__ == "__main__":

    api_telegram = TelegramApi(token=TOKEN_BOT)
    api_weather = Weather(api=WEATHER_API_KEY)

    if not api_weather.status_set_token or \
            not api_telegram.status_set_token or \
            not api_telegram.status_set_token.get("ok"):

        logger.warning("Error, view log file")
        exit(1)

    bot = BotWeather(telegram_api=api_telegram, weather_api=api_weather)
    bot.run_bot()
