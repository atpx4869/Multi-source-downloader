import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        proxyTimeout: 60000,
        timeout: 60000,
      },
      '/downloads': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        proxyTimeout: 60000,
        timeout: 60000,
      }
    }
  }
})
