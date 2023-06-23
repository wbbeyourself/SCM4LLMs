# coding=utf-8
import re
import os
import time
import json
import chardet
import pickle
import tiktoken

ENGINE_TURBO = 'gpt-3.5-turbo'
ENGINE_DAVINCI_003 = 'text-davinci-003'
ENGINE_EMBEDDING_ADA_002 = 'text-embedding-ada-002'

LANG_EN = 'English'
LANG_ZH = 'Chinese'
LANG_UN = 'Unknown'


def detect_language(text):
    # 统计总字符数和英文字符数
    total_count = len(text)
    en_count = len(re.findall(r'[a-zA-Z]', text))
    # 判断英文字母占比是否超过60%
    if en_count / total_count > 0.6:
        return LANG_EN
    else:
        return LANG_ZH


def detect_encode_type(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
        result = chardet.detect(data)
        return result['encoding']


def get_token_count_davinci(text):
    tokenizer = tiktoken.encoding_for_model(ENGINE_DAVINCI_003)
    tokens = tokenizer.encode(text)
    return len(tokens)


def print_doc(json_list):
    with open('tmp.txt', 'w') as f:
        for item in json_list:
            doc = item.get('doc')
            if doc:
                f.write(doc + '\n')
                f.write('-' * 30)
                f.write('\n\n')


# 递归新建文件夹
def makedirs(filename):
    dir_path = os.path.dirname(os.path.abspath(filename))
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print('makedirs %s' % dir_path)


# 将数据保存为pickle文件
def save_pickle_file(data, filename):
    makedirs(filename)
    with open(filename, 'wb') as f:
        pickle.dump(data, f)
    print('saved pkl file ', filename)


# 加载pickle文件
def load_pickle_file(filename):
    with open(filename, 'rb') as f:
        data = pickle.load(f)
    return data


# 把content列表保存成文本文件
def save_file(filename, content):
    """
    :param filename: 输出文件名
    :param content: 句子列表 默认每个元素自带换行啊
    :return:
    """
    makedirs(filename)
    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(content)
    print('save file %s successful!' % filename)


def save_jsonl_file(filename, data, indent=None):
    """
    :param filename: 输出文件名
    :param data: 数据对象，List[json]
    :param indent: 缩进
    :return: json line format file
    """
    makedirs(filename)
    with open(filename, 'w', encoding='utf-8') as fp:
        for js in data:
            if indent:
                js_str = json.dumps(js, indent=indent, ensure_ascii=False)
            else:
                js_str = json.dumps(js, ensure_ascii=False)
            fp.write(js_str + '\n')
    print('save file %s successful!' % filename)


def save_json_file(filename, data):
    """
    :param filename: 输出文件名
    :param data: 数据对象，json/list
    :return:
    """
    makedirs(filename)
    with open(filename, 'w', encoding='utf-8') as fp:
        json.dump(data, fp, indent=2, ensure_ascii=False)
    print('save file %s successful!' % filename)


def load_json_file(filename):
    """
    :param filename: 文件名
    :return: 数据对象，json/list
    """
    with open(filename, encoding='utf-8') as fp:
        data = json.load(fp)
    return data


def load_jsonl_file(path):
    lines = get_lines(path)
    data = [json.loads(x) for x in lines]
    return data


# 给定文件名，和待pickle的对象，用新文件将其覆盖
def overwrite_pkl_file(filename, data):
    tmp_filename = filename + '.swp'
    save_pickle_file(data, tmp_filename)
    if os.path.exists(filename):
        os.rename(filename, filename + '.old.' + datetime2str())
    os.rename(tmp_filename, filename)
    print('overwrite %s successful!' % filename)


# 给定文件名，和待保存的字符串列表，用新文件将其覆盖
def overwrite_txt_file(filename, data):
    tmp_filename = filename + '.swp'
    
    save_file(tmp_filename, data)
    if os.path.exists(filename):
        os.rename(filename, filename + '.old.' + datetime2str())
    os.rename(tmp_filename, filename)
    print('overwrite %s successful!' % filename)


# 读取文件的每一行, 返回列表
def get_lines(filename):
    with open(filename, encoding='utf-8') as f:
        data = [i.strip() for i in f.readlines() if i.strip() != '']
        return data


# 读取文件的每一行, 返回列表
def get_txt_content(filename):
    with open(filename, encoding='utf-8') as f:
        text = f.read()
        return text


def get_files(root, suffix):
    """
    获取指定目录下的所有指定后缀的文件
    :param root: 指定目录 str 类型  如：'.'
    :param suffix: 指定后缀 str 类型 如：'.txt'
    :return: 文件列表
    """
    import os
    import glob
    if not os.path.exists(root):
        raise FileNotFoundError(f'path {root} not found.')
    res = glob.glob(f'{root}/**/*{suffix}', recursive=True)
    res = [os.path.abspath(p) for p in res]
    return res


# 判断一个词语是不是纯中文词语，即不包含汉字以外的其他符号
def is_chinese_word(word):
    for c in word:
        if not ('\u4e00' <= c <= '\u9fa5'):
            # print(word)
            return False
    return True


# 判断一个字符是不是中文字符
def is_chinese_char(c):
    if len(c.strip()) == 1 and '\u4e00' <= c <= '\u9fa5':
        return True
    return False


def datetime2str():
    from datetime import datetime
    return datetime.now().strftime('%Y%m%d-%H%M%S')


# 计算从start到现在花费的时间
def time_cost(start):
    cost = int(time.time() - start)
    h = cost // 3600
    m = (cost % 3600) // 60
    print('')
    print('【%s】到目前总耗时: cost %s hours %s mins' % (datetime2str(), h, m))


# 将 content_list 追加到filename中
def append_file(filename, content_list, new_line=False):
    if not content_list:
        return
    if new_line:
        content_list = [text if text.endswith('\n') else text+'\n' for text in content_list]
    with open(filename, 'a+', encoding='utf-8') as f:
        f.writelines(content_list)
    # timestamp = datetime2str()
    # print('[%s]: append_file %s successful!' % (timestamp, filename))


def keep_only_alnum_chinese(s):
    # 只保留中英文字符和数字的正则表达式
    pattern = re.compile(r'[^\u4e00-\u9fa5a-zA-Z0-9]')

    # 去除非中英文字符和数字，得到新字符串
    s2 = re.sub(pattern, '', s)
    return s2


def choose_language_template(lang2template: dict, text: str):
    lang = detect_language(text)
    if lang not in lang2template:
        lang = LANG_EN
    return lang2template[lang]


def replace_newline(text):
    # print(f"\n\nraw:\n{text}\n--------------\n")
    result = ""
    code_start = False
    for i in range(len(text)):
        if i>=3 and text[i-3: i] == "```":
            code_start = not code_start
            if code_start == False:
                result += f"\n{text[i]}"
            else:
                result += text[i]
        elif not code_start and text[i] == "\n":
            result += "<br>\n"
        else:
            result += text[i]
    # print(f"\n\nresult:\n{result}\n--------------\n")
    return result