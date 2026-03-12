import { createContext, useContext } from 'react'

interface ChatState {
  isChatOpen: boolean
  toggleChat: () => void
}

export const ChatContext = createContext<ChatState>({
  isChatOpen: false,
  toggleChat: () => {},
})

export const useChatState = () => useContext(ChatContext)
