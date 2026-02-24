import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { sidebarConfig } from '@/content'
import HomePage from '@/pages/HomePage'
import MarkdownPage from '@/pages/MarkdownPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        {sidebarConfig.sections.flatMap(section =>
          section.pages.map(page => (
            <Route
              key={page.slug}
              path={page.slug}
              element={<MarkdownPage file={page.file} title={page.title} />}
            />
          ))
        )}
        <Route path="*" element={<HomePage />} />
      </Routes>
    </BrowserRouter>
  )
}
