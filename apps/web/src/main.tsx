import { StrictMode } from 'react'
import { hydrateRoot, createRoot } from 'react-dom/client'
import './index.css'
import App from './App'

const root = document.getElementById('root')!
const app = (
  <StrictMode>
    <App />
  </StrictMode>
)

const hasSSRContent = root.innerHTML.replace(/<!--.*?-->/g, '').trim().length > 0

if (hasSSRContent) {
  hydrateRoot(root, app)
} else {
  createRoot(root).render(app)
}
