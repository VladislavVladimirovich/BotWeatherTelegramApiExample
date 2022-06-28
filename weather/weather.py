import requests
import json
import logging
from db import session as db_session, ImageWeather


class ConfigWeather:

    LANGUAGE = 'ru'             # язык ответа
    UNITS = 'metric'            # единица измерения температуры
    TIME_BETWEEN_REQUESTS = 3   # пауза между запросами сообщений getUpdates

    __URL = 'https://api.openweathermap.org/data/2.5/weather?appid={WEATHER_API}'
    _URL_API = None
    _PATH_ICON = 'weather/icon/'
    _FORMAT_ICON = '@2x.png'
    _URL_GET_WEATHER_ICON = 'http://openweathermap.org/img/wn/{FILE_NAME}'


class Weather(ConfigWeather):
    def __init__(self, api: str):
        self.status_set_token = None
        self.set_api(api)

    def get_weather(self, data: str | tuple | int) -> dict:
        """ Получение погоды """
        url = self.__define_method_get_data(data)
        result = self.__get_weather(url)
        if result.get('weather', None):
            result['weather'][0]['icon'] = self.__get_icon(result)
        return result

    def __define_method_get_data(self, data) -> str:
        """ Определение метода получения погоды (str city, int city_id, coordinates tuple(lat, lon))"""
        if isinstance(data, str):
            return self._URL_API.format(CITY=data) + f'lang={self.LANGUAGE}&units={self.UNITS}&q={data}'
        elif isinstance(data, int):
            return self._URL_API.format(CITY=data) + f'lang={self.LANGUAGE}&units={self.UNITS}&id_city={data}'
        elif isinstance(data, tuple):
            return self._URL_API.format(CITY=data) + f'lang={self.LANGUAGE}&units={self.UNITS}&lat={data[0]}&lon={data[1]}'

    @staticmethod
    def __get_weather(url: str) -> dict:
        """ Запрос на получение данных о погоде """
        try:
            result = requests.get(url=url, timeout=3)
            json_data = result.json()
            return json_data
        except json.JSONDecodeError as Err:
            logging.debug(f'WEATHER - {Err}')
            return {'cod': '', 'message': 'weather server response data error'}
        except Exception as Ex:
            logging.warning(f"__get_weather: {Ex}")

    def __download_icon(self, name: str, path: str) -> bool:
        """ Загрузка icon """
        url_icon = self._URL_GET_WEATHER_ICON.format(FILE_NAME=name)
        try:
            result = requests.get(url_icon)
            if result.status_code != 200:
                raise requests.RequestException(f"Requests status code error : {result.status_code}")
            with open(path, 'wb') as file:
                file.write(result.content)
        except requests.RequestException:
            logging.exception('Weather.__download_icon: ')
        else:
            return True

        return False

    def __get_icon(self, data_weather: dict) -> object | None:
        """ Получение объекта icon """
        icon_name = data_weather['weather'][0]['icon'] + self._FORMAT_ICON
        db_icon = db_session.query(ImageWeather).filter_by(name=icon_name).first()
        if db_icon is not None:
            return db_icon
        # file_name = FILE_ICON_NAME.format(name=icon_name)
        # path = ROOT_DIR + f'/icon/{file_name}'
        path = self._PATH_ICON + icon_name
        if not self.__download_icon(icon_name, path):
            return None

        new_img_db = ImageWeather(name=icon_name, path=path)
        db_session.add(new_img_db)
        db_session.commit()
        return new_img_db

    def set_api(self, api: str) -> bool:
        """ Установить api key """
        url = f'https://api.openweathermap.org/data/2.5/weather?appid={api}&'
        result = False
        try:
            res = requests.get(url=url, timeout=self.TIME_BETWEEN_REQUESTS)
            if 'Invalid API key' not in res:
                self.status_set_token = True
                self._URL_API = url
                result = True
            else:
                logging.warning(f'Invalid Weather API key : {api}')
        except requests.RequestException:
            logging.exception('TelegramApi.getUpdates: ')
        except json.JSONDecodeError:
            logging.exception('TelegramApi.getUpdates: ')
        finally:
            return result
