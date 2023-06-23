import os
from flask import Flask, request, render_template
import json

app = Flask(__name__)

target_file = './annotation_data/data.json'

def load_data_json():
    if not os.path.exists(target_file):
        return []
    with open(target_file, 'r', encoding='utf-8') as f:
        records = json.load(f)
    return records


def count_json(json_list, cur_id):
    count = 0
    for item in json_list:
        if item.get("id") == cur_id:
            count += 1
    return count


def save_data_json(data):
    with open(target_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def validate_input(id, question, answer):
    """
    校验函数
    """

    data = load_data_json()
    if len(data) > 1 and id == 'same':
        id = data[-1]['id']
    for item in data:
        if item['id'] == id and item['question'] == question and item['answer'] == answer:
            return f"重复添加 {str(item)}"

    if not id.strip() or not question.strip() or not answer.strip():
        return "输入不能为空，请输入一个有效的值。"

    return ""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        id = request.form['ID'].strip()
        question = request.form['Question'].replace('\r\n', '\n').strip()
        answer = request.form['Answer'].replace('\r\n', '\n').strip()
        mode = request.form['Mode'].replace('\r\n', '\n').strip()

        error_msg = validate_input(id, question, answer)
        if error_msg:
            # 校验失败，弹出提示框
            return render_template('index.html', error_msg=error_msg)
        else:
            # 校验成功，将表单数据编码为JSON对象，并将其保存到文件中
            one = {'id': id, 'question': question, 'answer': answer, 'mode': mode}
            data = load_data_json()

            if id == 'same':
                one['id'] = data[-1]['id']
                id = data[-1]['id']
            
            data.append(one)
            save_data_json(data)

            num_count = count_json(data, id)

            # 返回提交成功的提示
            return render_template('index.html', success_msg=f"提交成功！当前对话【{id}】已标注【{num_count}】个问题。")

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)