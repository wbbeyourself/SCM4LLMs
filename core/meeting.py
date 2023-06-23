import torch
import torch.nn.functional as F
import numpy as np
from core.api import *
import tiktoken
from tools import *
import json
from dataclasses import dataclass
from typing import List
from prompts.meeting import zh_hierarchical_summarization_prompt

LOCAL_CHAT_LOGGER = None
def set_chat_logger(one):
    global LOCAL_CHAT_LOGGER
    LOCAL_CHAT_LOGGER = one


@dataclass
class Utterance:
    role: str
    content: str

    def to_text(self):
        text = f"[{self.role}]: {self.content}"
        return text
    
    def to_json(self):
        obj = {
            'role': self.role,
            'content': self.content
        }
        return obj
    
    def set_content(self, content):
        obj = Utterance(role=self.role, content=content)
        return obj
    

    @staticmethod
    def parse_from_json(js):
        obj = None
        try:
            obj = Utterance(js['role'], js['content'])
        except Exception as e:
            raise ValueError(f"invalid utterance {js}")
        return obj
    
    @staticmethod
    def parse(text):
        o = json.loads(text)
        obj = Utterance.parse_from_json(o)
        return obj

    @staticmethod
    def parse_batch(text):
        ut_lst = None
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                ut_lst = []
                for role, content in obj.items():
                    t = Utterance(role, content)
                    ut_lst.append(t)
        except Exception as e:
            if LOCAL_CHAT_LOGGER:
                LOCAL_CHAT_LOGGER.error(f"invalid utterance json : {text}")
            else:
                print(f"invalid utterance json : {text}")
        return ut_lst


def get_tokenizer_func(model_name):
    if model_name in [ENGINE_TURBO, ENGINE_DAVINCI_003]:
        tokenizer = tiktoken.encoding_for_model(model_name)
        return tokenizer.encode
    else:
        raise ValueError(f"model name {model_name} is invalid.")


class SummaryTurn(object):

    def __init__(self, paragraph, summary):
        self.paragraph = paragraph
        self.summary = summary
        self.content_tokens_length = 0
        self.summary_tokens_length = 0
    
    def to_json(self):
        js = {
            'paragraph': self.paragraph,
            'summary': self.summary
        }
        return js
    
    def to_json_str(self):
        js = self.to_json()
        js_str = json.dumps(js, ensure_ascii=False) + '\n'
        return js_str
    
    def to_text(self):
        text = f'[paragraph]:\n{self.paragraph}\n\n'
        text += f'[summary]:\n{self.summary}\n'
        text += ('-' * 30 + '\n\n')
        return text


class SummaryBot(object):

    def __init__(self, model_name) -> None:
        assert model_name in MODEL_LIST, f'model name "{model_name}" is not in {MODEL_LIST}'
        self.model_name = model_name
        self.api_func = MODEL_MAP[model_name]
        self.turbo_func = MODEL_MAP[ENGINE_TURBO]
        self.embedding_func = MODEL_EMBEDDING_MAP[model_name]
        self.tokenize_func = get_tokenizer_func(self.model_name)
        self.history: list[SummaryTurn] = []
        self.depth_summary_dict = {}
        self.final_summary = ''

    def clear_history(self):
        self.history = []
        self.final_summary = ''
        self.depth_summary_dict = {}
    
    def roll_back(self):
        self.history.pop()
    
    def export_history(self, meeting_id, suffix=''):
        hist_lst = [one.to_json() for one in self.history]
        depth_summaries = [{k: v} for k, v in self.depth_summary_dict.items()]
        if depth_summaries:
            hist_lst.extend(depth_summaries)
        hist_lst.append({'final summary': self.final_summary})

        hist_txt_lst = [one.to_text() for one in self.history]
        if depth_summaries:
            hist_txt_lst.extend([json.dumps(i, ensure_ascii=False)+'\n\n' for i in depth_summaries])
        hist_txt_lst.append(f"final summary: \n\n{self.final_summary}\n\n")
        
        if suffix:
            suffix = f"-{suffix}"
        json_filename = f'history/summary-{meeting_id}-{self.model_name}{suffix}.json'
        txt_filename = f'history/summary-{meeting_id}-{self.model_name}{suffix}.txt'
        makedirs(json_filename)
        save_json_file(json_filename, hist_lst)
        save_file(txt_filename, hist_txt_lst)
    

    def ask(self, prompt) -> str:
        output = self.api_func(prompt)
        return output


    def vectorize(self, text) -> list:
        output = self.embedding_func(text)
        return output

    def _summarize_paragraphs(self, paragraphs: str, max_tokens):
        paragraphs_text = paragraphs.strip()
        input_text = zh_hierarchical_summarization_prompt.format(paragraph_summaries=paragraphs_text, max_tokens=max_tokens)
        LOCAL_CHAT_LOGGER.info(f"_summarize_paragraphs; max_tokens:{max_tokens}; input_text:\n\n{input_text}\n")
        output = self.ask(input_text)
        LOCAL_CHAT_LOGGER.info(f"_summarize_paragraphs output:\n\n{output}\n")
        return output

    def group_strings(self, content_lst, summary_token_length_lst, group_tokens=2000):
        result = []
        curr_group = []
        curr_len = 0

        for i in range(len(content_lst)):
            if summary_token_length_lst[i] > group_tokens:
                # 如果字符串长度大于2000，单独放一组
                if curr_group:
                    result.append(curr_group)
                result.append([content_lst[i]])
                curr_group = []
                curr_len = 0
            elif curr_len + summary_token_length_lst[i] > group_tokens:
                # 当前分组的长度已经超过2000，需要新建一组
                result.append(curr_group)
                curr_group = [content_lst[i]]
                curr_len = summary_token_length_lst[i]
            else:
                # 将当前字符串加入当前分组
                curr_group.append(content_lst[i])
                curr_len += summary_token_length_lst[i]

        if curr_group:
            # 将最后一个分组加入结果列表中
            result.append(curr_group)

        return ['\n\n'.join(group).strip() for group in result]

    
    def _divide_conquer_summary(self, content_lst, depth=1):
        summary_token_length_lst = [len(self.tokenize_func(txt)) for txt in content_lst]
        LOCAL_CHAT_LOGGER.info(f"depth:{depth}; summary_token_length_lst:\n\n{summary_token_length_lst}")
        total_tokens = sum(summary_token_length_lst)
        LOCAL_CHAT_LOGGER.info(f"depth:{depth}; total_tokens: {total_tokens}")

        group_tokens = 2300
        groups = self.group_strings(content_lst, summary_token_length_lst, group_tokens=group_tokens)

        single_summary_max_tokens = 1000
        if len(groups) == 1:
            single_summary_max_tokens = 1500

        group_summaries = []
        total_groups = len(groups)
        for i, text in enumerate(groups):
            token_count = len(self.tokenize_func(text))
            current_tokens = max(token_count, group_tokens)
            tgt_tokens = min(4000 - current_tokens - 400, single_summary_max_tokens)

            summary = self._summarize_paragraphs(text, max_tokens=tgt_tokens)
            group_summaries.append(summary)
            LOCAL_CHAT_LOGGER.info(f"\n\ndepth:{depth}; processing: {i+1}/{total_groups}...\n\n")


        self.depth_summary_dict[f"depth={depth};count={len(group_summaries)}"] = group_summaries
        LOCAL_CHAT_LOGGER.info(f"depth:{depth}; group_summaries:\n\n{group_summaries}")

        return_summary = ''
        if len(group_summaries) > 1:
            return_summary = self._divide_conquer_summary(group_summaries, depth=depth+1)
        else:
            return_summary = group_summaries[0]
        
        if depth == 1:
            LOCAL_CHAT_LOGGER.info(f"depth:{depth}; return_summary:\n\n{return_summary}")
            self.final_summary = return_summary

        return return_summary

    def get_final_summary(self):
        sub_summary_lst = [item.summary for item in self.history]
        final_summary = self._divide_conquer_summary(sub_summary_lst)
        self.final_summary = final_summary
        return final_summary
    
    def add_turn_history(self, turn: SummaryTurn):
        turn.content_tokens_length = len(self.tokenize_func(turn.paragraph))
        turn.summary_tokens_length = len(self.tokenize_func(turn.summary))
        self.history.append(turn)
    
    def get_turn_for_previous(self):
        turn = self.history[-1]
        if turn.content_tokens_length < 500:
            return turn.paragraph
        else:
            return turn.summary

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

        index_value_lst = [(idx, v) for idx, v in zip(topk_indices, topk_values)]
        # print(index_value_lst)
        sorted_index_value_lst = sorted(index_value_lst, key=lambda x: x[0])
        LOCAL_CHAT_LOGGER.info(f'\n--------------\n')
        LOCAL_CHAT_LOGGER.info(f"\nTop{k}相似历史索引及其相似度: \n\n{sorted_index_value_lst}\n")
        LOCAL_CHAT_LOGGER.info(f'\n--------------\n')


        retrieve_history_text = ''
        for idx, sim_score in sorted_index_value_lst:
            turn: SummaryTurn = self.history[idx]
            # 判断一下长度
            cur = turn.paragraph.strip()
            use_summary = False
            if turn.content_tokens_length > 300:
                use_summary = True
                cur = turn.summary.strip()

            LOCAL_CHAT_LOGGER.info(f'\n@@@@@@@@@@@@@@@@@@')
            LOCAL_CHAT_LOGGER.info(f'检索到的历史轮[使用摘要?{use_summary}]：{cur.strip()}')
            LOCAL_CHAT_LOGGER.info(f'相似度：{sim_score}')
            retrieve_history_text += f'{cur}\n\n'
        
        return retrieve_history_text.strip()
    
    def _similarity(self, v1, v2):
        vec1 = torch.FloatTensor(v1)
        vec2 = torch.FloatTensor(v2)
        cos_sim = F.cosine_similarity(vec1, vec2, dim=0)
        return cos_sim