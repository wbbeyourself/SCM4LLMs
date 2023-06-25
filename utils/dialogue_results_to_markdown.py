from tools import *

class Markdown(object):

    def __init__(self) -> None:
        self.lines = []
    
    def print(self, text):
        self.lines.append(text)
    
    def save(self, filename):
        save_file(filename, self.lines)


path = 'annotation_data\dialogue\dialogue_zh_questions.json'
out = 'results\markdown_results\long_term_dialogue_zh.md'

data = load_json_file(path)

printer = Markdown()

printer.print(f"# Long-term Dialogue Questions and Answers\n\n")

dial_map =  {}

for i, item in enumerate(data):
    dial_id = item['id']
    if dial_id not in dial_map:
        printer.print(f"\n\n## Dialogue ID: {dial_id}\n\n")
        dial_map[dial_id] = 1
    turbo_ans = item["scm_turbo_answer"].replace("\n\n", '##').replace('\n', '\n>').replace('##', '\n\n').replace("\n\n", "\n>\n>")
    davinci_ans = item["scm_davinci_answer"].replace("\n\n", '##').replace('\n', '\n>').replace('##', '\n\n').replace("\n\n", "\n>\n>")
    gold_answer = item['answer'].replace("\n\n", '##').replace('\n', '\n>').replace('##', '\n\n').replace("\n\n", "\n>\n>")
    
    printer.print(f"### {item['question_id']}\n")
    printer.print(f'<span style="color:green">Question:</span>\n')
    printer.print(f"```text\n{item['question']}\n```\n")
    printer.print(f'\n\n')
    printer.print(f'<span style="color:purple">Gold Answer:</span>\n')
    printer.print(f'>{gold_answer}\n')
    printer.print(f'\n\n')
    printer.print(f'<span style="color:red">SCM-Turbo result:</span>\n')
    printer.print(f'>{turbo_ans}\n')
    printer.print(f'\n\n')
    printer.print(f'<span style="color:blue">SCM-Davinci003 result:</span> \n')
    printer.print(f'>{davinci_ans}\n')

makedirs(out)
printer.save(out)


