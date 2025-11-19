import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const apiBase = process.env.VITE_API_BASE || 'http://localhost:38089'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 35073,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: apiBase,
        changeOrigin: true,
      },
    },
  },
})
