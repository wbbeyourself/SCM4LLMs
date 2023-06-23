import json
from tools import *
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

data = []  # 将要标注的数据存储在这里
current_index = 0  # 当前数据的索引

src_path = 'annotation_data/zh-data-compare.json'
dst_path = 'annotation_data/zh-data-compare.json'

# src_path = 'annotation_data/en-data-compare.json'
# dst_path = 'annotation_data/en-data-compare.json'

# 加载数据
def load_data():
    global data
    # 从文件中读取数据并存储在 data 中
    # 以下代码仅作示例，请根据你的数据结构和数据存储方式进行修改
    data = load_json_file(src_path)


# 显示当前数据的界面
def show_data():
    global current_index
    # 获取当前数据
    tmp = data[current_index]
    item = {}
    for k, v in tmp.items():
        if isinstance(v, str):
            v = v.replace('\n', '<br>')
        item[k]  = v

    if 'annotated' not in item:
        item['annotated'] = False
    return render_template('data.html', **item, index=current_index, max_page=len(data))


# 处理标注结果
def process_result(obj):
    global current_index
    # 保存标注结果，这里仅作示例，请根据你的数据结构和数据存储方式进行修改
    data[current_index]['comparison_result'] = obj['comparison_result']
    data[current_index]['turbo_correct'] = obj['turbo_correct']
    data[current_index]['davinci_correct'] = obj['davinci_correct']
    data[current_index]['annotated'] = True
    save_json_file(dst_path, data)


# 显示下一条数据
@app.route('/next', methods=['GET'])
def next_question():
    global current_index
    current_index += 1
    return redirect(url_for('index'))


# 显示上一条数据
@app.route('/prev', methods=['GET'])
def prev_question():
    global current_index
    current_index -= 1
    return redirect(url_for('index'))


# 保存答案
@app.route('/save', methods=['POST'])
def save_answer():
    global current_index
    global dst_path

    # 处理标注结果
    process_result(request.form)
    # 切换到下一条数据的界面
    current_index += 1
    if current_index >= len(data):
        current_index = 0
    return redirect(url_for('index'))


# 跳转
@app.route('/goto', methods=['GET'])
def goto_question():
    global current_index
    page = request.args.get('page')
    current_index = int(page) - 1
    return redirect(url_for('index'))


@app.route("/", methods=["GET", "POST"])
def index():
    global current_index
    # 显示当前数据的界面
    return show_data()


# 启动服务器
if __name__ == '__main__':
    load_data()
    app.run()