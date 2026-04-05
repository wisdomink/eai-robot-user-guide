import { renderToString } from 'react-dom/server'
import { MemoryRouter } from 'react-router'
import { AppRoutes } from './App'

export function render(url: string): string {
  return renderToString(
    <MemoryRouter initialEntries={[url]}>
      <AppRoutes />
    </MemoryRouter>
  )
}
