// File Name: vite.config.js
// Description: Vite configuration for SmartLMS frontend.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-08-30
// Updated By: Tam Khang

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0',
    watch: {
      usePolling: true,
    },
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
});
