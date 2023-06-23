import json
import tiktoken
from tools import *
from dataclasses import dataclass
from core.meeting import Utterance
from typing import List

def get_tokenizer_func(model_name):
    if model_name not in [ENGINE_TURBO, ENGINE_DAVINCI_003]:
        raise ValueError('Invalid model name: {model_name} when calling get_tokenizer_func.')
    tokenizer = tiktoken.encoding_for_model(model_name)
    return tokenizer.encode


def get_token_count(func, text):
    tokens = func(text)
    return len(tokens)


@dataclass
class BookSpliter:
    model: str

    def split(self, txt_file):
        tokenize_fuc = get_tokenizer_func(self.model)
        encoding = detect_encode_type(txt_file)
        print(f"encoding: {encoding}")

        if 'gb' in encoding.lower():
            encoding = 'gbk'

        with open(txt_file, 'r', encoding=encoding) as f:
            book = f.read() # 读取书籍文本内容
        
        lang = detect_language(book)
        if lang == LANG_ZH:
            seperator = '。'
        else:
            seperator = '. '
        
        
        max_tokens = 3000 # 每部分最多 3000 个 token
        split_book = []
        current_tokens = 0
        current_block = ""

        for sentence in book.split(seperator): # 根据句子切分书籍文本
            _count = get_token_count(tokenize_fuc, sentence) # 计算句子中的 token 数量

            if current_tokens + _count > max_tokens:
                split_book.append(current_block)
                current_block = sentence + seperator
                current_tokens = _count
            else:
                current_tokens += _count
                current_block += sentence + seperator
        
        if current_block: # 加入最后一个块
            split_book.append(current_block)
        
        dst_dir = './logs/book_split/'
        dst_json_file = os.path.join(dst_dir, os.path.basename(txt_file) + f".{self.model}.json")
        makedirs(dst_json_file)
        save_json_file(dst_json_file, split_book)

        line_seperate = '#' * 30
        line_seperate = f"\n\n{line_seperate}\n\n"
        final_str = line_seperate.join(split_book)

        dst_txt_file = os.path.join(dst_dir, os.path.basename(txt_file) + f".{self.model}.txt")
        makedirs(dst_txt_file)
        save_file(dst_txt_file, [final_str])

        return split_book



@dataclass
class MeetingSpliter:
    model: str

    def split(self, dialogues: List[Utterance], meeting_id):
        tokenize_fuc = get_tokenizer_func(self.model)
        max_tokens = 2800 # 每部分最多 2800 个 token
        meetings = [u.to_text() for u in dialogues]
        meetings_str = '\n\n'.join(meetings)

        seperator = '。'
        
        split_parts = []
        current_tokens = 0
        current_block = ""

        for sentence in meetings_str.split(seperator): # 根据句子切分书籍文本
            _count = get_token_count(tokenize_fuc, sentence) # 计算句子中的 token 数量

            if current_tokens + _count > max_tokens:
                split_parts.append(current_block)
                current_block = sentence + seperator
                current_tokens = _count
            else:
                current_tokens += _count
                current_block += sentence + seperator
        
        if current_block: # 加入最后一个块
            split_parts.append(current_block)
        
        dst_dir = './logs/meeting_split/'
        dst_json_file = os.path.join(dst_dir, meeting_id + f".{self.model}.json")
        makedirs(dst_json_file)
        save_json_file(dst_json_file, split_parts)

        line_seperate = '#' * 30
        line_seperate = f"\n\n{line_seperate}\n\n"
        final_str = line_seperate.join(split_parts)

        dst_txt_file = os.path.join(dst_dir, meeting_id + f".{self.model}.txt")
        makedirs(dst_txt_file)
        save_file(dst_txt_file, [final_str])

        return split_parts