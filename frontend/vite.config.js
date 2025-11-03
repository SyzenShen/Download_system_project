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
        // 保留 /api 前缀，后端以 /api 开头
        secure: false
      },
      // 仅匹配以 /cellxgene/ 开头的路径，避免误匹配 /cellxgene-app
      '/cellxgene/': {
        target: 'http://localhost:5005',
        changeOrigin: true,
        secure: false,
        ws: true,
        rewrite: (path) => path.replace(/^\/cellxgene\//, '/')
      }
    }
  }
})