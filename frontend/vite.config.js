// File Name: vite.config.js
// Description: Vite configuration for SmartLMS frontend.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-11-14
// Updated By: AI Agent

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // `vite preview` serves production behind nginx/Cloudflare Tunnel, so the Host header is
  // the public domain. Without this Vite returns "Blocked request. This host is not allowed".
  // ponytail: allows any host; the app is only reachable through the tunnel. Pin to a domain list if exposed directly.
  preview: {
    allowedHosts: true,
  },
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
