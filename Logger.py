import json
import os


class Logger:
    MAIN_LOG_FILENAME = "logs/main_log.json"
    TEMP_LOG_FILENAME = "logs/temp_log.json"

    def __init__(self):
        self.main_log_data = None
        self.temp_log_seq = None
        self.last_temp_log_id = -1
        self.commit_operation_handlers = {
            'next': self.commit_operation_next,
            'answer': self.commit_operation_answer,
            'add_name': self.commit_operation_add_name,
        }

    def init_main_log_structure(self):
        self.main_log_data = {
            'questions_assignment': dict(),
            'stats': dict(),
            'name': dict(),
            'last_committed_temp_log_id': -1,
        }

    def read_main_log(self):
        tmp_file = self.MAIN_LOG_FILENAME + '.tmp'
        if os.path.exists(tmp_file):
            try:
                os.replace(tmp_file, self.MAIN_LOG_FILENAME)
            except:
                print("ERROR WRITING LOGS: CAN\'T REPLACE MAIN LOG TMP FILE")
                raise RuntimeError

        try:
            with open(self.MAIN_LOG_FILENAME, 'r') as f:
                data = f.read()
                f.close()
                self.main_log_data = json.loads(data)
        except FileNotFoundError:
            print("MAIN LOG DOESN\'t EXIST")
            open(self.MAIN_LOG_FILENAME, 'w').close()
            self.init_main_log_structure()
        except OSError:
            print('ERROR READING LOGS: MAIN LOG IS NOT AVAILABLE')
            raise RuntimeError
        except json.JSONDecodeError:
            print('ERROR READING LOGS: MAIN LOG IS NOT JSON')
            f.close()
            self.init_main_log_structure()

    def read_temp_log(self):
        try:
            with open(self.TEMP_LOG_FILENAME, 'r') as f:
                self.temp_log_seq = []
                for line in f:
                    try:
                        self.temp_log_seq.append(json.loads(line))
                    except json.JSONDecodeError:
                        print('ERROR READING LOGS: TEMP LOG IS NOT JSON')
                        continue
                f.close()
        except FileNotFoundError:
            print("TEMP LOG DOESN\'t EXIST")
            open(self.TEMP_LOG_FILENAME, 'w').close()
        except OSError:
            print('ERROR READING LOGS: TEMP LOG IS NOT AVAILABLE')
            raise RuntimeError

    def recover_last_temp_log_id(self):
        last_temp = -1
        if self.temp_log_seq:
            last_temp = self.temp_log_seq[-1]['log_id']
        self.last_temp_log_id = max(self.main_log_data['last_committed_temp_log_id'], last_temp)

    def commit_operation_next(self, operation):
        self.main_log_data['questions_assignment'][operation['chat_id']] = operation['question_id']

    def commit_operation_answer(self, operation):
        self.main_log_data['questions_assignment'].pop(operation['chat_id'], None)
        if operation['status'] == 'not_active':
            return
        if operation['chat_id'] not in self.main_log_data['stats']:
            self.main_log_data['stats'][operation['chat_id']] = [0, 0]
        self.main_log_data['stats'][operation['chat_id']][1] += 1
        if operation['status'] == 'ok':
            self.main_log_data['stats'][operation['chat_id']][0] += 1

    def commit_operation_add_name(self, operation):
        self.main_log_data['name'][operation['chat_id']] = operation['name']

    def commit_operation(self, operation):
        if operation['log_id'] <= self.main_log_data['last_committed_temp_log_id']:
            return
        if operation['type'] not in self.commit_operation_handlers:
            print('ERROR COMMITTING LOG: UNKNOWN OPERATION {}'.format(operation['type']))
            return
        self.commit_operation_handlers[operation['type']](operation)
        self.main_log_data['last_committed_temp_log_id'] = operation['log_id']

    def write_main_log(self):
        tmp_file = self.MAIN_LOG_FILENAME + '.tmp'
        try:
            with open(tmp_file, 'w') as f:
                f.write(json.dumps(self.main_log_data))
                f.close()
        except OSError:
            print("ERROR WRITING LOGS: MAIN LOG TMP FILE IS NOT AVAILABLE")
            raise RuntimeError
        try:
            os.replace(tmp_file, self.MAIN_LOG_FILENAME)
        except:
            print("ERROR WRITING LOGS: CAN\'T REPLACE MAIN LOG TMP FILE")
            raise RuntimeError

    def clear_tmp_log(self):
        try:
            open(self.TEMP_LOG_FILENAME, 'w').close()
        except OSError:
            print('ERROR WRITING LOGS: CAN\'T DELETE TEMP LOG')

    def add_to_log(self, operation_type: str, **kwargs):
        temp_log_object = {
            'log_id': self.last_temp_log_id + 1,
            'type': operation_type,
            **kwargs
        }
        self.last_temp_log_id += 1
        json_str = json.dumps(temp_log_object)
        try:
            with open(self.TEMP_LOG_FILENAME, 'a') as f:
                f.write(json_str + '\n')
                f.close()
        except OSError:
            print("ERROR WRITING LOGS: CAN\'T WRITE TO TEMP LOG")
            raise RuntimeError

    def recover(self):
        self.read_main_log()
        self.read_temp_log()
        self.recover_last_temp_log_id()
        if self.temp_log_seq:
            for operation in self.temp_log_seq:
                self.commit_operation(operation)
        self.write_main_log()
        self.clear_tmp_log()
