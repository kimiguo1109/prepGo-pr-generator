import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 28020,
    host: '0.0.0.0',
    cors: true,  // Enable CORS for all origins
    proxy: {
      '/api': {
        target: 'http://44.236.240.72:28021',
        changeOrigin: true,
        configure: (proxy) => {
          // Handle CORS preflight
          proxy.on('proxyReq', (proxyReq, req, res) => {
            const origin = req.headers.origin;
            if (origin) {
              res.setHeader('Access-Control-Allow-Origin', origin);
              res.setHeader('Access-Control-Allow-Credentials', 'true');
            }
          });
          proxy.on('proxyRes', (proxyRes, req) => {
            const origin = req.headers.origin;
            if (origin) {
              proxyRes.headers['access-control-allow-origin'] = origin;
              proxyRes.headers['access-control-allow-credentials'] = 'true';
            }
          });
        },
      },
    },
  },
})

