import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import basicSsl from '@vitejs/plugin-basic-ssl'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig(() => {
  const sharedConfig = {
    define: {
      __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
      'process.env.NODE_ENV': JSON.stringify('production'),
      'process.env': JSON.stringify({ NODE_ENV: 'production' }),
      global: 'globalThis',
    },
    plugins: [react(), tailwindcss(), basicSsl()],
    resolve: {
      alias: [
        { find: '@', replacement: path.resolve(__dirname, 'src') },
      ],
    },
  }

  return {
    ...sharedConfig,
    server: {
      host: '0.0.0.0',
      watch: {
        ignored: ['**/apps/rag-api/**', '**/tools/eval/**', '**/node_modules/**', '**/.git/**'],
      },
      proxy: {
        '/api/search': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/api/chatkit': {
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
        '/api/post-lead': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/api/get-leads': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/api/get-lead-capture-config': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/api/save-lead-capture-config': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/api/get-manual-download-config': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/api/save-manual-download-config': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/api/get-recommendations': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/api/save-recommendation': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/api/delete-recommendation': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/api/get-homepage-prompts': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/api/save-homepage-global-prompts': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/api/save-homepage-prompt': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/api/save-homepage-settings': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/api/delete-homepage-prompt': {
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
  }
})
