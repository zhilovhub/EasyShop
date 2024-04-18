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
  build: {
    rollupOptions: {
      external: ['swiper', 'swiper/vue', 'swiper/swiper-bundle.min.css', 'swiper/swiper.min.css', 'swiper/modules']
    }
  }
})
