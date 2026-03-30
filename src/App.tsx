import { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { ALL_PRODUCTS } from '@/hooks/useProductContext'
import MarkdownPage from '@/pages/MarkdownPage'
import AdminPage from '@/pages/AdminPage'
import { ChatPanel, type ChatEntityNavigatePayload } from '@/components/chat'

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
  const [isChatOpen, setIsChatOpen] = useState(false)
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

  return (
    <Routes>
      {/* Standalone admin page — no sidebar, no ChatPanel */}
      <Route path="/admin" element={<AdminPage />} />

      {/* All other pages — with sidebar + ChatPanel */}
      <Route
        path="*"
        element={
          <>
            <ManualRoutes />
            <ChatPanel
              open={isChatOpen}
              onOpenChange={setIsChatOpen}
              onEntityNavigate={handleEntityNavigate}
            />
          </>
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
