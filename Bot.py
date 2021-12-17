import random
import time

import requests

from Logger import Logger


class Bot:
    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)

        self.logger = Logger()
        self.logger.recover()

        self.questions = self.logger.main_log_data['questions_assignment']

        self.offset = 0

        self.commands_handlers = {
            '/start': self.start_command_handler,
            '/next': self.next_command_handler,
            '/help': self.help_command_handler,
        }

    def get_updates(self, timeout=30):
        params = {"timeout": timeout, "offset": self.offset}
        resp = requests.get(self.api_url + "getUpdates", params).json()
        if "result" not in resp:
            return []
        return resp["result"]

    def start_command_handler(self, chat_id, update):
        greetings_message = 'Здравствуйте, {}!'.format(update['message']['from']['username'])
        self.send_message(chat_id, greetings_message)

    def next_command_handler(self, chat_id, update):
        question_id = random.randint(1, 100)
        self.questions[chat_id] = question_id
        self.logger.add_to_log(operation_type='next', chat_id=chat_id, question_id=question_id)
        reply_text = 'Вопрос: введите число {}'.format(question_id)
        self.send_message(chat_id, reply_text)

    def help_command_handler(self, chat_id, update):
        self.send_message(chat_id, 'Памагити...')

    def simple_text_handler(self, chat_id, update):
        question_id = self.questions.pop(chat_id, None)
        self.logger.add_to_log(operation_type='answer', chat_id=chat_id)
        if question_id is None:
            reply_text = 'Сейчас у Вас нет активного вопроса'
        elif str(question_id) == update['message']['text']:
            reply_text = 'Верный ответ!'
        else:
            reply_text = 'Неверный ответ'
        self.send_message(chat_id, reply_text)

    def process_update(self, update):
        if 'message' not in update:
            return
        chat_id = str(update['message']['chat']['id'])
        if 'text' not in update['message']:
            return
        if update['message']['text'] in self.commands_handlers:
            self.commands_handlers[update['message']['text']](chat_id, update)
            return
        self.simple_text_handler(chat_id, update)

    def send_message(self, chat_id, text):
        params = {"chat_id": chat_id, "text": text}
        return requests.post(self.api_url + "sendMessage", params)

    def main_loop(self):
        while True:
            updates = self.get_updates()
            for update in updates:
                print(update)
                self.process_update(update)
                self.offset = max(self.offset, update['update_id'] + 1)
            time.sleep(1)
