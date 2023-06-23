import os
import sys
import argparse
from os.path import join
from tools import *
import logging
from core.api import set_api_logger, KEY_MANAGER
from core.book import SummaryBot, SummaryTurn, set_chat_logger
from utils.spliter import BookSpliter
from prompts.book import *

args: argparse.Namespace = None
bot: SummaryBot = None


def get_concat_input(user_str, pre_sre, hist_str=None):
    lang2template = {
        LANG_EN: en_agent_scm_prompt,
        LANG_ZH: zh_agent_scm_prompt
    }

    template: str = choose_language_template(lang2template, user_str)

    current_text = user_str
    previous_content = pre_sre
    if hist_str:
        previous_content = f"{hist_str}\n\n{pre_sre}"
    
    input_text = template.format(previous_content=previous_content, current_text=current_text)

    return input_text


def check_key_file(key_file):
    if not os.path.exists(key_file):
        print(f'[{key_file}] not found! Please put your apikey in the txt file.')
        sys.exit(-1)


def get_first_prompt(user_text):
    lang2template = {
        LANG_EN: en_start_prompt,
        LANG_ZH: zh_start_prompt
    }

    tmp = choose_language_template(lang2template, user_text)
    concat_input = tmp.format(text=user_text)
    return concat_input


def get_paragragh_prompt(user_text):
    lang2template = {
        LANG_EN: en_agent_no_scm_prompt,
        LANG_ZH: zh_agent_no_scm_prompt
    }

    tmp = choose_language_template(lang2template, user_text)
    concat_input = tmp.format(text=user_text)
    return concat_input


def summarize_book(book_file, model_name, scm=True):
    global args
    global bot

    bot.clear_history()

    spliter = BookSpliter(model_name)

    paragraphs = spliter.split(book_file)

    total = len(paragraphs)

    for i, text in enumerate(paragraphs):
        concat_input = ''
        if scm:
            if i == 0:
                concat_input = get_first_prompt(text)
            else:
                pre_info = bot.get_turn_for_previous()
                concat_input = get_concat_input(text, pre_info)
        else:
            concat_input = get_paragragh_prompt(text)
        
        logger.info(f'\n--------------\n[第{i+1}轮] model_name:{model_name};  USE SCM: {scm} \n\nconcat_input:\n\n{concat_input}\n--------------\n')

        summary: str = bot.ask(concat_input).strip()
        logger.info(f"model_name:{model_name}; USE SCM: {scm}; Summary:\n\n{summary}\n\n")
        # embedding = bot.vectorize(summary)
        # just book summarization do not need embedding
        embedding = None
        cur_turn = SummaryTurn(paragraph=text, summary=summary, embedding=embedding)
        bot.add_turn_history(cur_turn)
        logger.info(f"model_name:{model_name}; USE SCM: {scm};  Processing: {i+1}/{total}; add_turn_history is done!")
    
    logger.info(f"First Level Summarization Done!")

    final_summary = bot.get_final_summary()
    logger.info(f"final_summary:\n\n{final_summary}")
    
    suffix = ''
    if scm is False:
        suffix = 'no_scm'
    bot.export_history(book_file, suffix)
    bot.clear_history()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    model_choices = [ENGINE_TURBO, ENGINE_DAVINCI_003]
    parser.add_argument("--apikey_file", type=str, default="./config/apikey.txt")
    parser.add_argument("--model_name", type=str, default=ENGINE_DAVINCI_003, choices=model_choices)
    parser.add_argument("--book_files", nargs='+', type=str, required=True)
    parser.add_argument("--logfile", type=str, default="./logs/book.summary.log.txt")
    parser.add_argument('--no_scm', action='store_true', help='do not use historical memory, default is False')
    args = parser.parse_args()

    check_key_file(args.apikey_file)

    log_path = args.logfile
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

    book_list = args.book_files
    
    # whether use scm for history memory
    USE_SCM = False if args.no_scm else True
    model_name = args.model_name

    
    bot = SummaryBot(model_name=model_name)
    for book_file in book_list:
        book_name = os.path.basename(book_file)
        logger.info(f'\n\n※※※ Begin Summarize Book : {book_name} ※※※\n\n')
        try:
            summarize_book(book_file, model_name, scm=USE_SCM)
        except Exception as e:
            logger.info(f"☆☆☆☆☆ ERROR: model_name {model_name}; book_file {book_file}; e: {e} ☆☆☆☆☆")
            continue
    
    KEY_MANAGER.remove_deprecated_keys()