import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import basicSsl from '@vitejs/plugin-basic-ssl'

export default defineConfig({
  define: {
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
  },
  plugins: [react(), tailwindcss(), basicSsl()],
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  server: {
    host: '0.0.0.0',
    watch: {
      ignored: ['**/rag_server/**', '**/node_modules/**', '**/.git/**'],
    },
    proxy: {
      '/api/search': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/search/, '/search'),
      },
      '/chatkit': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/api/chat-mode': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/api/chat-history': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/api/logs': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/reindex': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/api/embed': {
        target: 'http://localhost:3001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/search/, '/search'),
      },
    },
  },
})
