import os
import sys
import argparse
from tools import *
import logging
from core.api import set_api_logger, KEY_MANAGER
from core.meeting import Utterance, SummaryTurn, SummaryBot, set_chat_logger

from utils.spliter import MeetingSpliter
from prompts.meeting import *
from typing import List

args: argparse.Namespace = None
bot: SummaryBot = None
# meeting theme
theme = ''


def get_concat_input(theme, user_str, pre_sre):
    current_text = user_str
    previous_content = pre_sre
    input_text = zh_memory_prompt.format(theme=theme, previous_content=previous_content, current_text=current_text)
    return input_text


def check_file(key_file):
    if not os.path.exists(key_file):
        print(f'[{key_file}] not found!')
        sys.exit(-1)


def get_first_prompt(theme, user_text):
    concat_input = zh_start_prompt.format(theme=theme, input=user_text)
    return concat_input


def get_paragragh_prompt(theme, user_text):
    concat_input = zh_start_prompt.format(theme=theme, input=user_text)
    return concat_input


def get_theme(dialogues: List[Utterance]):
    introduction = dialogues[0].content
    total = len(dialogues)
    if len(introduction) < 100:
        i = 1
        while len(introduction) < 1800 and i < total:
            introduction += f" {dialogues[i].content}"
            i += 1
    
    introduction = introduction[:1200]
    theme_prompt = zh_theme_prompt.format(input=introduction)
    theme = bot.ask(theme_prompt).strip().rstrip('。').rstrip('.')
    return theme


def summarize_meeting(meeting_id, dialogues, model_name, scm=True):
    global args
    global bot
    global theme

    bot.clear_history()

    spliter = MeetingSpliter(model_name)

    dialogues = [Utterance.parse_from_json(o) for o in dialogues]

    # get_meeting_theme
    theme = get_theme(dialogues)

    logger.info(f"meeting_id: {meeting_id}   theme: {theme}")


    parts = spliter.split(dialogues, meeting_id)
    total = len(parts)
    for i, text in enumerate(parts):
        concat_input = ''
        if scm:
            if i == 0:
                concat_input = get_first_prompt(theme, text)
            else:
                pre_info = bot.get_turn_for_previous()
                concat_input = get_concat_input(theme, text, pre_info)
        else:
            concat_input = get_paragragh_prompt(theme, text)



        logger.info(f'\n--------------\n[第{i+1}轮] model_name:{model_name};  USE SCM: {scm} \n\nconcat_input:\n\n{concat_input}\n--------------\n')

        summary: str = bot.ask(concat_input).strip()
        logger.info(f"model_name:{model_name}; USE SCM: {scm}; Summary:\n\n{summary}\n\n")

        summary_turn = SummaryTurn(paragraph=text, summary=summary)
        
        bot.add_turn_history(summary_turn)

        logger.info(f"model_name:{model_name}; USE SCM: {scm};  Processing: {i+1}/{total}; add_turn_history is done!")
    
    logger.info(f"First Level Summarization Done!")

    final_summary = bot.get_final_summary()
    logger.info(f"final_summary:\n\n{final_summary}")
    
    suffix = ''
    if scm is False:
        suffix = 'no_scm'
    bot.export_history(meeting_id, suffix)
    bot.clear_history()


def get_target_meetings(meeting_data, meeting_ids):
    meetings = {}
    for i, o in enumerate(meeting_data):
        mid = o['meeting_id']
        meetings[mid] = o
    
    target_data = {}
    for mid in meeting_ids:
        if mid in meetings:
            target_data[mid] = meetings[mid]
        else:
            raise ValueError(f'Invalid meeting id : {mid} !!!')
    
    return target_data


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    model_choices = [ENGINE_TURBO, ENGINE_DAVINCI_003]
    parser.add_argument("--apikey_file", type=str, default="./config/apikey.txt")
    parser.add_argument("--model_name", type=str, default=ENGINE_DAVINCI_003, choices=model_choices)
    parser.add_argument("--meeting_file", type=str, default="./data/meeting/vc_summary.json")
    parser.add_argument("--meeting_ids", nargs='+', type=str, required=True)
    parser.add_argument("--logfile", type=str, default="./logs/meeting.summary.log.txt")
    parser.add_argument('--no_scm', action='store_true', help='do not use historical memory, default is False')
    args = parser.parse_args()

    check_file(args.apikey_file)
    check_file(args.meeting_file)

    log_path = args.logfile
    meeting_path = args.meeting_file
    makedirs(log_path)
    # 配置日志记录

    logger = logging.getLogger('summary_logger')
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('【%(asctime)s - %(levelname)s】 - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    set_chat_logger(logger)
    set_api_logger(logger)

    logger.info('\n\n\n')
    logger.info('#################################')
    logger.info('#################################')
    logger.info('#################################')
    logger.info('\n\n\n')
    logger.info(f"args: \n\n{args}\n")

    meeting_ids = args.meeting_ids
    
    # whether use scm for history memory
    USE_SCM = False if args.no_scm else True
    model_name = args.model_name

    meeting_data: List[dict] = load_json_file(meeting_path)

    target_data = get_target_meetings(meeting_data, meeting_ids)

    bot = SummaryBot(model_name=model_name)
    for mid in meeting_ids:
        logger.info(f'\n\n※※※ Begin Summarize Meeting : {mid} ※※※\n\n')
        dialogues = target_data[mid]['dialogues']
        try:
            summarize_meeting(mid, dialogues, model_name, scm=USE_SCM)
        except Exception as e:
            logger.info(f"☆☆☆☆☆ ERROR: model_name {model_name}; Meeting ID {mid}; e: {e} ☆☆☆☆☆")
            continue
    
    KEY_MANAGER.remove_deprecated_keys()