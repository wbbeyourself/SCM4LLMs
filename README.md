# Enhancing Large Language Model with Self-Controlled Memory Framework

This is the official repository for the paper ["Enhancing Large Language Model with Self-Controlled Memory Framework"](https://arxiv.org/abs/2304.13343). In this paper, we introduce the **Self-Controlled Memory (SCM)** system to unleash infinite-length input capacity for large-scale language models.
Our SCM system is composed of three key modules: the language model agent, the memory stream, and the memory controller. 

<img src="misc/workflow.png" align="middle" width="95%">

# 🔥 Updates
- [**2024-02-18**] Newest version of the paper is released. We update the paper with more details and experiments.
- [**2023-4-26**] We released our first version [paper](https://arxiv.org/abs/2304.13343), [codes](https://github.com/wbbeyourself/SCM4LLMs). Check it out!

# 🌟 Overview

Our SCM system can be integrated with any LLMs to enable them to process ultra-long texts without any modification or fine-tuning. 



## Supported Tasks

| Tasks                            |            Status            |
| -------------------------------- | :--------------------------: |
| Long-Term Dialogue               | :white_check_mark: Supported |
| Ultra-long Book Summarization    | :white_check_mark: Supported |
| Ultra-long Meeting Summarization | :white_check_mark: Supported |



# ⚡️ Usage

## config

In `config` directory, copy `apikey.txt.template` to `apikey.txt`, put your openai apikey in it, support multiple keys. This file is ignored to protect privacy.

Note: If the ChatGPT service is unavailable in your area, please utilize proxy settings. Copy `config\api_config.template.json` to `config\api_config.json` and config `http_proxy` as you like.

## Requirements

The key requirements are as below:

- python 3.8+
- openai 0.27.0+
- gradio 3.27.0+

Use conda to create environment.
```shell
conda create -n scm python=3.8 -y
conda activate scm
```

You can install the requirements by running:
```shell
pip install -r requirements.txt
```

## Run

Default agent model use `text-davinci-003`.

You can specify model by `--model_name`, current support model list: 
- `text-davinci-003`
- `gpt-3.5-turbo`



### 👻Long-Term Dialogue

Run this command, chat with model. Chat logs are recorded in `logs\log.txt`.

```bash
python dialogue_demo.py
```

Functional command during dialogue, these operations will be silently done, you can see them in the log output:
- `reset` or `清空`: clear dialogue history.
- `export` or `导出`: save the dialogue history to files.
- `roll back` or `回滚`: pop previous turn dialogue.

### 📚Ultra-long Book Summarization

Take the shortest book `The Old Man and the Sea`, whose content cost 34k tokens, as a demo example:
```bash
python book_summary.py   --book_files data/book/EnglishBook/The_Old_Man_and_the_Sea.txt
```

### 📝Ultra-long Meeting Summarization

Take the blockchain meeting as example, whose content cost 37k tokens, as a demo example:
```bash
python meeting_summary.py --meeting_ids 26231372_区块链技术的应用前景
```

# 📝 Evaluation Dataset

Data files are in `data` folder.

|                | Dialogue | Book  | Meeting |
|----------------|----------|-------|---------|
| \#Instances    | 18       | 10    | 20      |
| Max tokens     | 34k      | 2M    | 50k     |
| Total tokens   | 420k     | 8M    | 632k    |
| Max turn       | 200      | -     | 80      |
| Language       | En+Zh    | En+Zh | Zh      |

Evaluation dataset statistics. 2M means 2 miillion token count.

# 📊 Evaluation Results

- [Chinese Long-term Dialogue QA results](results/markdown_results/long_term_dialogue_zh.md)
- [English Long-term Dialogue QA results](results/markdown_results/long_term_dialogue_en.md)
- [Book Summarization results](results/markdown_results/book_summary.md)
- [Meeting Summarization Results](results/markdown_results/meeting_summary_zh.md)

More running records and summary details are zipped to `history.zip`. You can download it from [Google Drive Link](https://drive.google.com/file/d/1iPsZnClj170W5vZyrFADoVZoXICb1ELo/view?usp=sharing) and [Baidu Netdisk](https://pan.baidu.com/s/1TPdTP7LBJZAopxckyIfb8A?pwd=yqwa).
`call_embedding_history.json` and `call_func_history.json` store the openai cache log and are zipped in `logs.zip`. You can download it from [Google Drive Link](https://drive.google.com/file/d/17Tx294kixfgFfAkB0Z98q1M_aT5OOZEU/view?usp=sharing) and [Baidu Netdisk](https://pan.baidu.com/s/1yo2p_m-aRbTd5hIyNTlL4Q?pwd=ka6j).

# ⚠️ Limitations & Risks

> we will assess the efficacy of our system on more open-source models that possess single-turn instruction comprehension capability.


> Our system has the capability to attach to any LLMs, which may be prone to factual errors, delusions, toxic language, and malicious responses. Consequently, we restrict the usage of our system to academic research purposes for now.

# 💬 Citation

If you find our work is helpful, please cite as:
```
@article{liang2023unleashing,
      title={Enhancing Large Language Model with Self-Controlled Memory Framework}, 
      author={Bing Wang, Xinnian Liang, Jian Yang, Hui Huang, Shuangzhi Wu, Peihao Wu, Lu Lu, Zejun Ma, Zhoujun Li},
      year={2023},
      eprint={2304.13343}
}
```

# 👍 Contributing

We welcome contributions and suggestions!
