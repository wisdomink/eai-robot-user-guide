#!/usr/bin/env python3
"""
One-time helper: create the FF Master Support assistant on OpenAI
and print the ASSISTANT_ID to add to your .env file.

Usage:
    cd rag_server
    source venv/bin/activate
    python create_assistant.py
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INSTRUCTIONS = """\
你是一名专业的技术支持工程师，专门负责 FF Master Ultra Edition 机器人的用户支持。

规则：
1. 收到用户问题后，必须先使用 search_manual 工具搜索相关文档。
2. 仅根据搜索结果回答用户问题，不要使用任何外部知识。
3. 如果搜索结果中未提及相关信息，请直接回答："抱歉，说明书中未找到相关信息。"
4. 保持回答简洁、专业、结构化，使用中文回答。
5. 如果搜索结果中包含图片链接，请在回答中保留图片的 Markdown 语法。
6. 不要在回答中附加参考来源或引用链接，系统会自动在回答末尾添加。
"""

SEARCH_MANUAL_TOOL = {
    "type": "function",
    "function": {
        "name": "search_manual",
        "description": (
            "Search the FF Master robot user manual for relevant documentation. "
            "Always use this tool before answering any user question about the robot."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant documentation",
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}

assistant = client.beta.assistants.create(
    name="FF Master Support",
    instructions=INSTRUCTIONS,
    model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
    tools=[SEARCH_MANUAL_TOOL],
)

print(f"\n✅ Assistant created successfully!")
print(f"   ID:    {assistant.id}")
print(f"   Name:  {assistant.name}")
print(f"   Model: {assistant.model}")
print(f"\n👉 Add this to your .env file:")
print(f"   OPENAI_ASSISTANT_ID={assistant.id}\n")
