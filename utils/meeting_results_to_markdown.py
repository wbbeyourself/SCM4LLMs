from tools import *

class Markdown(object):

    def __init__(self) -> None:
        self.lines = []
    
    def print(self, text):
        self.lines.append(text)
    
    def save(self, filename):
        save_file(filename, self.lines)


gold_summary_path = 'data/meeting/vc_summary.json'
pred_summary_dir = 'history/meeting-sum/'
out = 'results/markdown_results/meeting_summary_zh.md'

mid_lst = []

gold_summary_data = load_json_file(gold_summary_path)
id2gold_summary = {}
for i, obj in enumerate(gold_summary_data):
    mid = obj['meeting_id']
    mid_lst.append(mid)
    summary = obj['summary']
    id2gold_summary[mid] = summary

pred_summary_data = {}

files = get_files(pred_summary_dir, '.json')
for fname in files:
    lst = load_json_file(fname)
    uid = fname.split('meeting-summary-')[-1][:-5]
    print(f"uid : {uid}")
    pred_sum = lst[-1]['final summary']
    
    pred_summary_data[uid] = pred_sum

printer = Markdown()

printer.print(f"# Meeting Summary of SCM\n\n")

dial_map =  {}

for i, mid in enumerate(mid_lst):
    printer.print(f"\n\n## {mid}\n\n")
    uid_turbo = f"{mid}-{ENGINE_TURBO}"
    uid_davinci = f"{mid}-{ENGINE_DAVINCI_003}"

    turbo_ans = pred_summary_data[uid_turbo]
    davinci_ans = pred_summary_data[uid_davinci]
    gold_answer = id2gold_summary[mid]

    printer.print(f'\n\n')
    printer.print(f'<span style="color:purple">Reference Summary:</span>\n')
    printer.print(f'>{gold_answer}\n')
    printer.print(f'\n\n')
    printer.print(f'<span style="color:red">SCM-Turbo result:</span>\n')
    printer.print(f'>{turbo_ans}\n')
    printer.print(f'\n\n')
    printer.print(f'<span style="color:blue">SCM-Davinci003 result:</span> \n')
    printer.print(f'>{davinci_ans}\n')

makedirs(out)
printer.save(out)


