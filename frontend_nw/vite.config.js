import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv, searchForWorkspaceRoot } from 'vite'
import process from 'node:process'
import { fileURLToPath } from 'node:url'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const proxy = {
    '/api': {
      target: env.BACKEND_URL || 'http://127.0.0.1:5000',
      changeOrigin: true,
      rewrite: path => path.replace(/^\/api/, ''),
    },
  }
  return {
    plugins: [react()],
    server: { port: 5173, strictPort: true, proxy, fs: { allow: [searchForWorkspaceRoot(process.cwd()), fileURLToPath(new URL('../shared', import.meta.url))] } },
    preview: { port: 4173, strictPort: true, proxy },
  }
})
