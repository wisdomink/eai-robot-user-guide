import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { sidebarConfig } from '@/content'
import MarkdownPage from '@/pages/MarkdownPage'
import ChatPanel from '@/components/chat/ChatPanel'

export function AppRoutes() {
  const firstPageSlug = sidebarConfig.sections[0]?.pages[0]?.slug || '/'

  return (
    <Routes>
      {/* Cover / Home page — same unified layout */}
      <Route
        path="/"
        element={
          <MarkdownPage
            file="home.md"
            title="FF Master Ultra Edition"
          />
        }
      />

      {/* All content pages */}
      {sidebarConfig.sections.flatMap(section =>
        section.pages.map(page => (
          <Route
            key={page.slug}
            path={page.slug}
            element={<MarkdownPage file={page.file} title={page.title} />}
          />
        ))
      )}

      {/* Fallback */}
      <Route path="*" element={<Navigate to={firstPageSlug} replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
      <ChatPanel />
    </BrowserRouter>
  )
}
