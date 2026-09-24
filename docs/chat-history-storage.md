# 聊天记录持久化

AWS 部署使用独立 DynamoDB 表 `eai-robot-chat-history`。新会话、消息、卡片、会话语言及 Agent 轨迹写入数据库，后端重启或重新发布后继续可读。上线前仅在内存中的记录不迁移。

## 配置与发布

- `CHAT_BACKEND=memory`：默认本地开发模式，重启即清空。
- `CHAT_BACKEND=dynamodb`：数据库模式；必须设置 `CHAT_DDB_TABLE`。
- AWS 区域沿用 `AWS_DEFAULT_REGION` / `AWS_REGION`。
- `aws-deploy.sh --build` 会创建聊天表与 `threads-by-created` 索引、更新 ECS 角色权限，并向新任务注入数据库配置。已有表不会被清空。使用平时的 AWS profile 和部署参数即可。
- 发布前需要重新构建镜像；只更新任务配置、继续使用旧镜像不会启用新存储。
- 本次不设置 TTL，数据不会自动过期。回滚到旧版服务不会删除表，但旧版不会读写此表。

## 数据组织

每个会话一个分区 `THREAD#<id>`：

- `META`：会话信息，同时进入按创建时间排序的稀疏 GSI。
- `ITEM#<UTC timestamp>#<id>`：完整消息，按时间排序。
- `ID#<id>`：消息 ID 到排序键的映射，供更新、单条查询和分页使用。
- `LANG`：会话语言。
- `TRACE#<timestamp>#<id>`：Agent 执行轨迹。
- `CHUNK#<version>#<number>`：超大内容分块。

数据以压缩 JSON 保存，保留 ChatKit 类型信息以及浮点数。压缩后超过 300 KB 的内容分块写入，所有分块成功后才发布主记录。失败不会替换已有完整版本。为保证并发读取安全，旧分块及失败写入遗留分块保留到删除整个会话；因此反复更新超大消息会增加存储占用。普通消息更新直接覆盖，不产生额外版本。

消息按稳定的 ID 和创建时间幂等写入。调用方必须保留已有消息的创建时间。数据库使用有限重试；失败记录日志并向上抛出，不静默降级到内存。完整消息在 ChatKit 的消息完成事件时保存，不逐 token 写库；服务强制退出时未完成的回复不保证完整保存。

同步 boto3 操作在线程池运行，每个工作线程持有独立资源实例，不阻塞异步事件循环。详情与上下文使用强一致读取；列表 GSI 为最终一致，新会话可能短暂延迟出现。

## 历史接口

- `GET /api/chat-history?limit=50&order=desc&after=<thread_id>`
- `GET /api/chat-history/<thread_id>?limit=500&after=<item_id>`

原返回字段保留，新增 `after`；详情新增 `has_more`。继续查询时传回响应中的 `after`，直到 `has_more=false`。列表 `total` 仍表示本页数量，不是数据库总量。详情消息默认正序；每页仍附带该会话的全部轨迹。

列表使用索引 Query，不执行全表 Scan。为保持原接口的精确消息数与首条消息，仍需按每个会话查询消息摘要；查询开销随该会话消息数量增加。Projection 减少网络传输，但不会减少 DynamoDB 按记录大小计算的读取单位。详情中的全部轨迹也会随会话长度增长。当前适用于客服聊天规模，若有大量超长会话或高频后台轮询，再增加持久化摘要及轨迹分页。

历史接口沿用现有访问控制，本次未新增鉴权。长期保存后，部署侧应确保历史查询入口只向预期使用者开放。

## 验证

安装测试依赖后运行：

```bash
apps/rag-api/venv/bin/python -m pip install -r apps/rag-api/requirements-test.txt
PYTHONDONTWRITEBYTECODE=1 apps/rag-api/venv/bin/python -m unittest discover -s apps/rag-api/tests
```

新增测试使用 Moto 模拟 AWS，验证新存储实例恢复、继续对话、覆盖去重、分页、超过 1 MB 数据库查询页、超大消息分块、写入失败不覆盖旧消息、删除和 HTTP 历史接口。

实际发布后的验收：创建测试会话并记下 ID，确认历史接口可读取；重启或重新发布后再次读取同一 ID，并继续发送消息。模拟测试不替代此线上验收。
