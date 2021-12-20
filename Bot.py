import random
import time

import requests
import json

from Logger import Logger


class Bot:
    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)

        self.logger = Logger()
        self.logger.recover()

        self.questions = self.logger.main_log_data['questions_assignment']
        self.stats = self.logger.main_log_data['stats']
        self.name = self.logger.main_log_data['name']

        self.offset = 0

        self.commands_handlers = {
            '/start': self.start_command_handler,
            '/question': self.question_command_handler,
            '/help': self.help_command_handler,
            '/stats': self.stats_command_handler,
            '/leaderboard': self.leaderboard_command_handler
        }

        self.questions_list = dict()
        self.theme_list = dict()
        self.theme_list["Random"] = []
        self.name = dict()

        with open('questions_list.json', encoding='utf-8') as f:
            tmp = json.load(f)
        for question in tmp:
            cur_id = question['id']
            if question["theme"] not in self.theme_list:
                self.theme_list[question["theme"]] = []
            self.theme_list[question["theme"]].append(cur_id)
            self.theme_list["Random"].append(cur_id)
            self.questions_list[question["id"]] = question

    def get_updates(self, timeout=30):
        params = {"timeout": timeout, "offset": self.offset}
        resp = requests.get(self.api_url + "getUpdates", params).json()
        if "result" not in resp:
            return []
        return resp["result"]

    def leaderboard_command_handler(self, chat_id, update):
        top = []
        in_top = set()
        for i in range(10):
            mx = -1
            best_chat_id = -1
            for x in self.stats:
                if x in in_top:
                    continue
                if self.stats[x][0] > mx:
                    mx = self.stats[x][0]
                    best_chat_id = x
            if mx == -1:
                break
            in_top.add(best_chat_id)
            top.append([best_chat_id, mx])
        text = f"Список лидеров:\n"
        for i in range(len(top)):
            if i > 0:
                text += f"\n"
            text += f"{i + 1}. {self.name[top[i][0]]}: {top[i][1]} ответов."
        self.send_message(chat_id, text)

    def stats_command_handler(self, chat_id, update):
        correct = 0
        total = 0
        if chat_id in self.stats:
            correct = self.stats[chat_id][0]
            total = self.stats[chat_id][1]
        message = f"Вы правильно ответили на {correct} из {total} вопросов.\n" \
                  f"Ваш процент правильных ответов равен {correct * 100 // max(total, 1)}%."
        self.send_message(chat_id, message)

    def start_command_handler(self, chat_id, update):
        if 'username' in update['message']['from']:
            greetings_message = 'Здравствуйте, {}!'.format(update['message']['from']['username'])
        elif 'first_name' in update['message']['from'] and 'last_name' in update['message']['from']:
            greetings_message = 'Здравствуйте, {} {}!'.format(update['message']['from']['first_name'],
                                                              update['message']['from']['last_name'])
        else:
            greetings_message = 'Здравствуйте!'

        self.send_message(chat_id, greetings_message)

    def choose_theme(self, chat_id):
        text = "Пожалуйста, выберите тему."
        variants = []
        for v in self.theme_list:
            variants.append(v)
        self.give_text_question(chat_id, text, variants)

    def question_command_handler(self, chat_id, update):
        self.choose_theme(chat_id)
        self.questions[chat_id] = -1
        self.logger.add_to_log(operation_type='next', chat_id=chat_id, question_id=-1)

    def help_command_handler(self, chat_id, update):
        self.send_message(chat_id, 'Памагити...')

    def choose_theme_question(self, chat_id, theme):
        question_id = self.theme_list[theme][random.randint(0, len(self.theme_list[theme]) - 1)]
        self.questions[chat_id] = question_id
        self.logger.add_to_log(operation_type='next', chat_id=chat_id, question_id=question_id)
        reply_text = '{}'.format(self.questions_list[question_id]["question"])
        wrong_answers = self.questions_list[question_id]["wrong_answers"]
        random.shuffle(wrong_answers)
        variants = wrong_answers[0:3]
        variants.append(self.questions_list[question_id]["answer"])
        random.shuffle(variants)
        if self.questions_list[question_id]["photo"] == 0:
            self.give_text_question(chat_id, reply_text, variants)
        else:
            self.give_photo_question(chat_id, self.questions_list[question_id]["link"], reply_text, variants)

    def simple_text_handler(self, chat_id, update):
        question_id = self.questions.pop(chat_id, None)
        if question_id is None:
            reply_text = 'Сейчас у Вас нет активного вопроса'
            self.send_message(chat_id, reply_text)
            self.logger.add_to_log(operation_type='answer', chat_id=chat_id, status='not_active')
        elif question_id == -1:
            if update['message']['text'] not in self.theme_list:
                self.send_message(chat_id, "Такой темы нет!")
            else:
                self.choose_theme_question(chat_id, update['message']['text'])
        elif self.questions_list[question_id]["answer"] == update['message']['text']:
            if chat_id not in self.stats:
                self.stats[chat_id] = [0, 0]
            self.stats[chat_id][0] += 1
            self.stats[chat_id][1] += 1
            self.send_message(chat_id, "Верный ответ!")
            self.logger.add_to_log(operation_type='answer', chat_id=chat_id, status='ok')
        else:
            if chat_id not in self.stats:
                self.stats[chat_id] = [0, 0]
            self.stats[chat_id][1] += 1
            self.send_message(chat_id, "Неправильный ответ")
            self.logger.add_to_log(operation_type='answer', chat_id=chat_id, status='wrong')

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

    def give_text_question(self, chat_id, text, variants):
        keyboard = []
        for v in variants:
            keyboard.append([v])
        params = {"chat_id": chat_id, "text": text, "reply_markup": json.dumps({"keyboard": keyboard, "one_time_keyboard": True})}
        requests.post(self.api_url + "sendMessage", params)

    def give_photo_question(self, chat_id, link, text, variants):
        keyboard = []
        for v in variants:
            keyboard.append([v])
        params = {"chat_id": chat_id, "photo": link, "caption": text, "reply_markup": json.dumps({"keyboard": keyboard, "one_time_keyboard": True})}
        requests.post(self.api_url + "sendPhoto", params)

    def send_message(self, chat_id, text):
        params = {"chat_id": chat_id, "text": text}
        return requests.post(self.api_url + "sendMessage", params)

    def process_update_name(self, update):
        chat_id = update['message']['chat']['id']
        if chat_id in self.name:
            return
        if "username" in update["message"]["from"]:
            self.name[chat_id] = update["message"]["from"]["username"]
        else:
            self.name[chat_id] = update["message"]["from"]["first_name"]
        self.logger.add_to_log(operation_type='add_name', chat_id=chat_id, name=self.name[chat_id])

    def main_loop(self):
        while True:
            updates = self.get_updates()
            for update in updates:
                print(update)
                update["message"]["chat"]["id"] = str(update["message"]["chat"]["id"])
                self.process_update_name(update)
                self.process_update(update)
                self.offset = max(self.offset, update['update_id'] + 1)
            time.sleep(1)
