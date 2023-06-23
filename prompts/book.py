zh_start_prompt = """给定一段文本(用三个反引号括起来的文本)，请写出对应的摘要，请严格按照以下要求执行:

要求:
(1) 输出内容使用中文;
(2) 输出内容最多不超过500字.

文本内容: 
```{text}```

摘要:
"""


en_start_prompt = """Given a text, delimited by triple backticks, please write a corresponding summary strictly following the following requirements:

Requirements:
(1) Output content in English;
(2) The output should not exceed 500 words at most.

Text Content:
```{text}```

Summary:
"""


zh_agent_scm_prompt = """给定当前文本和上文内容，请写出当前文本的摘要，请严格按照以下要求执行:

要求: 
(1) 将上文内容只作为理解当前文本的背景信息; 
(2) 对当前文本进行摘要，摘要里不再重复上文内容的任何信息; 
(3) 输出内容使用中文; 
(4) 输出内容最多不超过500字; 
(5) 摘要以 "该段描述了 ..." 开头，描述该段文本的主题。

上文内容: {previous_content}

当前文本: {current_text}

摘要: 
"""


en_agent_scm_prompt = """Given the current text and the previous content, please provide a summary of the current text in strict accordance with the following requirements:
    
Requirements:
(1）Use the previous text only as background information to understand the current text;
(2）Summarize the current text without repeating any information from the previous text;
(3) The output should be in English;
(4) The output should not exceed 500 words at most;
(5) Start the summary with "This section describes..." to explain the main theme of the text.

Previous Content: {previous_content}

Current Text: {current_text}

Summary:
"""



zh_agent_no_scm_prompt = """给定一段文本(用三个反引号括起来的文本)，请写出对应的摘要，请严格按照以下要求执行:

要求:
(1) 输出内容使用中文;
(2) 输出内容最多不超过500字;
(3) 摘要以 "该段描述了 ..." 开头，描述该段文本的主题.

文本内容: 
```{text}```

摘要:
"""


en_agent_no_scm_prompt = """Given a text, delimited by triple backticks, please write a corresponding summary strictly following the following requirements:

Requirements:
(1) Output content in English;
(2) The output should not exceed 500 words at most;
(3) Start the summary with "This section describes..." to explain the main theme of the text.

Text Content:
```{text}```

Summary:
"""



zh_hierarchical_summarization_prompt = """给定一个文档的各个段落摘要(用三个反引号括起来的文本)，请写出该文档的最终摘要，请严格按照以下要求执行:

要求:
(1) 对各个段落的摘要进行分析，提取关键信息并组织成一段逻辑通顺的文本;
(2) 摘要内容要使用中文;
(3) 摘要只保留最紧凑的30%的核心信息;
(4) 最终摘要的字数不能超过{max_tokens}个字符.

各段落摘要:
```{paragraph_summaries}```

文档摘要:
"""


en_hierarchical_summarization_prompt = """Given the summaries of each paragraph in a document, delimited by triple backticks, write the final summary of the document in accordance with the following requirements:

Requirements:
(1) Analyze the summaries of each paragraph, extract key information, and organize it into a logically coherent text;
(2) Write the summary in English;
(3) The summary should only retain the most compact 30% of the core information;
(4) The final summary cannot exceed {max_tokens} characters.

Summaries of each paragraph:
```{paragraph_summaries}```

Document Summary:
"""