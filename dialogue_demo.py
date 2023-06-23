import os
import sys
import argparse
from os.path import join
from tools import *
import logging
from core.api import set_api_logger
from core.chat import ChatBot, Turn, set_chat_logger
import gradio as gr
from prompts.dialogue import *

args: argparse.Namespace = None
bot: ChatBot = None


def summarize_embed_one_turn(bot: ChatBot, dialogue_text, dialogue_text_with_index):
    lang2template = {
        LANG_EN: en_turn_summarization_prompt,
        LANG_ZH: zh_turn_summarization_prompt
    }

    tmp = choose_language_template(lang2template, dialogue_text)
    input_text = tmp.format(input=dialogue_text)
    logger.info(f'turn summarization input_text: \n\n{input_text}')
    # 如果原文很短，保留原文即可
    summarization = dialogue_text_with_index
    if get_token_count_davinci(input_text) > 300:
        logger.info(f'current turn text token count > 300, summarize !\n\n')
        summarization = bot.ask(input_text)
        logger.info(f'Summarization is:\n\n{summarization}\n\n')
    else:
        logger.info(f'Raw content is short, keep raw content as summarization:\n\n{summarization}\n\n')
    embedding = bot.vectorize(dialogue_text_with_index)
    return summarization, embedding


def get_concat_input(user_str, pre_sre, hist_str=None):
    lang2template = {
        LANG_EN: en_no_history_agent_prompt,
        LANG_ZH: zh_no_history_agent_prompt
    }

    templates_no_hist = choose_language_template(lang2template, user_str)

    lang2template = {
        LANG_EN: en_history_agent_prompt,
        LANG_ZH: zh_history_agent_prompt
    }

    templates_hist = choose_language_template(lang2template, user_str)

    if hist_str:
        input_text = templates_hist.format(history_turn_text=hist_str, pre_turn_text=pre_sre, input=user_str)
    else:
        input_text = templates_no_hist.format(pre_turn_text=pre_sre, input=user_str)
    return input_text


def check_key_file(key_file):
    if not os.path.exists(key_file):
        print(f'[{key_file}] not found! Please put your apikey in the txt file.')
        sys.exit(-1)


def get_first_prompt(user_text, model_name):
    if model_name in [ENGINE_TURBO]:
        return user_text
    else:
        lang2template = {
            LANG_EN: en_start_prompt,
            LANG_ZH: zh_start_prompt
        }

        tmp = choose_language_template(lang2template, user_text)
        concat_input = tmp.format(input=user_text)
        return concat_input


def my_chatbot(user_input, history):
    history = history or []

    user_input = user_input.strip()

    my_history = list(sum(history, ()))

    COMMAND_RETURN = '命令已成功执行！'

    if user_input in ['清空', 'reset']:
        # history.append((user_input, COMMAND_RETURN))
        history = []
        bot.clear_history()
        logger.info(f'[User Command]: {user_input} {COMMAND_RETURN}')
        return history, history
    elif user_input in ['导出', 'export']:
        # history.append((user_input, COMMAND_RETURN))
        bot.export_history()
        logger.info(f'[User Command]: {user_input} {COMMAND_RETURN}')
        return history, history
    elif user_input in ['回退', '回滚', 'roll back']:
        history.pop()
        bot.roll_back()
        logger.info(f'[User Command]: {user_input} {COMMAND_RETURN}')
        return history, history


    len_hist = len(bot.history)
    cur_turn_index = len_hist + 1
    if len_hist == 0:
        concat_input = get_first_prompt(user_input, args.model_name)
    else:
        retrieve = None
        if cur_turn_index > 2:
            retrieve = bot.get_related_turn(user_input, args.similar_top_k)
        
        concat_input = get_concat_input(user_input, bot.get_turn_for_previous(), hist_str=retrieve)
    
    logger.info(f'\n--------------\n[第{cur_turn_index}轮] concat_input:\n\n{concat_input}\n--------------\n')

    try:
        rsp: str = bot.ask(concat_input)
    except Exception as e:
        logger.error(f'ERROR: \n\n{e}')
        rsp = 'System error, please check log file for details.'
        history.append((user_input, rsp))
        return history, history

    system_text = rsp.strip()

    logger.info(f"system response:\n\n{system_text}")

    cur_text_without_index = '用户：{}\n\n助手：{}'.format(user_input, system_text)
    cur_text_with_index = '[第{}轮]\n\n用户：{}\n\n助手：{}'.format(cur_turn_index, user_input, system_text)

    if detect_language(user_input) == LANG_EN:
        cur_text_without_index = 'User: {}\n\nAssistant: {}'.format(user_input, system_text)
        cur_text_with_index = '[Turn {}]\n\nUser: {}\n\nAssistant: {}'.format(cur_turn_index, user_input, system_text)


    try:
        summ, embedding = summarize_embed_one_turn(bot, cur_text_without_index, cur_text_with_index)
    except Exception as e:
        logger.error(f'summarize_embed_one_turn ERROR: \n\n{e}')
        rsp = 'Summarization error, please check log file for details.'
        history.append((user_input, rsp))
        return history, history

    cur_turn = Turn(user_input=user_input, system_response=system_text, user_sys_text=cur_text_with_index, summ=summ, embedding=embedding)
    bot.add_turn_history(cur_turn)
    
    my_history.append(user_input)
    output = replace_newline(system_text)
    history.append((user_input, output))
    return history, history


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    model_choices = [ENGINE_DAVINCI_003, ENGINE_TURBO]
    parser.add_argument("--apikey_file", type=str, default="./config/apikey.txt")
    parser.add_argument("--model_name", type=str, default=ENGINE_DAVINCI_003, choices=model_choices)
    parser.add_argument("--logfile", type=str, default="./logs/log.txt")
    parser.add_argument("--similar_top_k", type=int, default=4)
    args = parser.parse_args()

    check_key_file(args.apikey_file)

    log_path = args.logfile
    makedirs(log_path)
    # 配置日志记录

    logger = logging.getLogger('dialogue_logger')
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

    stamp = datetime2str()
    bot = ChatBot(model_name=args.model_name)
    
    with gr.Blocks() as demo:
        gr.Markdown(f"<h1><center>Long Dialogue Chatbot ({args.model_name})</center></h1>")
        chatbot = gr.Chatbot()
        state = gr.State()
        txt = gr.Textbox(show_label=False, placeholder="Ask me a question and press enter.").style(container=False)
        txt.submit(my_chatbot, inputs=[txt, state], outputs=[chatbot, state])
        
    demo.launch(share = False)