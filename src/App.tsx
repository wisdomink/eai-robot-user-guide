import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { sidebarConfig, futuristSidebarConfig, aegiseduSidebarConfig, aegisSidebarConfig } from '@/content'
import MarkdownPage from '@/pages/MarkdownPage'
import ChatPanel from '@/components/chat/ChatPanel'
import { ProductProvider } from '@/hooks/useProductContext'

const allSidebars = [
  { sidebar: sidebarConfig, homeRoute: '/master-ultra', homeFile: 'master-ultra/home.md', homeTitle: 'FF Master' },
  { sidebar: futuristSidebarConfig, homeRoute: '/futurist-ultra', homeFile: 'futurist-ultra/home.md', homeTitle: 'FF Futurist' },
  { sidebar: aegiseduSidebarConfig, homeRoute: '/aegis-edu', homeFile: 'aegis-edu/home.md', homeTitle: 'FX Aegis EDU' },
  { sidebar: aegisSidebarConfig, homeRoute: '/aegis-ultra', homeFile: 'aegis-ultra/home.md', homeTitle: 'FX Aegis Ultra' },
]

export function AppRoutes() {
  return (
    <Routes>
      {/* Home pages for each product */}
      {allSidebars.map(({ homeRoute, homeFile, homeTitle }) => (
        <Route
          key={homeRoute}
          path={homeRoute}
          element={<MarkdownPage file={homeFile} title={homeTitle} />}
        />
      ))}

      {/* Redirect root to /master-ultra */}
      <Route path="/" element={<Navigate to="/master-ultra" replace />} />

      {/* All content pages from all products */}
      {allSidebars.flatMap(({ sidebar }) =>
        sidebar.sections.flatMap(section =>
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
  return (
    <BrowserRouter>
      <ProductProvider>
        <AppRoutes />
        <ChatPanel />
      </ProductProvider>
    </BrowserRouter>
  )
}
