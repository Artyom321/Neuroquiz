#!/usr/bin/env python

import requests
import json
import datetime
import time
import argparse
import os
import random

import re

from Logger import Logger


class BotHandler(object):
    def __init__(self, token, logger):
        self.logger = logger
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)

        self.questions = self.logger.main_log_data['questions_assignment']

    def get_updates(self, offset=None, timeout=30):
        params = {"timeout": timeout, "offset": offset}
        resp = requests.get(self.api_url + "getUpdates", params).json()
        if "result" not in resp:
            return []
        return resp["result"]

    def send_message(self, chat_id, text):
        params = {"chat_id": chat_id, "text": text}
        return requests.post(self.api_url + "sendMessage", params)

    def bot_answer_text(self, update, text_question):
        if text_question == '/start':
            return "Test EGE-bot please tell me what you want"
        elif text_question == '/next':
            new_question = random.randint(1, 100)
            chat_id = str(update["message"]["chat"]['id'])
            self.questions[chat_id] = new_question
            self.logger.add_to_log(operation_type='next', chat_id=chat_id, question_id=new_question)
            return 'New question: {}'.format(new_question)
        else:
            chat_id = str(update["message"]["chat"]['id'])
            right_answer = self.questions.pop(chat_id, None)
            self.logger.add_to_log(operation_type='answer', chat_id=chat_id)
            if right_answer is None:
                return 'You don\'t have an active question'
            if str(right_answer) == text_question:
                return 'OK'
            else:
                return 'Wrong answer'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', type=str, default='')
    args = parser.parse_args()

    token = args.token
    if not token:
        if not "TELEGRAM_TOKEN" in os.environ:
            print(
                "Please, set bot token through --token or TELEGRAM_TOKEN env variable"
            )
            return
        token = os.environ["TELEGRAM_TOKEN"]

    logger = Logger()
    logger.recover()

    bot = BotHandler(token, logger)
    offset = 0
    
    while True:
        updates = bot.get_updates(offset=offset)
        for update in updates:
            print(update)
            chat_id = update["message"]["chat"]["id"]
            if "text" in update["message"]:
                bot.send_message(chat_id, bot.bot_answer_text(update, update["message"]["text"]))
            offset = max(offset, update['update_id'] + 1)

        time.sleep(1)


if __name__ == "__main__":
    main()
