import { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ALL_PRODUCTS } from '@/hooks/useProductContext'
import MarkdownPage from '@/pages/MarkdownPage'
import AdminPage from '@/pages/AdminPage'
import ChatPanel from '@/components/chat/ChatPanel'
import { ChatContext } from '@/hooks/useChatState'

const isDesktop = () =>
  typeof window !== 'undefined' && window.innerWidth >= 1024

function ManualRoutes() {
  return (
    <Routes>
      {ALL_PRODUCTS.map(product => (
        <Route
          key={product.homeRoute}
          path={product.homeRoute}
          element={<MarkdownPage file={product.homeFile} title={product.label} />}
        />
      ))}

      <Route path="/" element={<Navigate to="/master-ultra" replace />} />

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

      <Route path="*" element={<Navigate to="/master-ultra" replace />} />
    </Routes>
  )
}

export function AppRoutes() {
  const [isChatOpen, setIsChatOpen] = useState(isDesktop)
  const toggleChat = () => setIsChatOpen(prev => !prev)

  return (
    <Routes>
      {/* Standalone admin page — no sidebar, no ChatPanel */}
      <Route path="/admin" element={<AdminPage />} />

      {/* All other pages — with sidebar + ChatPanel */}
      <Route
        path="*"
        element={
          <ChatContext.Provider value={{ isChatOpen, toggleChat }}>
            <ManualRoutes />
            <ChatPanel />
          </ChatContext.Provider>
        }
      />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}
