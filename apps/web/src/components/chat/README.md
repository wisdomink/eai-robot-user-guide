# ChatPanel 集成说明

聊天面板由 `packages/chat-sdk` 提供，通过 `<script>` 标签加载 IIFE 脚本，使用 `window.FFRobotChat` 全局 API。

本目录仅保留 `ChatPanelSdkBridge.tsx`，用于在主站中对接 React Router 导航。

详见 [`packages/chat-sdk/README.md`](../../../../packages/chat-sdk/README.md)。
