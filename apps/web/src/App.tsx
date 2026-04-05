import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ALL_PRODUCTS } from '@/hooks/useProductContext'
import MarkdownPage from '@/pages/MarkdownPage'
import AdminPage from '@/pages/AdminPage'
import ChatPanelSdkBridge from '@/components/chat/ChatPanelSdkBridge'

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

      <Route path="/" element={<Navigate to="/futurist" replace />} />

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

      <Route path="*" element={<Navigate to="/futurist" replace />} />
    </Routes>
  )
}

export function AppRoutes() {
  return (
    <>
      <ChatPanelSdkBridge />
      <Routes>
        {/* Standalone admin page — no sidebar, no ChatPanel */}
        <Route path="/admin" element={<AdminPage />} />

        {/* All other pages — with sidebar; ChatPanel now mounts through the SDK bridge */}
        <Route path="*" element={<ManualRoutes />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}
