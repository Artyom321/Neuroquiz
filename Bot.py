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
        self.last_theme = self.logger.main_log_data['last_theme']
        self.last_markup = dict()

        self.offset = 0

        self.commands_handlers = {
            '/start': self.start_command_handler,
            '/leaderboard': self.leaderboard_command_handler,
            '/help': self.help_command_handler,
            '/stats': self.stats_command_handler,
            '/rand': self.rand_command_handler,
            '/theme': self.theme_command_handler,
            '/rep': self.rep_command_handler,
            '/credits': self.credits_command_handler,
            '/secret': self.secret_command_handler
        }

        self.questions_list = dict()
        self.theme_list = dict()
        self.theme_list["Случайная тема"] = []
        self.theme_list["Секрет"] = []

        with open('questions_list.json', encoding='utf-8') as f:
            tmp = json.load(f)
        for question in tmp:
            cur_id = question['id']
            if question["theme"] not in self.theme_list:
                self.theme_list[question["theme"]] = []
            self.theme_list[question["theme"]].append(cur_id)
            if question["id"] == 0:
                self.theme_list["Секрет"].append(cur_id)
            self.theme_list["Случайная тема"].append(cur_id)
            self.questions_list[question["id"]] = question

    def get_updates(self, timeout=30):
        params = {"timeout": timeout, "offset": self.offset}
        resp = requests.get(self.api_url + "getUpdates", params).json()
        if "result" not in resp:
            return []
        return resp["result"]

    def secret_command_handler(self, chat_id, update):
        self.choose_theme_question(chat_id, "Секрет")

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
        text = f"Список лидеров (количество правильных ответов):\n"
        for i in range(len(top)):
            if i > 0:
                text += f"\n"
            text += f"{i + 1}. {self.name[str(top[i][0])]} - {top[i][1]}"
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

    def rand_command_handler(self, chat_id, update):
        theme = "Случайная тема"
        self.choose_theme_question(chat_id, theme)

    def start_command_handler(self, chat_id, update):
        greetings_message = open('bot_info_messages/greetings.txt', 'r', encoding='utf-8').read().replace('{{name}}', self.name[chat_id])
        self.send_message(chat_id, greetings_message)

    def credits_command_handler(self, chat_id, update):
        credits_message = open('bot_info_messages/credits.txt', 'r', encoding='utf-8').read()
        self.send_message(chat_id, credits_message)

    def choose_theme(self, chat_id):
        text = "Пожалуйста, выберите тему."
        variants = []
        for v in self.theme_list:
            if v != "Случайная тема" and v != "Секрет":
                variants.append(v)
        self.give_text_question(chat_id, text, variants)

    def theme_command_handler(self, chat_id, update):
        self.choose_theme(chat_id)
        self.questions[chat_id] = [-1, -1]
        self.logger.add_to_log(operation_type='next', chat_id=chat_id, question_id=[-1, -1])

    def help_command_handler(self, chat_id, update):
        help_message = open('bot_info_messages/help.txt', 'r', encoding='utf-8').read()
        self.send_message(chat_id, help_message)

    def choose_theme_question(self, chat_id, theme):
        question_id = self.theme_list[theme][random.randint(0, len(self.theme_list[theme]) - 1)]
        self.last_theme[chat_id] = self.questions_list[question_id]['theme']
        self.logger.add_to_log(operation_type='last_theme_update', chat_id=chat_id, theme=self.last_theme[chat_id])
        reply_text = self.questions_list[question_id]["question"]
        reply_text += "\nВарианты ответов:"
        wrong_answers = self.questions_list[question_id]["wrong_answers"]
        random.shuffle(wrong_answers)
        variants = wrong_answers[0:3]
        cnt_correct = len(self.questions_list[question_id]["answer"])
        answer = self.questions_list[question_id]["answer"][random.randint(0, cnt_correct - 1)]
        variants.append(answer)
        random.shuffle(variants)
        correct = 0
        for i in range(4):
            reply_text += '\n' + str(i + 1) + '. ' + variants[i]
            if variants[i] == answer:
                correct = i + 1

        self.questions[chat_id] = [question_id, correct]
        self.logger.add_to_log(operation_type='next', chat_id=chat_id, question_id=[question_id, correct])

        if self.questions_list[question_id]["photo"] == 0:
            self.give_text_question(chat_id, reply_text, ["1", "2", "3", "4"])
        else:
            self.give_photo_question(chat_id, self.questions_list[question_id]["link"], reply_text, ["1", "2", "3", "4"])

    def rep_command_handler(self, chat_id, update):
        if chat_id not in self.last_theme:
            self.send_message(chat_id, "Вы ещё не задавали вопросов")
        else:
            self.choose_theme_question(chat_id, self.last_theme[chat_id])

    def simple_text_handler(self, chat_id, update):
        question_id = self.questions.pop(chat_id, None)
        if question_id is None:
            reply_text = 'Сейчас у Вас нет активного вопроса'
            self.send_message(chat_id, reply_text)
            self.logger.add_to_log(operation_type='answer', chat_id=chat_id, status='not_active')
        elif question_id == [-1, -1]:
            if update['message']['text'] not in self.theme_list:
                self.send_message(chat_id, "Такой темы нет!")
            else:
                self.choose_theme_question(chat_id, update['message']['text'])
        elif str(question_id[1]) == update['message']['text']:
            if chat_id not in self.stats:
                self.stats[chat_id] = [0, 0]
            self.stats[chat_id][0] += 1
            self.stats[chat_id][1] += 1
            self.logger.add_to_log(operation_type='answer', chat_id=chat_id, status='ok')
            self.send_message(chat_id, "Верный ответ!")
            keyboard = []
            keyboard.append([{"text": "Вопрос на ту же тему", "callback_data": "/rep"}])
            keyboard.append([{"text": "Случайный вопрос", "callback_data": "/rand"}])
            keyboard.append([{"text": "Моя статистика", "callback_data": "/stats"}])
            params = {"chat_id": chat_id, "text": "Предлагаем Вам:",
                      "reply_markup": json.dumps({"inline_keyboard": keyboard, "one_time_keyboard": True})}
            while True:
                res = requests.post(self.api_url + "sendMessage", params).json()
                if "result" not in res:
                    continue
                self.last_markup[chat_id] = res["result"]["message_id"]
                break
        else:
            if chat_id not in self.stats:
                self.stats[chat_id] = [0, 0]
            self.stats[chat_id][1] += 1
            self.logger.add_to_log(operation_type='answer', chat_id=chat_id, status='wrong')
            self.send_message(chat_id, f"Неправильный ответ.\nПравильный ответ: {question_id[1]}.")
            keyboard = []
            keyboard.append([{"text": "Вопрос на ту же тему", "callback_data": "/rep"}])
            keyboard.append([{"text": "Случайный вопрос", "callback_data": "/rand"}])
            keyboard.append([{"text": "Моя статистика", "callback_data": "/stats"}])
            params = {"chat_id": chat_id, "text": "Предлагаем Вам:",
                      "reply_markup": json.dumps({"inline_keyboard": keyboard, "one_time_keyboard": True})}
            while True:
                res = requests.post(self.api_url + "sendMessage", params).json()
                if "result" not in res:
                    continue
                self.last_markup[chat_id] = res["result"]["message_id"]
                break

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
            keyboard.append([{"text": v, "callback_data": v}])
        params = {"chat_id": chat_id, "text": text, "reply_markup": json.dumps({"inline_keyboard": keyboard, "one_time_keyboard": True})}
        while True:
            res = requests.post(self.api_url + "sendMessage", params).json()
            if "result" not in res:
                continue
            self.last_markup[chat_id] = res["result"]["message_id"]
            break

    def give_photo_question(self, chat_id, link, text, variants):
        keyboard = []
        for v in variants:
            keyboard.append([{"text": v, "callback_data": v}])
        params = {"chat_id": chat_id, "photo": link, "caption": text, "reply_markup": json.dumps({"inline_keyboard": keyboard, "one_time_keyboard": True})}
        while True:
            res = requests.post(self.api_url + "sendPhoto", params).json()
            if "result" not in res:
                continue
            self.last_markup[chat_id] = res["result"]["message_id"]
            break

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
                if "message" in update:
                    update["message"]["chat"]["id"] = str(update["message"]["chat"]["id"])
                    chat_id = update["message"]["chat"]["id"]
                    if chat_id in self.last_markup:
                        message_id = self.last_markup[chat_id]
                        params = {"chat_id": chat_id, "message_id": message_id}
                        requests.post(self.api_url + "deleteMessage", params)
                    self.process_update_name(update)
                    self.process_update(update)
                else:
                    update1 = update["callback_query"]
                    update1["message"]["text"] = update1["data"]
                    update1["message"]["chat"]["id"] = str(update1["message"]["chat"]["id"])
                    chat_id = update1["message"]["chat"]["id"]
                    if chat_id in self.last_markup:
                        message_id = self.last_markup[chat_id]
                        params = {"chat_id": chat_id, "message_id": message_id}
                        requests.post(self.api_url + "deleteMessage", params)
                    self.process_update_name(update1)
                    self.process_update(update1)
                self.offset = max(self.offset, update['update_id'] + 1)
            time.sleep(1)
