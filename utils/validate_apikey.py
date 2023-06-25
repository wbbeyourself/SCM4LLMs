import openai
import sys
sys.path.append('.')
sys.path.append('..')

from core.api import KEY_MANAGER

APIKEY_FILE = 'config/apikey.txt'

ENGINE_TURBO = 'gpt-3.5-turbo'

# 读取 apikey.txt 中的所有行
with open(APIKEY_FILE) as f:
    apikeys = [line.strip() for line in f]


def call_func(prompt, apikey):
    openai.api_key = apikey
    response = openai.ChatCompletion.create(
        model=ENGINE_TURBO, 
        messages=[{"role": "user", "content": prompt}],
        stop=["###"]
    )
    text = response['choices'][0]['message']['content'].strip()
    return text

# 验证每个 apikey 是否有效

QUOTA_ERROR = 'You exceeded your current quota'

valid_apikeys = []
for i, apikey in enumerate(apikeys):
    openai.api_key = apikey
    try:
        output = call_func('Tell me your name.', apikey)
        valid_apikeys.append(apikey)
        print(f"index: {i}, output: {output}")
        # print(f"index: {i}, {apikey} is valid. return text is : {output}")
    except Exception as e:
        error_msg = str(e)
        print(f"index: {i}, {apikey} is invalid. Exception: {e}")

# 将有效的 apikey 写回 apikey.txt 文件中
with open(APIKEY_FILE, 'w') as f:
    for apikey in valid_apikeys:
        f.write(f"{apikey}\n")