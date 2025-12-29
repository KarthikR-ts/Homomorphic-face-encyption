import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://app:5000',  // Use Docker service name, not localhost
        changeOrigin: true,
        secure: false,
      }
    }
  }

})
