import { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ALL_PRODUCTS } from '@/hooks/useProductContext'
import MarkdownPage from '@/pages/MarkdownPage'
import ChatPanel from '@/components/chat/ChatPanel'
import { ChatContext } from '@/hooks/useChatState'

const isDesktop = () => window.innerWidth >= 1024

export function AppRoutes() {
  return (
    <Routes>
      {/* Home pages for each product */}
      {ALL_PRODUCTS.map(product => (
        <Route
          key={product.homeRoute}
          path={product.homeRoute}
          element={<MarkdownPage file={product.homeFile} title={product.label} />}
        />
      ))}

      {/* Redirect root to /master-ultra */}
      <Route path="/" element={<Navigate to="/master-ultra" replace />} />

      {/* All content pages from all products */}
      {ALL_PRODUCTS.flatMap(product =>
        product.sidebar.sections.flatMap(section =>
          section.pages.map(page => (
            <Route
              key={page.slug}
              path={page.slug}
              element={<MarkdownPage file={page.file} title={page.title} />}
            />
          ))
        )
      )}

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/master-ultra" replace />} />
    </Routes>
  )
}

export default function App() {
  const [isChatOpen, setIsChatOpen] = useState(isDesktop)
  const toggleChat = () => setIsChatOpen(prev => !prev)

  return (
    <BrowserRouter>
      <ChatContext.Provider value={{ isChatOpen, toggleChat }}>
        <AppRoutes />
        <ChatPanel />
      </ChatContext.Provider>
    </BrowserRouter>
  )
}
