import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

function silentProxy(target) {
  return {
    target,
    changeOrigin: true,
    configure: (proxy) => {
      proxy.on('error', () => {})
    },
  }
}

export default defineConfig({
  plugins: [react()],
  base: '/',
  server: {
    port: 5173,
    proxy: {
      '/events':  silentProxy('http://localhost:8000'),
      '/summary': silentProxy('http://localhost:8000'),
      '/status':  silentProxy('http://localhost:8000'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
