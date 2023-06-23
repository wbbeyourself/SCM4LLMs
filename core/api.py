import os
import json
import logging
import openai
import time
import random
import functools
import tiktoken
import multiprocessing
from tools import *
from core.cfg import HTTP_PROXY

embedding_cache_path = './logs/call_embedding_history.json'
text_cache_path = './logs/call_func_history.json'

def load_cache(path):
    if not os.path.exists(path):
        makedirs(path)
        save_file(path, ["{}\n"])
        return {}
    cache_map = {}
    data = load_jsonl_file(path)
    for item in data:
        if len(item) == 0:
            continue
        key = f"{item['function']}_{item['input']}"
        value = item['output']
        cache_map[key] = value
    return cache_map

# load openai cache
embedding_cache = load_cache(embedding_cache_path)
text_cache = load_cache(text_cache_path)

formatter = logging.Formatter('%(message)s')

# 配置logger
openai_logger = logging.getLogger('call_func_history')
openai_logger.setLevel(logging.INFO)
handler = logging.FileHandler(text_cache_path, encoding='utf-8')
handler.setFormatter(formatter)
openai_logger.addHandler(handler)

openai_embedding_logger = logging.getLogger('call_embedding_history')
openai_embedding_logger.setLevel(logging.INFO)
embedding_handler = logging.FileHandler(embedding_cache_path, encoding='utf-8')
embedding_handler.setFormatter(formatter)
openai_embedding_logger.addHandler(embedding_handler)

APIKEY_FILE = 'config/apikey.txt'

if HTTP_PROXY:
    os.environ["HTTP_PROXY"] = HTTP_PROXY
    os.environ["HTTPS_PROXY"] = HTTP_PROXY
    print(f"\nUse Proxy {HTTP_PROXY}\n\n")

LOCAL_API_LOGGER = None
def set_api_logger(one):
    global LOCAL_API_LOGGER
    LOCAL_API_LOGGER = one


def log_info(message):
    global LOCAL_API_LOGGER
    if LOCAL_API_LOGGER:
        LOCAL_API_LOGGER.info(message)
    else:
        print(message)


# 定义一个函数，用于记录调用历史
def log_openai_result(func):
    global embedding_cache
    global text_cache

    def wrapper(*args, **kwargs):
        prompt = args[0] if args else None
        
        # print(f"prompt: {prompt}")
        # print(f"response: {response}")
        func_name = str(func.__name__)
        # print(f"function: {func_name}")

        key = f"{func_name}_{prompt}"
        if key in embedding_cache:
            print(f'hit embedding cache: {prompt[:20]} .. ')
            return embedding_cache[key]
        elif key in text_cache:
            print(f'hit text cache: {prompt[:20]} .. ')
            return text_cache[key]

        response = func(*args, **kwargs)

        call_info = {'function': func.__name__, 'input': prompt, 'output': response}
        json_str = json.dumps(call_info, ensure_ascii=False)
        if func_name == 'call_embedding_openai':
            openai_embedding_logger.info(json_str)
            embedding_cache[key] = response
        else:
            openai_logger.info(json_str)
            text_cache[key] = response
        
        return response
    return wrapper


class KeyManager(object):

    index_save_file = '.key.index'

    def __init__(self, filename) -> None:
        self.apikey_file = filename
        self.keys = get_lines(filename)
        assert len(self.keys) > 0, f"no keys found in {filename}!"
        self.key_index = 0
        self.deprecated_keys = {}
        if os.path.exists(self.index_save_file):
            index = int(get_lines(self.index_save_file)[-1])
            index += 1
            index %= len(self.keys)
            self.key_index = index

    def get_api_key(self, verbo=False):
        scan_count = 0
        total_key_len = len(self.keys)
        while True:
            if scan_count > total_key_len:
                raise ValueError(f"ERROR: No available keys !!!")
            self.key_index += 1
            self.key_index %= len(self.keys)
            cur_key = self.keys[self.key_index]
            if cur_key in self.deprecated_keys:
                scan_count += 1
                continue
            else:
                append_file(self.index_save_file, [str(self.key_index)+'\n'])
                if verbo:
                    print(f'\n-----------------\nkey: {cur_key}\nindex:{self.key_index}\n-----------------\n')
                return cur_key
    
    def set_deprecated_key(self, key):
        self.deprecated_keys[key] = 1
    
    def remove_deprecated_keys(self):
        keeps = []
        for key in self.keys:
            if key not in self.deprecated_keys:
                keeps.append(f"{key}\n")
        save_file(self.apikey_file, keeps)

QUOTA_ERROR = 'You exceeded your current quota'

KEY_MANAGER = KeyManager(APIKEY_FILE)

def handle_call_openai_api(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if "apikey" not in kwargs or kwargs["apikey"] is None:
            kwargs["apikey"] = KEY_MANAGER.get_api_key(verbo=False)
        openai.api_key = kwargs["apikey"]
        error_count = 0
        max_try = 6
        while True:
            try:
                ans = func(*args, **kwargs)
                return ans
            except Exception as e:
                error_msg = str(e)
                if QUOTA_ERROR in error_msg:
                    KEY_MANAGER.set_deprecated_key(openai.api_key)
                else:
                    error_count += 1
                LOCAL_API_LOGGER.info(f"Exception during {func.__name__} using api_key {openai.api_key}: {e}, sleep 2 secs. error_count: {error_count}")
                time.sleep(2)
                apikey = KEY_MANAGER.get_api_key(verbo=False)
                openai.api_key = apikey
            if error_count >= max_try:
                raise ValueError(f'Have try {max_try} times, still error, give up!!!')
    return wrapper


@log_openai_result
@handle_call_openai_api
def call_embedding_openai(prompt, apikey=None, verbo=True):
    response = openai.Embedding.create(
        model="text-embedding-ada-002",
        input=prompt
    )
    embedding = response['data'][0]['embedding']
    return embedding


@log_openai_result
@handle_call_openai_api
def call_text_davinci_003(prompt, apikey=None, verbo=True):
    max_tokens=1024
    tokenizer = tiktoken.encoding_for_model(ENGINE_DAVINCI_003)
    prompt_tokens = tokenizer.encode(prompt)
    assert len(prompt_tokens) < 3999, f"ERROR: prompt length > 4000, {prompt[:100]} ..."
    max_tokens = min(4000 - len(prompt_tokens), max_tokens)

    api_model_index = ENGINE_DAVINCI_003
    response = openai.Completion.create(
            engine=ENGINE_DAVINCI_003,
            prompt=prompt,
            temperature=0.5,
            max_tokens=max_tokens,
            stop=["\n\n\n", "###"],
        )
    log_info(f"[{api_model_index} request cost token]: {response['usage']['total_tokens']}")
    log_info(f"[{api_model_index} available tokens]: {4000 - response['usage']['total_tokens']}")
    text = response['choices'][0]['text'].strip()
    return text


@log_openai_result
@handle_call_openai_api
def call_gpt3_5_turbo(prompt, apikey=None, verbo=True):
    api_model_index = ENGINE_TURBO
    response = openai.ChatCompletion.create(
        model=ENGINE_TURBO, 
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        stop=["###"]
    )
    if verbo:
        log_info(f"[{api_model_index} request cost token]: {response['usage']['total_tokens']}")
        log_info(f"[{api_model_index} available tokens]: {4000 - response['usage']['total_tokens']}")
    text = response['choices'][0]['message']['content'].strip()
    return text


MODEL_MAP = {
    ENGINE_DAVINCI_003: call_text_davinci_003,
    ENGINE_TURBO: call_gpt3_5_turbo
}

MODEL_EMBEDDING_MAP = {
    ENGINE_EMBEDDING_ADA_002: call_embedding_openai,
    ENGINE_DAVINCI_003: call_embedding_openai,
    ENGINE_TURBO: call_embedding_openai,
}

MODEL_LIST = [k for k in MODEL_MAP.keys()]

