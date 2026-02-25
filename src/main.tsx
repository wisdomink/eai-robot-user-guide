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

// If the root has pre-rendered content (SSG), hydrate; otherwise create fresh
if (root.innerHTML.trim()) {
  hydrateRoot(root, app)
} else {
  createRoot(root).render(app)
}
