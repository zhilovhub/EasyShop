import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import fs from 'fs';

const env = loadEnv(
  'all',
  process.cwd()
);

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueJsx(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    https: {
      key: fs.readFileSync(env.VITE_SSL_KEY_PATH),
      cert: fs.readFileSync(env.VITE_SSL_CERT_PATH)
    }
  },
  modules: [
    'virtual',
    'keyboard',
    'navigation',
    'pagination',
    'scrollbar',
    'parallax',
    'zoom',
    'controller',
    'a11y',
    'history',
    'hash-navigation',
    'autoplay',
    'effect-fade',
    'effect-cube',
    'effect-flip',
    'effect-coverflow',
    'effect-creative',
    'effect-cards',
  ],
})