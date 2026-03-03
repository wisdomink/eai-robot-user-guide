#!/usr/bin/env python3
"""
Create the FF Master Support assistant on OpenAI with File Search (hosted RAG).

Uploads all markdown manual pages to an OpenAI Vector Store and creates
an assistant that uses the built-in file_search tool — no local ChromaDB
or custom embedding pipeline needed.

Usage:
    cd rag_server
    source venv/bin/activate
    python create_assistant.py
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = PROJECT_ROOT / "src" / "content"
SIDEBAR_PATH = CONTENT_DIR / "sidebar.json"
PAGES_DIR = CONTENT_DIR / "pages"

# ── Instructions ──────────────────────────────────────────────────────────
# This is the complete prompt for the Agent.  Paste it as-is into the
# OpenAI Agent Builder "Instructions" field if you prefer the UI workflow.
# ──────────────────────────────────────────────────────────────────────────

INSTRUCTIONS = """\
你是一名专业的技术支持工程师，专门负责 FF Master 系列机器人（FF Master / FF Master Edu / FF Master Ultra Edition）的用户支持。

## 你的知识来源

你的全部知识来自上传到 Vector Store 的用户手册文档（Markdown 文件）。这些文档涵盖：

| 分类 | 内容 |
|------|------|
| 安全须知 | 安全指南、安全注意事项、维护管理指南 |
| 产品介绍 | 装箱清单、产品概述（三个版本对比）、产品结构图、计算单元、电池指示灯、传感器视野、关节名称与限位、坐标系、规格参数 |
| 操作指南 | 安全预防措施、开机指南、关机指南、充电流程、遥控器使用指南、机器人交互流程、FF Robotic APP 手册、其他操作 |
| 运动平台 | 运动与操控平台手册 |
| 联系方式 | 联系信息 |

## 文档文件名 → 页面路径映射

当你引用文档内容时，以下映射关系用于前端页面导航。请在回答末尾标注所引用的文档来源文件名：

```
safety-instructions.md    → /safety-instructions
safety-guidelines.md      → /safety-guidelines
maintenance.md            → /maintenance-guidelines
packing-list.md           → /packing-list
product-overview.md       → /product-overview
computational-unit.md     → /computational-unit
battery-indicator.md      → /battery-indicator-lights
sensor-fov.md             → /sensor-fov
joint-limits.md           → /joint-limits
coordinate-systems.md     → /coordinate-systems
specifications.md         → /specifications
safety-precautions.md     → /safety-precautions
startup-guide.md          → /startup-guide
shutdown-guide.md         → /shutdown-guide
charging-procedure.md     → /charging-procedure
remote-control.md         → /remote-control
robot-interaction.md      → /robot-interaction
ff-robotic-app.md         → /ff-robotic-app
others.md                 → /others
locomotion-platform.md    → /locomotion-platform
contact-information.md    → /contact-information
```

## 回答规则

1. 收到用户问题后，系统会自动搜索相关文档（file_search）。仅根据搜索结果回答，**不要使用任何外部知识**。
2. 如果文档中未找到相关信息，直接回答："抱歉，说明书中未找到相关信息。"
3. 使用**中文**回答，保持简洁、专业、结构化（适当使用列表、表格）。
4. 如果文档中包含图片引用（如 `![alt](/images/docx/xxx.png)`），在回答中**保留完整的 Markdown 图片语法**。
5. **不要**在回答中手动附加引用标记或来源链接，系统会自动处理引用显示。
"""


def build_file_list() -> list[Path]:
    """Collect all page markdown files referenced in sidebar.json."""
    with open(SIDEBAR_PATH, "r", encoding="utf-8") as f:
        sidebar = json.load(f)

    files: list[Path] = []
    for section in sidebar.get("sections", []):
        for page in section.get("pages", []):
            filepath = PAGES_DIR / page["file"]
            if filepath.exists():
                files.append(filepath)
            else:
                print(f"⚠️  {page['file']} not found, skipping")
    return files


def main():
    md_files = build_file_list()
    print(f"📁 Found {len(md_files)} markdown files to upload\n")

    # 1. Create Vector Store
    vector_store = client.vector_stores.create(name="FF Robot User Manual")
    print(f"📦 Vector Store created: {vector_store.id}")

    # 2. Upload files in batch
    file_streams = [open(f, "rb") for f in md_files]
    try:
        batch = client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id,
            files=file_streams,
        )
        print(
            f"✅ Upload complete — "
            f"{batch.file_counts.completed} succeeded, "
            f"{batch.file_counts.failed} failed"
        )
    finally:
        for f in file_streams:
            f.close()

    # 3. Create Assistant with file_search
    assistant = client.beta.assistants.create(
        name="FF Master Support",
        instructions=INSTRUCTIONS,
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        tools=[{"type": "file_search"}],
        tool_resources={
            "file_search": {"vector_store_ids": [vector_store.id]},
        },
    )

    print(f"\n{'='*50}")
    print(f"✅ Assistant created!")
    print(f"   ID:            {assistant.id}")
    print(f"   Name:          {assistant.name}")
    print(f"   Model:         {assistant.model}")
    print(f"   Vector Store:  {vector_store.id}")
    print(f"{'='*50}")
    print(f"\n👉 Add to your .env file:")
    print(f"   OPENAI_ASSISTANT_ID={assistant.id}\n")


if __name__ == "__main__":
    main()
