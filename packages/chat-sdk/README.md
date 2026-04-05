# @ffrobot/chat-sdk

ChatPanel 聊天面板 SDK — 构建为 IIFE 单文件，通过 `<script>` 标签嵌入任意网页。

## 使用方式

**唯一入口**：`<script>` 标签加载 `ffrobot-chat-sdk.js`，通过 `window.FFRobotChat` 全局 API 使用。

```html
<script src="ffrobot-chat-sdk.js"></script>
<script>
  FFRobotChat.init({
    defaultOpen: true,
  });
</script>
```

## 构建

```bash
# 本地调试（API → http://127.0.0.1:8000）
./packages/chat-sdk/build.sh debug

# 生产发布（API → https://robotics-instruction-manual.ff.com）
./packages/chat-sdk/build.sh release
```

产物：`dist-embed/ffrobot-chat-sdk.js`，同时自动复制到 `apps/web/public/`。

## API

| 方法 | 说明 |
|------|------|
| `FFRobotChat.init(options?)` | 初始化 SDK，返回 `Promise<FFRobotChatInstance>` |
| `FFRobotChat.open()` | 打开聊天面板 |
| `FFRobotChat.close()` | 关闭聊天面板 |
| `FFRobotChat.destroy()` | 销毁实例并移除 DOM |
| `FFRobotChat.update(options)` | 更新配置 |
| `FFRobotChat.getInstance()` | 获取当前实例 |

## TypeScript 支持

引入 `packages/chat-sdk/types/global.d.ts` 即可获得 `window.FFRobotChat` 的类型提示：

```json
{
  "include": ["src", "../../packages/chat-sdk/types/global.d.ts"]
}
```

## 依赖

构建时自动打包以下依赖（消费方无需安装）：
- `react`、`react-dom`、`@openai/chatkit-react`、`clsx`
