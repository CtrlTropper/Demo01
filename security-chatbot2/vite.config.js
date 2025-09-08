import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // Tinh chỉnh để SSE không bị timeout trên dev proxy
        configure: (proxy) => {
          proxy.on('proxyRes', (proxyRes) => {
            // Tránh nén/biến đổi nội dung SSE
            if (proxyRes.headers['content-type'] === 'text/event-stream') {
              delete proxyRes.headers['content-encoding']
            }
          })
        },
        // forward WebSocket nếu dùng sau này
        ws: true,
        // Không đặt timeout để stream lâu
        timeout: 0,
        proxyTimeout: 0
      },
    },
  },
})
