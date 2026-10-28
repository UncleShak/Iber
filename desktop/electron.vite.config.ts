import { resolve } from 'path'
import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import type { Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const DEV_CSP =
  "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; " +
  "img-src 'self' data:; connect-src 'self' ws://localhost:* http://localhost:*"

// Dev only: Vite needs an inline preamble + HMR websocket. Packaged build keeps the strict CSP.
const devCsp = (): Plugin => ({
  name: 'ag-dev-csp',
  apply: 'serve',
  transformIndexHtml: {
    order: 'post',
    handler: (html) =>
      html.replace(
        /(<meta http-equiv="Content-Security-Policy" content=")[^"]*(")/,
        `$1${DEV_CSP}$2`
      )
  }
})

export default defineConfig({
  main: { plugins: [externalizeDepsPlugin()] },
  preload: { plugins: [externalizeDepsPlugin()] },
  renderer: {
    resolve: { alias: { '@': resolve(__dirname, 'src/renderer/src') } },
    plugins: [react(), tailwindcss(), devCsp()]
  }
})