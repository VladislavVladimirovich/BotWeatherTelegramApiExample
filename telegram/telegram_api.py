import json
import logging
import requests


class ConfigTelegramBot:

    _URL = 'https://api.telegram.org/bot{TOKEN}/'
    _URL_UPDATE = _URL + 'getUpdates'
    _URL_SEND_TEXT = _URL + 'sendMessage'
    _URL_SEND_PHOTO = _URL + 'sendPhoto'
    _TEST_TOKEN = _URL + 'getMe'

    _TIMEOUT_REQUESTS = 5


class TelegramApi(ConfigTelegramBot):

    def __init__(self, token: str):
        self.__token = None
        self.status_set_token = None
        self.set_token(token=token)

    def update(self) -> list:
        messages = []
        try:
            result = requests.get(
                url=self._URL_UPDATE.format(TOKEN=self.__token), timeout=self._TIMEOUT_REQUESTS
            )
            messages = result.json().get('result', list())
        except requests.RequestException:
            logging.exception('TelegramApi.getUpdates: ')
        except json.JSONDecodeError:
            logging.exception('TelegramApi.getUpdates: ')
        finally:
            return messages

    def send_message(self, data: dict):
        result = None
        try:
            result = requests.post(
                url=self._URL_SEND_TEXT.format(TOKEN=self.__token), data=data, timeout=self._TIMEOUT_REQUESTS
            )
        except requests.RequestException:
            logging.exception('TelegramApi.sendMessage: ')
        return result

    def send_photo(self, data: dict, **kwargs):
        result = None
        try:
            result = requests.post(
                url=self._URL_SEND_PHOTO.format(TOKEN=self.__token), data=data, timeout=self._TIMEOUT_REQUESTS, **kwargs
            )
        except requests.RequestException:
            logging.exception('TelegramApi.sendPhoto: ')
        return result

    def set_token(self, token) -> dict:
        """ Установка token для работы с ботом """
        result = {
            "ok": False,
            "error_code": 0,
            "description": f"unknown error, view log file"
        }
        try:
            result = requests.get(self._TEST_TOKEN.format(TOKEN=token), timeout=self._TIMEOUT_REQUESTS)
            result = result.json()
            if not result.get('ok', None):
                logging.warning(f'Invalid Telegram Token : {token}')
        except requests.RequestException:
            logging.exception('TelegramApi.set_token: ')
        except json.JSONDecodeError:
            logging.exception('TelegramApi.set_token: ')
        else:
            self.__token = token
            self.status_set_token = result
        finally:
            return result
