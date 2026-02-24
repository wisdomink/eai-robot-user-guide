import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { sidebarConfig } from '@/content'
import MarkdownPage from '@/pages/MarkdownPage'

export default function App() {
  const firstPageSlug = sidebarConfig.sections[0]?.pages[0]?.slug || '/'

  return (
    <BrowserRouter>
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
    </BrowserRouter>
  )
}
