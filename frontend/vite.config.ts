import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
    // Allow CORS so external files on your desktop can fetch the script
    cors: true,
  },
  build: {
    // This allows you to build the widget loader separately
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        'widget-loader': resolve(__dirname, 'src/utils/widgetLoader.ts'),
      },
      output: {
        entryFileNames: (chunkInfo) => {
          return chunkInfo.name === 'widget-loader' ? '[name].js' : 'assets/[name]-[hash].js';
        },
      },
    },
  },
})