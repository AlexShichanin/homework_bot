import requests
import os
import sys
import logging
import time
import telegram
import telegram.ext
from http import HTTPStatus
from dotenv import load_dotenv
from xmlrpc.client import ResponseError

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s'
                              ' %(name)s - %(message)s')

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступности переменных окружения."""
    logger.info('Проверка окружения')
    token_check = PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID
    if token_check:
        return True
    return False


def send_message(bot, message):
    """Сообщения в телеграмм чат."""
    try:
        logger.debug('Сообщение отпрвлено в чат!')
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Сообщение отправлено успешно!')
    except Exception as error:
        logger.error(f'Сообщение не отправлено в связи с {error}')
        raise SystemError(f'Сообщение не было отправлено {error}')


def get_api_answer(timestamp):
    """Получаем ответ от API Yandex."""
    try:
        response = requests.get(url=ENDPOINT,
                                headers=HEADERS,
                                params={'from_date': timestamp})
        if response.status_code != HTTPStatus.OK:
            logger.critical('Возникла ошибка endpoint недоступен')
            raise ValueError('Получено неверное значение')
        return response.json()
    except Exception as error:
        raise ValueError(f'Возникла ошибка при работе с API! {error}')


def check_response(response):
    """Проверка ответа endpoaint."""
    if not isinstance(response, dict):
        raise TypeError('Некорректный тип данных !')
    elif 'homeworks' not in response:
        raise ResponseError('Homeworks отсутсвует !')
    elif 'current_date' not in response:
        raise ResponseError('Ключ current_date отсутствует !')
    elif not isinstance(response['homeworks'], list):
        raise TypeError('Некоректный тип данных!')
    return response.get('homeworks')


def parse_status(homework: dict):
    """Поиск статуса Homework."""
    status = homework.get('status')
    homework_name = homework.get('homework_name')
    if 'homework_name' not in homework or None:
        logger.critical('Отсутствуют данные')
        raise KeyError(f'Отсутсвует необходимый ключ {homework_name}')
    if status not in HOMEWORK_VERDICTS or None:
        logger.error('Недокументированный статус домашней работы')
        raise Exception('Некорректный статус')
    verdict = HOMEWORK_VERDICTS.get(status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Возникла ошибка с токенами')
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    send_message(bot, 'Practicum_bot активирован')
    timestamp = int(time.time()) - 5184000
    last_status = ''
    while True:
        try:
            responce = get_api_answer(timestamp)
            homework = check_response(responce)
            if homework:
                status = parse_status(homework[0])
                new_satatus = homework[0]['status']
                if new_satatus != last_status:
                    send_message(bot, status)
                    last_status = new_satatus
                else:
                    logger.debug('Нет обновлений')
            if status == '' or None:
                logger.critical('Неверный статус или пустой статус')
                raise ValueError('Ошибка статуса')
        except telegram.TelegramError:
            logger.error(' Не удалость отправить сообщение!')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            return message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
