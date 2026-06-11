# 添加新产品说明书 — 操作手册

> 适用场景：将一份新产品的 `.docx` 说明书接入用户手册网站 + FF Assist 聊天系统。

---

## 概览

```
Step 1  DOCX → Markdown + 图片提取
Step 2  Markdown 按章节拆分为子页面 + 更新 sidebar.json
Step 3  注册产品路由（useProductContext.tsx）
Step 4  创建 OpenAI Vector Store 并同步文档
Step 5  接入 FF Assist（config + agent instructions + plan routing）
```

---

## Step 1 — DOCX 转 Markdown

### 1.1 安装依赖（首次）

```bash
pip3 install python-docx Pillow
```

### 1.2 参考转换脚本

参考 `scripts/convert_navi_docx.py`，为新产品新建一个同类脚本，例如 `scripts/convert_{product}_docx.py`。

**关键配置项：**

| 变量 | 说明 |
|---|---|
| `DOCX_PATH` | 源 docx 文件路径，放在 `docs/` 下 |
| `IMG_OUT_DIR` | `apps/web/public/images/{product}/` |
| `MD_OUT_PATH` | `apps/web/src/content/source/v3/{Product} Manual.md` |
| `HEADING_MAP` | `{ 段落index: 标题层级 }` — 需要根据文档结构手动标注 |
| `SKIP_INDICES` | 跳过的段落（空行、重复封面等） |
| `LIST_ITEM_INDICES` | 渲染为列表项（`-`）的段落 |
| `RID_TO_FILENAME` | `{ "rId6": "product-cover.png", ... }` — rId 与语义文件名的映射 |
| `RID_TO_ALT` | 对应图片的 alt 文本 |

**确认文档结构的方法：**

```bash
python3 - << 'EOF'
from docx import Document
doc = Document("docs/YourProduct.docx")
# 打印所有段落 + rId
for i, p in enumerate(doc.paragraphs):
    if p.text.strip():
        print(f"[{i:3d}] {p.text[:80]}")
# 打印图片 rel 映射
for rid, rel in doc.part.rels.items():
    if "image" in rel.reltype:
        print(f"  {rid} → {rel.target_ref}")
EOF
```

### 1.3 执行转换

```bash
python3 scripts/convert_{product}_docx.py
```

**产出：**
- `apps/web/public/images/{product}/` — 所有图片（按语义命名）
- `apps/web/src/content/source/v3/{Product} Manual.md` — 完整源 Markdown

---

## Step 2 — 拆分子页面 + 更新 sidebar.json

### 2.1 参考拆分脚本

参考 `scripts/split_navi_pages.py`，新建 `scripts/split_{product}_pages.py`。

**分页原则：**
- 每个 H2 大章节对应 1 个页面文件（短节可合并）
- 文件命名：`{product}/{product}-{section}.md`，例如 `navi/navi-power-on-off.md`
- 内容可在脚本里直接以字符串定义（便于手动优化），无需机械按行切割

**必须配置的 sidebar.json 结构：**

```json
"{product-id}": {
  "title": "FF XXXX",
  "sections": [
    {
      "id": "{product}-home",
      "title": "Home",
      "pages": [
        {
          "title": "FF XXXX Product Manual",
          "slug": "/{product}",
          "file": "{product}/{product}-home.md"
        }
      ]
    },
    {
      "id": "{product}-{section}",
      "title": "Section Title",
      "pages": [
        {
          "title": "Page Title",
          "slug": "/{product}/{page-name}",
          "file": "{product}/{product}-{page-name}.md"
        }
      ]
    }
  ]
}
```

### 2.2 执行脚本

```bash
python3 scripts/split_{product}_pages.py
```

**产出：**
- `apps/web/src/content/pages/{product}/` — 所有子页面 md 文件
- `apps/web/src/content/sidebar.json` — 注入新产品条目

---

## Step 3 — 注册产品路由

编辑 `apps/web/src/hooks/useProductContext.tsx`，两处修改：

### 3.1 扩展 ProductId 类型

```ts
export type ProductId = 'futurist' | 'futurist-ultra' | 'master' | 'aegis' | 'aegis-ultra' | 'ff91' | 'navi' | '{new-product}'
```

### 3.2 在 PRODUCTS 对象中添加条目

```ts
'{new-product}': {
  id: '{new-product}',
  label: 'FF XXXX',
  homeRoute: '/{new-product}',
  homeFile: '{new-product}/{new-product}-home.md',
  sidebar: allSidebars['{new-product}'],
},
```

> ⚠️ 这一步容易遗漏。如果跳过，所有 `/{new-product}/*` 路由都会命中 `path="*"` fallback，跳转到 `/futurist`。

### 3.3 验证

启动 dev server 后，访问 `/{new-product}` 及其子页面，确认不再跳转。

```bash
./apps/web/client_run.sh
```

---

## Step 4 — 创建 Vector Store 并同步文档

### 4.1 在 OpenAI 平台创建 Vector Store

登录 [platform.openai.com](https://platform.openai.com) → Storage → Vector Stores → Create，记录返回的 `vs_xxxxxxxx` ID。

### 4.2 更新环境变量

在 `apps/rag-api/.env` 中添加：

```env
OPENAI_VECTOR_STORE_{PRODUCT}_ID=vs_xxxxxxxxxxxxxxxx
```

### 4.3 更新 config.py

编辑 `apps/rag-api/app/core/config.py`，添加：

```python
OPENAI_VECTOR_STORE_{PRODUCT}_ID: str = os.getenv("OPENAI_VECTOR_STORE_{PRODUCT}_ID", "")
```

### 4.4 同步文档到 Vector Store

`create_vector_store.py` 会读取 `sidebar.json` 里所有产品的 md 文件，一次性同步到 `OPENAI_VECTOR_STORE_ROBOT_ALL_ID`（全量 Vector Store）。

```bash
cd apps/rag-api
source venv/bin/activate
python create_vector_store.py
```

若还需要为该产品创建**独立的 Vector Store**（用于精准路由），同样运行上述脚本但指向单产品 VS，或手动上传对应 md 文件。

---

## Step 5 — 接入 FF Assist

需要改动 3 个文件：

### 5.1 新增 Agent Instructions 文件

新建 `apps/rag-api/app/services/instructions/product-{product}.md`，参考 `product-aegis.md` 的格式：

```markdown
你是 FF {Product} Product Agent 的官网资料检索子模块。你当前只负责从资料库中提取与问题相关的信息，供下游 Output Agent 汇总。

回答语言：{{input_lang}}
检索查询：{{query_text}}

## 资料范围

| 分类 | 内容 |
|------|------|
| ... | ... |

## 检索要求

1. 必须先使用 `{{query_text}}` 调用 `file_search`。
2. 输出的是"检索结果摘要"，不是最终客服答复。
3. 仅整理与该产品直接相关的信息。
4. 优先保留有明确价值的细节：参数、步骤、警告、限制。
5. 如果命中文本里包含图片 Markdown，请完整保留原样。
6. 不要手动附加引用标记，系统会统一处理。

## 输出格式

### 结论
### 关键依据
### 细节摘录
### 缺失与不确定项
```

### 5.2 注册 Agent 配置

编辑 `apps/rag-api/app/services/chatkit_handler.py`，在 `_SUPPORT_AGENT_CONFIGS` 中添加：

```python
"{product}": {
    "name": "FF {Product} Product Agent",
    "instructions_file": "product-{product}",
    "vector_store_id": OPENAI_VECTOR_STORE_{PRODUCT}_ID,
},
```

同时在 `config.py` 的 import 处加上新的 vector store ID 变量。

### 5.3 更新 Plan Agent 路由表

编辑 `apps/rag-api/app/services/instructions/plan.md`，两处：

**① 产品路由表中添加一行：**

```markdown
| `{product}` | {Product}、关键词1、关键词2、... |
```

**② 字段约束中加入合法值：**

```markdown
- `product_key` 只能是 `"master"`、`"futurist"`、`"futurist-ultra"`、`"aegis"`、`"aegis-ultra"`、`"ff91"`、`"navi"`、`"{product}"`
```

### 5.4 重启 RAG 服务

```bash
./apps/rag-api/server_run.sh
```

---

## 检查清单

```
[ ] docs/{Product}.docx 已放入 docs/
[ ] scripts/convert_{product}_docx.py 已按文档结构配置
[ ] apps/web/public/images/{product}/ 图片已按语义命名
[ ] apps/web/src/content/source/v3/ 源 md 已生成
[ ] apps/web/src/content/pages/{product}/ 子页面已创建
[ ] sidebar.json 已注入 {product} 条目
[ ] useProductContext.tsx ProductId 类型已扩展
[ ] useProductContext.tsx PRODUCTS 对象已添加条目
[ ] 浏览器访问 /{product} 及子页面正常，不跳转
[ ] .env 已添加 OPENAI_VECTOR_STORE_{PRODUCT}_ID
[ ] config.py 已添加对应常量
[ ] create_vector_store.py 已同步文档
[ ] product-{product}.md instructions 文件已创建
[ ] chatkit_handler.py _SUPPORT_AGENT_CONFIGS 已注册
[ ] plan.md 路由表和字段约束已更新
[ ] RAG 服务已重启，FF Assist 可正确路由到新产品
```

---

## 文件路径速查

| 用途 | 路径 |
|---|---|
| 源 docx | `docs/{Product}.docx` |
| 转换脚本 | `scripts/convert_{product}_docx.py` |
| 分页脚本 | `scripts/split_{product}_pages.py` |
| 图片目录 | `apps/web/public/images/{product}/` |
| 源 Markdown | `apps/web/src/content/source/v3/` |
| 子页面目录 | `apps/web/src/content/pages/{product}/` |
| 导航配置 | `apps/web/src/content/sidebar.json` |
| 路由注册 | `apps/web/src/hooks/useProductContext.tsx` |
| RAG 环境变量 | `apps/rag-api/.env` |
| RAG 配置 | `apps/rag-api/app/core/config.py` |
| Vector Store 同步脚本 | `apps/rag-api/create_vector_store.py` |
| Agent Instructions | `apps/rag-api/app/services/instructions/product-{product}.md` |
| Agent 注册 | `apps/rag-api/app/services/chatkit_handler.py` |
| Plan 路由表 | `apps/rag-api/app/services/instructions/plan.md` |
