import os
import re
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

translation_map = {}


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


def check_string_format(input_str):
    input_str = input_str.strip()
    if 'filename' not in input_str or 'dial_id' not in input_str:
        return False
    filename = dial_id = False
    for item in input_str.split('; '):
        if 'filename' in item:
            if item.split(': ')[1]:
                filename = True
        elif 'dial_id' in item:
            if item.split(': ')[1]:
                dial_id = True
    return filename and dial_id


def extract_values(input_str):
    if 'filename' not in input_str or 'dial_id' not in input_str:
        return False
    filename, dial_id = None, None
    for item in input_str.split('; '):
        if 'filename' in item:
            filename = item.split(': ')[1]
        elif 'dial_id' in item:
            dial_id = item.split(': ')[1]
    return filename, dial_id


def replace_code(s: str) -> str:
    start_index = s.find("```")
    end_index = s.rfind("```")
    if start_index != -1 and end_index != -1:
        end_index = min(end_index+3, len(s)-1)
        s = s[:start_index] + "Ommit Code Here ..." + s[end_index:]
    return s


def load_history_dialogue(filename, dial_id):
    data = load_json_file(filename)
    for item in data:
        if dial_id == item['id']:
            return item['dialogue']
    raise ValueError('Invalid dial_id: {dial_id}')


def initialize_bot_and_dial(dialogues, dial_id):
    history = []
    turn_idx = 0
    history.append(('请输入待标注的对话ID', dial_id))
    total = len(dialogues) // 2
    for i in range(0, len(dialogues), 2):
        turn_idx += 1
        if i+1 < len(dialogues):
            user_text = dialogues[i]
            user_text_display = user_text
            if translation_map and translation_map.get(user_text, None):
                zh_text = translation_map.get(user_text)
                zh_text = replace_code(zh_text)
                user_text_display += f"\n\n{zh_text}"
                user_text_display = user_text_display.replace('__', 'prefix_')
            
            # user_text = dialogues[i].replace('\\n', '\n')


            assistant_text = dialogues[i+1]
            assistant_text_display = assistant_text
            if translation_map and translation_map.get(assistant_text, None):
                zh_text = translation_map.get(assistant_text)
                zh_text = replace_code(zh_text)
                assistant_text_display += f"\n\n{zh_text}"
                assistant_text_display = assistant_text_display.replace('__', 'prefix_')

            # assistant_text = dialogues[i+1].replace('\\n', '\n')

            cur = (replace_newline(user_text_display), replace_newline(assistant_text_display))
            # cur = (user_text_display, assistant_text_display)
            history.append(cur)

            cur_text_without_index = '用户：{}\n\n助手：{}'.format(user_text, assistant_text)
            cur_text_with_index = '[第{}轮]\n\n用户：{}\n\n助手：{}'.format(turn_idx, user_text, assistant_text)

            if detect_language(user_text+assistant_text) == LANG_EN:
                cur_text_without_index = 'User: {}\n\nAssistant: {}'.format(user_text, assistant_text)
                cur_text_with_index = '[Turn {}]\n\nUser: {}\n\nAssistant: {}'.format(turn_idx, user_text, assistant_text)

            print(f"loading progress : {turn_idx} / {total}, {cur_text_with_index[:200]} ...\n")

            summary, embedding = summarize_embed_one_turn(bot, cur_text_without_index, cur_text_with_index)

            cur_turn = Turn(user_input=user_text, system_response=assistant_text, user_sys_text=cur_text_with_index, summ=summary, embedding=embedding)
            
            bot.add_turn_history(turn = cur_turn)
    

    return history


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
    elif check_string_format(user_input):
        filename, dial_id = extract_values(user_input)
        dialogues = load_history_dialogue(filename, dial_id)
        history = initialize_bot_and_dial(dialogues, dial_id)
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

    logger.info(f'\n--------------\n[第{cur_turn_index}轮] system_text:\n\n{system_text}\n--------------\n')
    
    my_history.append(user_input)
    output = system_text
    output_display = replace_newline(output)
    history.append((user_input, output_display))
    return history, history


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    model_choices = [ENGINE_DAVINCI_003, ENGINE_TURBO]
    parser.add_argument("--apikey_file", type=str, default="./config/apikey.txt")
    parser.add_argument("--model_name", type=str, default=ENGINE_DAVINCI_003, choices=model_choices)
    parser.add_argument("--logfile", type=str, default="./logs/load_dialogue_log.txt")
    parser.add_argument("--translation_file", type=str, default=None)
    parser.add_argument("--similar_top_k", type=int, default=6)
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
    # print(stamp)

    if args.translation_file:
        translation_map = load_json_file(args.translation_file)
    
    bot = ChatBot(model_name=args.model_name)

    with gr.Blocks() as demo:
        gr.Markdown(f"<h1><center>Long Dialogue Chatbot ({args.model_name}) for test</center></h1>")
        chatbot = gr.Chatbot()
        state = gr.State()
        txt = gr.Textbox(show_label=False, placeholder="Ask me a question and press enter.").style(container=False)
        txt.submit(my_chatbot, inputs=[txt, state], outputs=[chatbot, state])
        
    demo.launch(share = False)