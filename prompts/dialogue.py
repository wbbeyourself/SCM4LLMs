
zh_start_prompt = """假设你是人工智能助手， 请回答用户的问题和请求：

用户：{input}

助手："""

en_start_prompt = """Assuming you are an AI assistant, please answer the user's questions and requests:

User: {input}

Assistant: """


en_turn_summarization_prompt = """Below is a conversation between a user and an AI assistant. Please write a summary for each of them in one sentence and list them in separate paragraphs, while trying to preserve the key information of the user’s question and the assistant’s answer as much as possible.

conversation content: 

{input}

Summary:
"""

zh_turn_summarization_prompt = """以下是用户和人工智能助手的一段对话，请分别用一句话写出用户摘要、助手摘要，分段列出，要求尽可能保留用户问题和助手回答的关键信息。

对话内容： 

{input}

摘要：
"""

zh_no_history_agent_prompt = """以下是用户和人工智能助手的对话，请根据历史对话内容，回答用户当前问题：

上一轮对话：

{pre_turn_text}

###

用户：{input}

助手："""


en_no_history_agent_prompt = """The following is a conversation between a user and an AI assistant. Please answer the current question based on the history of the conversation:

Previous conversation:

{pre_turn_text}

###

User: {input}

Assistant: """


zh_history_agent_prompt = """以下是用户和人工智能助手的对话，请根据历史对话内容，回答用户当前问题：

相关历史对话：

{history_turn_text}

上一轮对话：

{pre_turn_text}

###

用户：{input}

助手："""


en_history_agent_prompt = """The following is a conversation between a user and an AI assistant. Please answer the current question based on the history of the conversation:

Related conversation history:

{history_turn_text}

Previous conversation:

{pre_turn_text}

###

User: {input}

Assistant: """


judge_answerable_prompt = """给定[对话内容]和[用户问题]，请回答指令问题。

[对话内容]:
```
{content}
```

[用户问题]:
```
{query}
```

指令问题: 
```
根据[对话内容]是否能够回答[用户问题]？如果能请回答 `(A)是`，否则请回答 `(B)否`。
```

现在请开始回答，输出必须严格按照以下格式输出：

[答案]: 最终的答案是：(A)是 / (B)否
"""