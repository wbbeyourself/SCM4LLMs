import os
import re
import sys
import tiktoken

sys.path.append('.')
sys.path.append('..')

from tools import *

turbo_tokenizer = tiktoken.encoding_for_model(ENGINE_TURBO)
davinci_tokenizer = tiktoken.encoding_for_model(ENGINE_DAVINCI_003)

content_path = 'evaluation_data/VCSum/dev_overall.json'
summary_path = 'evaluation_data/VCSum/long_dev.json'
dst_path = 'evaluation_data/VCSum/vc_summary.json'


def split_arr(arr):
    result = []
    start = 0
    for i in range(1, len(arr)):
        if arr[i] != arr[start]:  # 当出现不同的元素时，将前面的部分作为一组
            result.append([arr[start], list(range(start, i))])
            start = i
    result.append([arr[start], list(range(start, len(arr)))])  # 加入最后一组
    return result

id2all = {}
data = load_jsonl_file(content_path)
for i, obj in enumerate(data):
    uid = obj['av_num']
    if uid not in id2all:
        id2all[uid] = {}
    context_lst = obj['context']
    speaker_ids_lst = obj['speaker']
    speak_lst = split_arr(speaker_ids_lst)
    speak_data = []
    davinci_tokens = 0
    turbo_tokens = 0
    for spk_idx, ct_id_lst in speak_lst:
        turn = {}
        turn['role'] = f"Speaker {spk_idx}"
        cur_content = ''
        cur_ut_lst = [u for i, u in enumerate(context_lst) if i in ct_id_lst]
        ut_lst = []
        for utt_lst in cur_ut_lst:
            ut_lst.append(' '.join(utt_lst))
        cur_content = ' '.join(ut_lst)
        turn['content'] = cur_content

        davinci_tokens += len(davinci_tokenizer.encode(cur_content))
        turbo_tokens += len(turbo_tokenizer.encode(cur_content))
        speak_data.append(turn)
    id2all[uid]['dialogues'] = speak_data
    id2all[uid]['davinci_tokens'] = davinci_tokens
    id2all[uid]['turbo_tokens'] = turbo_tokens


data = load_jsonl_file(summary_path)
for i, obj in enumerate(data):
    uid = obj['av_num']
    id2all[uid]['summary'] = obj['summary']

save_json_file(dst_path, id2all)


