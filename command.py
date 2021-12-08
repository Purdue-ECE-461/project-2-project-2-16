import os
from dotenv import load_dotenv

from analysis import get_score
from setup import setup_dependency, count_lines
from test import test_all
from dotenv import load_dotenv


load_dotenv()
LOG_LEVEL = os.getenv("LOG_LEVEL")
LOG_FILE = os.getenv("LOG_FILE")

def get_command(input_command):
    command_dict = {'install': "INSTALL", 'test': 'TEST'}

    # Any string besides "install" and "test" may be a url set
    command_dict.setdefault(input_command, "URL_SET")

    return command_dict.get(input_command)



def figure_out_command(user_input):
    user_command = get_command(user_input)

    if user_command == "INSTALL":
        try:
            print("starting install")
            setup_dependency()
        except RuntimeError:
            print("Dependency does not install correctly")

        return 0

    elif user_command == "URL_SET":
        try:
            print("starting scoring with " + user_input)
            get_score(user_input, {"test": 1})
            
        except RuntimeError:
            print("Score evaluation does not work correctly")

        return 0

    elif user_command == "TEST":
        print("starting tests")
        test_all()
        return 0


def find_log_mode():
    log_level_dic = {'0': 'SILENT', '1': 'NORMAL', '2': 'DEBUG'}
    return log_level_dic.get(LOG_LEVEL)


def write_log_file():
    current_mode = find_log_mode()

    output_file_address = str(LOG_FILE) + ".log"
    #output_file = open(output_file_address, 'a')
	
    API_num = count_lines("requirements.txt")

    if current_mode == 'SILENT':
        pass

    elif current_mode == 'NORMAL':
        print("log mode: Normal")
        #output_file.write(str(API_num) + "API analyzed\n")

    elif current_mode == 'DEBUG':
        print("log mode: debug")
        #output_file.write(str(API_num) + "cases tested\n")
