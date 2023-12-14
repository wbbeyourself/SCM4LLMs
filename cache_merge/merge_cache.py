import sys
sys.path.append('.')
sys.path.append('..')
sys.path.append('../..')
from tools import *
import os
from os.path import join
from copy import deepcopy
from collections import OrderedDict

root = 'C:/Users/xxx/Desktop/cache_center'

def merge_text_cache(files):
    global root
    d = {}
    for i, path in enumerate(files):
        base: str = os.path.basename(path)
        if not base.startswith('call_func_history'):
            continue
        for js in load_jsonl_file(path):
            if not js:
                continue
            func = js['function']
            _input = js['input']
            key = f"{func}_{_input}"
            d[key] = deepcopy(js)
    new_data = []
    sorted_d = OrderedDict(sorted(d.items(), key=lambda x: x[0]))
    for k, v in sorted_d.items():
        new_data.append(v)
    out = join(root, 'merge_func_history.json')
    save_jsonl_file(out, new_data)
    return 0


def merge_embedding_cache(files):
    global root
    d = {}
    for i, path in enumerate(files):
        base: str = os.path.basename(path)
        if not base.startswith('call_embedding_history'):
            continue
        for js in load_jsonl_file(path):
            if not js:
                continue
            func = js['function']
            _input = js['input']
            key = f"{func}_{_input}"
            d[key] = deepcopy(js)
    new_data = []
    sorted_d = OrderedDict(sorted(d.items(), key=lambda x: x[0]))
    for k, v in sorted_d.items():
        new_data.append(v)
    out = join(root, 'merge_embedding_history.json')
    save_jsonl_file(out, new_data)
    return 0


def main():
    files = get_files(root, suffix='.json')
    # merge_text_cache(files)
    merge_embedding_cache(files)
    return 0

main()
