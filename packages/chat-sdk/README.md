# @ffrobot/chat-sdk

ChatPanel 聊天面板 SDK — 构建为 IIFE 单文件，通过 `<script>` 标签嵌入任意网页。

## 使用方式

**唯一入口**：`<script>` 标签加载 `ffrobot-chat-sdk.js`，通过 `window.FFRobotChat` 全局 API 使用。

```html
<script src="ffrobot-chat-sdk.js"></script>
<script>
  FFRobotChat.init();
</script>
```

默认聊天面板为收起状态；若需在加载后自动展开，可传入 `defaultOpen: true`。

右下角入口依次为 `Order Now`（上）和 `FF Assist`（下）。打开聊天时两者一起隐藏，关闭聊天后恢复；`showFab: false` 同时隐藏两个入口。

### Order Now

SDK 初始化时从 ChatKit API 所在服务的 `/api/get-order-now-config` 独立加载全部启用规则。同一页面内缓存请求及结果，内部路由跳转和重复初始化不会重新请求；完整刷新页面后获取最新配置。

入口文字由规则中的 `button_label` 决定，默认 `Order Now`；Nova 显示 `Apply Now`，Faber 显示 `Contact Sales`。点击时使用当前 `window.location.href`（或显式传入的 `hostUrl`）本地匹配，并在新标签页打开目标链接。匹配优先级为精确 URL、最长路径前缀（`/*`）、默认商城首页；来源 URL 的查询参数、hash 和末尾 `/` 不参与匹配。配置加载中、失败或无匹配规则时显示 Order Now，跳转 `https://shop.ff.com/`。目标链接的查询参数和 hash 会原样保留。

SDK 会监听 `pushState`、`replaceState`、前进后退和 hash 变化，更新当前入口文字；该过程使用已缓存的规则，不会重新请求配置。

在 `/admin` 的 **Order Now 配置** 标签中维护规则。使用显式 `hostUrl` 的单页网站应在路由变化后调用 `FFRobotChat.update({ hostUrl: window.location.href })` 更新覆盖值。

默认收起状态下，SDK 只挂载右下角入口，不加载 ChatKit runtime，也不渲染聊天面板主体。用户首次打开面板时才会加载聊天运行时，以降低对宿主页面滚动与触摸事件的影响。

SDK 在浏览器中会自动读取 `window.location.href`，并在请求首页推荐配置时作为 `url` 参数发送给后端，用于按页面返回不同的欢迎语与预置问题。也可以通过 `hostUrl` 手动覆盖：

```html
<script>
  FFRobotChat.init({
    hostUrl: 'https://www.ff.com/fx/super-one'
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
| `FFRobotChat.getVersion()` | 获取 SDK 版本、构建版本与构建时间 |

## 查看版本

控制台可直接调用：

```js
FFRobotChat.getVersion()
```

也可以在聊天面板打开后，连续点击标题 `FF Assist` 5 次查看版本信息。

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
