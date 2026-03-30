# ChatPanel 使用说明

`ChatPanel` 现在是一个相对独立的聊天组件，已经去掉了对项目内 `ChatContext` 和 `react-router` 的硬依赖，方便迁移到别的页面或项目中复用。

## 目录结构

```text
src/components/chat/
  ChatPanel.tsx
  chat-panel.css
  index.ts
  README.md
```

## 组件特性

- 支持受控和非受控两种打开方式
- 默认自带浮动按钮（FAB）
- 支持自定义标题、占位文案、欢迎语和快捷提问
- 页面跳转通过 `onEntityNavigate` 回调交给外层页面处理
- 样式收敛在组件目录下，迁移时更容易一起复制

## 依赖

- `@openai/chatkit-react`
- `clsx`
- 全局 CSS 变量：
  - `--bg`
  - `--border`
  - `--accent`
  - `--accent-bg`
  - `--text`
  - `--font-rubik`
  - `--font-roboto`

如果迁移到其它项目，需要确保这些 CSS 变量存在，或者按需改写 `chat-panel.css`。

## 环境变量

默认情况下，组件会读取以下环境变量来构造 ChatKit API 配置：

- `VITE_CHATKIT_API_URL`
- `VITE_CHATKIT_DOMAIN_KEY`

如果你不想依赖环境变量，也可以直接通过 `apiConfig` 传入：

```tsx
<ChatPanel
  apiConfig={{
    url: 'https://example.com/api/chatkit',
    domainKey: 'your-domain-key',
  }}
/>
```

## 最简单用法

非受控模式下，组件自己管理打开/关闭状态：

```tsx
import { ChatPanel } from '@/components/chat'

export default function DemoPage() {
  return <ChatPanel />
}
```

## 受控用法

如果页面自己管理开关状态，可以使用受控模式：

```tsx
import { useState } from 'react'
import { ChatPanel } from '@/components/chat'

export default function DemoPage() {
  const [open, setOpen] = useState(false)

  return (
    <ChatPanel
      open={open}
      onOpenChange={setOpen}
    />
  )
}
```

## 页面跳转回调

如果 ChatKit 返回的实体里带有 `slug`，组件会触发 `onEntityNavigate`。这样页面跳转逻辑就由外层页面自己实现：

```tsx
import { useNavigate } from 'react-router-dom'
import { ChatPanel, type ChatEntityNavigatePayload } from '@/components/chat'

export default function DemoPage() {
  const navigate = useNavigate()

  const handleEntityNavigate = ({ url }: ChatEntityNavigatePayload) => {
    navigate(`${url.pathname}${url.search}`)

    if (url.hash) {
      setTimeout(() => {
        document.getElementById(url.hash.slice(1))
          ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 300)
    }
  }

  return <ChatPanel onEntityNavigate={handleEntityNavigate} />
}
```

## 常用 Props

- `open`: 受控打开状态
- `defaultOpen`: 非受控默认打开状态
- `onOpenChange`: 打开状态变化回调
- `onEntityNavigate`: 实体点击后的页面跳转回调
- `apiConfig`: 覆盖默认 ChatKit API 配置
- `title`: 头部标题
- `placeholder`: 输入框占位文案
- `greeting`: 欢迎语
- `prompts`: 首页快捷提问列表
- `fabLabel`: 浮动按钮文案
- `fabAriaLabel`: 浮动按钮无障碍文案
- `showFab`: 是否显示浮动按钮
- `buildVersion`: 底部版本号文案
- `panelId`: 面板 DOM id
- `className`: 面板额外类名

## 迁移建议

迁移到其它项目时，建议至少一起带走下面这些内容：

- `src/components/chat/ChatPanel.tsx`
- `src/components/chat/chat-panel.css`
- `src/components/chat/index.ts`

同时检查以下事项：

- 目标项目是否已安装 `@openai/chatkit-react` 和 `clsx`
- 目标项目是否提供了 ChatKit 所需接口
- 目标项目是否已有对应的全局 CSS 变量
- 如果要支持页面跳转，是否已实现 `onEntityNavigate`
