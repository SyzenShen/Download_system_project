import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // Keep the /api prefix intact; the backend is mounted there
        secure: false
      },
      // Only proxy /cellxgene/* to avoid intercepting /cellxgene-app
      '/cellxgene/': {
        target: 'http://localhost:5005',
        changeOrigin: true,
        secure: false,
        ws: true,
        rewrite: (path) => path.replace(/^\/cellxgene\//, '/')
      },
      '/cellxgene': {
        target: 'http://localhost:5005',
        changeOrigin: true,
        secure: false,
        ws: true,
        rewrite: (path) => path.replace(/^\/cellxgene/, '/')
      },
      // Cellxgene also fetches static assets/API calls that must be proxied to 5005
      '/static/': {
        target: 'http://localhost:5005',
        changeOrigin: true,
        secure: false
      },
      '/api/v0.2/': {
        target: 'http://localhost:5005',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
