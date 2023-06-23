from flask import Flask, request, render_template, redirect, url_for
import json

app = Flask(__name__)

# 全局变量（当前展示的数据索引、数据列表）
index = 0
data = []

src_file = 'annotation_data/data.json'
dst_file = 'annotation_data/data.json'

with open(src_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 显示当前数据及答案输入框
@app.route('/', methods=['GET'])
def show_question():
    if len(data) == 0:
        return "没有数据"
    global index
    index = min(max(index, 0), len(data) - 1)
    question = data[index]['question']
    id = data[index]['id']
    answer = data[index]['answer']
    turbo_answer = data[index].get('turbo_answer', '')
    # davinci_answer = data[index].get('davinci_answer', '')
    return render_template('question.html', question=question, id=id, answer=answer, turbo_answer=turbo_answer, index=index, max_page=len(data))
    # return render_template('question.html', question=question, id=id, answer=answer, davinci_answer=davinci_answer, index=index, max_page=len(data))


# 保存答案
@app.route('/save', methods=['POST'])
def save_answer():
    global index
    global dst_file
    answer = request.form['turbo_answer']
    data[index]['turbo_answer'] = answer.replace('\r\n', '\n')

    # answer = request.form['davinci_answer']
    # data[index]['davinci_answer'] = answer.replace('\r\n', '\n')

    with open(dst_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return redirect(url_for('show_question'))

# 显示下一条数据
@app.route('/next', methods=['GET'])
def next_question():
    global index
    index += 1
    return redirect(url_for('show_question'))

# 显示上一条数据
@app.route('/prev', methods=['GET'])
def prev_question():
    global index
    index -= 1
    return redirect(url_for('show_question'))

# 跳转
@app.route('/goto', methods=['GET'])
def goto_question():
    global index
    page = request.args.get('page')
    index = int(page) - 1
    return redirect(url_for('show_question'))

if __name__ == '__main__':
    app.run(debug=True, port=5005)