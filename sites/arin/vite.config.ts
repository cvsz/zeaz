import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8787',
      '/preview': 'http://127.0.0.1:8787',
      '/app': 'http://127.0.0.1:8787',
    },
  },
})
