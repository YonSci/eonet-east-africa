import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

function silentProxy(target) {
  return {
    target,
    changeOrigin: true,
    configure: (proxy) => { proxy.on('error', () => {}) },
  }
}

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'favicon.svg'],
      manifest: {
        name: 'NET-EA -- Natural Event Tracker for East Africa',
        short_name: 'NET-EA',
        description: 'Near real-time natural hazard monitoring for the Greater Horn of Africa',
        theme_color: '#1D9E75',
        background_color: '#f6f8fa',
        display: 'standalone',
        start_url: process.env.VITE_BASE_PATH || '/',
        scope: process.env.VITE_BASE_PATH || '/',
        icons: [
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png',
            purpose: 'any maskable' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.hostname === 'eonet.gsfc.nasa.gov',
            handler: 'NetworkFirst',
            options: {
              cacheName: 'eonet-api',
              networkTimeoutSeconds: 10,
              expiration: { maxEntries: 10, maxAgeSeconds: 86400 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            urlPattern: ({ url }) => url.hostname.includes('cartocdn.com'),
            handler: 'CacheFirst',
            options: {
              cacheName: 'map-tiles',
              expiration: { maxEntries: 500, maxAgeSeconds: 7 * 86400 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            urlPattern: ({ url }) => url.hostname.includes('gibs.earthdata.nasa.gov'),
            handler: 'NetworkFirst',
            options: {
              cacheName: 'gibs-tiles',
              networkTimeoutSeconds: 8,
              expiration: { maxEntries: 100, maxAgeSeconds: 86400 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
      },
    }),
  ],
  base: process.env.VITE_BASE_PATH || '/',
  server: {
    port: 5173,
    proxy: {
      '/events':  silentProxy('http://localhost:8000'),
      '/summary': silentProxy('http://localhost:8000'),
      '/status':  silentProxy('http://localhost:8000'),
      '/alerts':  silentProxy('http://localhost:8000'),
    },
  },
  build: { outDir: 'dist', sourcemap: false },
})
