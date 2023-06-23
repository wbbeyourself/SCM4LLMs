import torch
import torch.nn.functional as F
import numpy as np
from core.api import *
import tiktoken
import json
from tools import *
from prompts.dialogue import judge_answerable_prompt

LOCAL_CHAT_LOGGER = None
def set_chat_logger(one):
    global LOCAL_CHAT_LOGGER
    LOCAL_CHAT_LOGGER = one


def get_tokenizer_func(model_name):
    if model_name in [ENGINE_TURBO, ENGINE_DAVINCI_003]:
        tokenizer = tiktoken.encoding_for_model(model_name)
        return tokenizer.encode
    else:
        raise ValueError(f"model name {model_name} is invalid.")


class Turn(object):

    def __init__(self, user_input, system_response, user_sys_text, summ, embedding):
        self.user_input = user_input
        self.system_response = system_response
        self.user_sys_text = user_sys_text
        self.summ = summ
        self.embedding = embedding
        self.content_tokens_length = 0
        self.summary_tokens_length = 0
    
    def to_json(self):
        js = {
            'user': self.user_input,
            'system': self.system_response
            # 'summary': self.summ
        }
        return js
    
    def to_json_str(self):
        js = self.to_json()
        js_str = json.dumps(js, ensure_ascii=False) + '\n'
        return js_str
    
    def to_plain_text(self):
        text = f'[User]:\n{self.user_input}\n\n'
        text += f'[System]:\n{self.system_response}\n'
        text += ('-' * 30 + '\n\n')
        return text


class ChatBot(object):

    def __init__(self, model_name) -> None:
        assert model_name in MODEL_LIST, f'model name "{model_name}" is not in {MODEL_LIST}'
        self.model_name = model_name
        self.api_func = MODEL_MAP[model_name]
        self.turbo_func = MODEL_MAP[ENGINE_TURBO]
        self.embedding_func = MODEL_EMBEDDING_MAP[model_name]
        self.tokenize_func = get_tokenizer_func(self.model_name)
        self.history: list[Turn] = []

    def clear_history(self):
        self.history = []
    
    def roll_back(self):
        self.history.pop()
    
    def export_history(self):
        hist_lst = [one.to_json() for one in self.history]
        hist_txt_lst = [one.to_plain_text() for one in self.history]
        txt_prefix = keep_only_alnum_chinese(hist_lst[0]["user"][:10])

        json_filename = f'history/{txt_prefix}-{self.model_name}.json'
        txt_filename = f'history/{txt_prefix}-{self.model_name}.txt'
        save_json_file(json_filename, hist_lst)
        save_file(txt_filename, hist_txt_lst)
    
    # def load_history(self, hist_file):
    #     diag_hist = load_jsonl_file(hist_file)
    #     emb_hist = load_jsonl_file(hist_file + '.emb.json')
    #     for dig, e in zip(diag_hist, emb_hist):
    #         js = {}
    #         js['text'] = dig['text']
    #         js['summ'] = dig['summ']
    #         js['embedding'] = e
    #         one = Turn(**js)
    #         self.history.append(one)
    #     self.show_history()
    
    # def show_history(self):
    #     print('\n\n-------------【history】-------------\n\n')
    #     for i, turn in enumerate(self.history):
    #         print(f'{turn.text.strip()}\n\n')
    #         # print(f'对话摘要: \n{turn.summ}\n')

    def ask(self, prompt) -> str:
        output = self.api_func(prompt, verbo=False)
        return output

    def is_history_need(self, prompt) -> str:
        output = self.api_func(prompt)
        LOCAL_CHAT_LOGGER.info(f'\n--------------\nprompt: \n{prompt}\n\n')
        LOCAL_CHAT_LOGGER.info(f'output: {output}\n--------------\n')
        if '(B)否' in output or '(B)' in output:
            return False
        return True
    

    def get_binary_answer(self, prompt, false_choices=[]) -> str:
        output = self.api_func(prompt)
        LOCAL_CHAT_LOGGER.info(f'\n--------------\nprompt: \n{prompt}\n\n')
        LOCAL_CHAT_LOGGER.info(f'output: {output}\n--------------\n')
        if false_choices:
            for ch in false_choices:
                if ch in output:
                    return False
            return True
        else:
            if '(B)否' in output or '(B)' in output:
                return False
            return True

    def vectorize(self, text) -> list:
        output = self.embedding_func(text, verbo=False)
        return output
    
    def add_turn_history(self, turn: Turn):
        turn.content_tokens_length = len(self.tokenize_func(turn.user_sys_text))
        turn.summary_tokens_length = len(self.tokenize_func(turn.summ))
        self.history.append(turn)
    
    def get_turn_for_previous(self):
        turn = self.history[-1]
        if turn.content_tokens_length < 500:
            return turn.user_sys_text
        else:
            return turn.summ
    
    def _is_concat_history_too_long(self, length_lst):
        total_tokens = sum(length_lst)
        pre_turn = self.history[-1]
        pre_turn_length = pre_turn.content_tokens_length
        if pre_turn_length > 500:
            pre_turn_length = pre_turn.summary_tokens_length

        total_tokens += pre_turn_length

        if LOCAL_CHAT_LOGGER:
            LOCAL_CHAT_LOGGER.info(f"total_tokens: {total_tokens}")
        
        if total_tokens > 2500:
            return True
        else:
            return False


    def judge_drop_or_summary(self, user_query, turn_index):
        turn_raw = self.history[turn_index].user_sys_text
        turn_summary = self.history[turn_index].summ

        input_text = judge_answerable_prompt.format(content=turn_raw, query=user_query)
        is_answerable = self.get_binary_answer(input_text)
        if LOCAL_CHAT_LOGGER:
            LOCAL_CHAT_LOGGER.info(f'\n--------------\nuse raw_text is_answerable: {is_answerable}\n--------------\n')
        
        if not is_answerable:
            return 'drop'
        
        input_text = judge_answerable_prompt.format(content=turn_summary, query=user_query)
        is_answerable = self.get_binary_answer(input_text)
        if LOCAL_CHAT_LOGGER:
            LOCAL_CHAT_LOGGER.info(f'\n--------------\nuse turn summary is_answerable: {is_answerable}\n--------------\n')

        if is_answerable:
            return 'summary'
        else:
            return 'raw'
    
    
    def get_related_turn(self, query, k=3):
        q_embedding = self.vectorize(query)
        # 只检索 [0, 上一轮)   上一轮的文本直接拼接进入对话，无需检索
        sim_lst = [
            self._similarity(q_embedding, v.embedding)
            for v in self.history[:-1]
        ]

        # convert to numpy array
        arr = np.array(sim_lst)

        # get indices and values of the top k maximum values
        topk_indices = arr.argsort()[-k:]
        topk_values = arr[topk_indices]

        topk_indices = topk_indices.tolist()
        topk_values = topk_values.tolist()

        turns = [self.history[t] for t in topk_indices]
        length_lst = [t.content_tokens_length for t in turns]
        turn_flag_map = {t: 'raw' for t in topk_indices}
        shorten_history = self._is_concat_history_too_long(length_lst)

        first_round = True
        
        while shorten_history:
            # 开始用模型来判断是否精简, 如果是，修改 use_summary_map[key] = True
            for i, turn_idx in enumerate(topk_indices):
                # todo: judge
                cur_turn = self.history[turn_idx]
                if first_round:
                    if i < (len(topk_indices) - 1):
                        choice = self.judge_drop_or_summary(query, turn_idx)
                    else:
                        choice = 'raw'
                else:
                    choice = turn_flag_map[turn_idx]
                    if choice == 'raw':
                        choice = 'summary'
                
                turn_flag_map[turn_idx] = choice
                if choice == 'drop':
                    length_lst[i] = 0
                elif choice == 'summary':
                    length_lst[i] = cur_turn.summary_tokens_length
                else:
                    pass

                if not first_round:
                    shorten_history = self._is_concat_history_too_long(length_lst)
                    if not shorten_history:
                        break

            shorten_history = self._is_concat_history_too_long(length_lst)
            if first_round:
                first_round = False

        index_value_lst = [(idx, v) for idx, v in zip(topk_indices, topk_values)]
        # print(index_value_lst)
        sorted_index_value_lst = sorted(index_value_lst, key=lambda x: x[0])
        # LOCAL_CHAT_LOGGER.info(f'\n--------------\n')
        # LOCAL_CHAT_LOGGER.info(f"\nTop{k}相似历史索引及其相似度: \n\n{sorted_index_value_lst}\n")
        # LOCAL_CHAT_LOGGER.info(f'\n--------------\n')

        retrieve_history_text = ''
        for idx, sim_score in sorted_index_value_lst:
            turn: Turn = self.history[idx]

            flag = turn_flag_map[idx]

            # LOCAL_CHAT_LOGGER.info(f'\n@@@@@@@@@@@@@@@@@@')
            # LOCAL_CHAT_LOGGER.info(f'检索到的历史轮: {turn.user_sys_text[:100]}\n')
            # LOCAL_CHAT_LOGGER.info(f'模型对于这段文本的选择: {flag}')

            text = ''
            if flag == 'drop':
                continue
            elif flag == 'summary':
                text = turn.summ
            else:
                text = turn.user_sys_text

            # LOCAL_CHAT_LOGGER.info(f'turn final text: {text}\n\n')
            # LOCAL_CHAT_LOGGER.info(f'相似度：{sim_score}')
            retrieve_history_text += f'{text}\n\n'
        
        return retrieve_history_text
    
    def _similarity(self, v1, v2):
        vec1 = torch.FloatTensor(v1)
        vec2 = torch.FloatTensor(v2)
        cos_sim = F.cosine_similarity(vec1, vec2, dim=0)
        return cos_sim