// vite.config.js
import { fileURLToPath, URL } from "node:url";
import { defineConfig, loadEnv } from "file:///D:/EasyShop/EasyShop/webapp/frontend/node_modules/vite/dist/node/index.js";
import vue from "file:///D:/EasyShop/EasyShop/webapp/frontend/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import vueJsx from "file:///D:/EasyShop/EasyShop/webapp/frontend/node_modules/@vitejs/plugin-vue-jsx/dist/index.mjs";
import fs from "fs";
var __vite_injected_original_import_meta_url = "file:///D:/EasyShop/EasyShop/webapp/frontend/vite.config.js";
var env = loadEnv(
  "all",
  process.cwd()
);
var vite_config_default = defineConfig({
  modules: [
    "virtual",
    "keyboard",
    "mousewheel",
    "navigation",
    "pagination",
    "scrollbar",
    "parallax",
    "zoom",
    "controller",
    "a11y",
    "history",
    "hash-navigation",
    "autoplay",
    "thumbs",
    "free-mode",
    "grid",
    "manipulation",
    "effect-fade",
    "effect-cube",
    "effect-flip",
    "effect-coverflow",
    "effect-creative",
    "effect-cards"
  ],
  build: {
    transpile: ["swiper"]
  },
  plugins: [
    vue(),
    vueJsx()
  ],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", __vite_injected_original_import_meta_url)),
      "@SwiperBundle": fileURLToPath(new URL("./node_modules/swiper/swiper-bundle.esm.js", __vite_injected_original_import_meta_url)),
      "@SwiperBundleCss": fileURLToPath(new URL("./node_modules/swiper/swiper-bundle.min.css", __vite_injected_original_import_meta_url)),
      "@Swiper": fileURLToPath(new URL("./node_modules/swiper/swiper.esm.js", __vite_injected_original_import_meta_url)),
      "@SwiperVue": fileURLToPath(new URL("./node_modules/swiper/vue/swiper-vue.js", __vite_injected_original_import_meta_url))
    }
  },
  server: {
    https: {
      key: fs.readFileSync(env.VITE_SSL_KEY_PATH),
      cert: fs.readFileSync(env.VITE_SSL_CERT_PATH)
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuanMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJEOlxcXFxFYXN5U2hvcFxcXFxFYXN5U2hvcFxcXFx3ZWJhcHBcXFxcZnJvbnRlbmRcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIkQ6XFxcXEVhc3lTaG9wXFxcXEVhc3lTaG9wXFxcXHdlYmFwcFxcXFxmcm9udGVuZFxcXFx2aXRlLmNvbmZpZy5qc1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vRDovRWFzeVNob3AvRWFzeVNob3Avd2ViYXBwL2Zyb250ZW5kL3ZpdGUuY29uZmlnLmpzXCI7aW1wb3J0IHsgZmlsZVVSTFRvUGF0aCwgVVJMIH0gZnJvbSAnbm9kZTp1cmwnXHJcbmltcG9ydCB7IGRlZmluZUNvbmZpZywgbG9hZEVudiB9IGZyb20gJ3ZpdGUnXHJcbmltcG9ydCB2dWUgZnJvbSAnQHZpdGVqcy9wbHVnaW4tdnVlJ1xyXG5pbXBvcnQgdnVlSnN4IGZyb20gJ0B2aXRlanMvcGx1Z2luLXZ1ZS1qc3gnXHJcbmltcG9ydCBmcyBmcm9tICdmcyc7XHJcbmltcG9ydCBwYXRoIGZyb20gJ3BhdGgnXHJcblxyXG5jb25zdCBlbnYgPSBsb2FkRW52KFxyXG4gICdhbGwnLFxyXG4gIHByb2Nlc3MuY3dkKClcclxuKTtcclxuXHJcbi8vIGh0dHBzOi8vdml0ZWpzLmRldi9jb25maWcvXHJcbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZyh7XHJcbiAgbW9kdWxlczogW1xyXG4gICAgJ3ZpcnR1YWwnLFxyXG4gICAgJ2tleWJvYXJkJyxcclxuICAgICdtb3VzZXdoZWVsJyxcclxuICAgICduYXZpZ2F0aW9uJyxcclxuICAgICdwYWdpbmF0aW9uJyxcclxuICAgICdzY3JvbGxiYXInLFxyXG4gICAgJ3BhcmFsbGF4JyxcclxuICAgICd6b29tJyxcclxuICAgICdjb250cm9sbGVyJyxcclxuICAgICdhMTF5JyxcclxuICAgICdoaXN0b3J5JyxcclxuICAgICdoYXNoLW5hdmlnYXRpb24nLFxyXG4gICAgJ2F1dG9wbGF5JyxcclxuICAgICd0aHVtYnMnLFxyXG4gICAgJ2ZyZWUtbW9kZScsXHJcbiAgICAnZ3JpZCcsXHJcbiAgICAnbWFuaXB1bGF0aW9uJyxcclxuICAgICdlZmZlY3QtZmFkZScsXHJcbiAgICAnZWZmZWN0LWN1YmUnLFxyXG4gICAgJ2VmZmVjdC1mbGlwJyxcclxuICAgICdlZmZlY3QtY292ZXJmbG93JyxcclxuICAgICdlZmZlY3QtY3JlYXRpdmUnLFxyXG4gICAgJ2VmZmVjdC1jYXJkcycsXHJcbiAgXSxcclxuICBidWlsZDoge1xyXG4gICAgdHJhbnNwaWxlOiBbJ3N3aXBlciddXHJcbiAgfSxcclxuICBwbHVnaW5zOiBbXHJcbiAgICB2dWUoKSxcclxuICAgIHZ1ZUpzeCgpLFxyXG4gIF0sXHJcbiAgcmVzb2x2ZToge1xyXG4gICAgYWxpYXM6IHtcclxuICAgICAgJ0AnOiBmaWxlVVJMVG9QYXRoKG5ldyBVUkwoJy4vc3JjJywgaW1wb3J0Lm1ldGEudXJsKSksXHJcbiAgICAgIFwiQFN3aXBlckJ1bmRsZVwiOiBmaWxlVVJMVG9QYXRoKG5ldyBVUkwoJy4vbm9kZV9tb2R1bGVzL3N3aXBlci9zd2lwZXItYnVuZGxlLmVzbS5qcycsIGltcG9ydC5tZXRhLnVybCkpLFxyXG4gICAgICBcIkBTd2lwZXJCdW5kbGVDc3NcIjogZmlsZVVSTFRvUGF0aChuZXcgVVJMKCcuL25vZGVfbW9kdWxlcy9zd2lwZXIvc3dpcGVyLWJ1bmRsZS5taW4uY3NzJywgaW1wb3J0Lm1ldGEudXJsKSksXHJcbiAgICAgIFwiQFN3aXBlclwiOiBmaWxlVVJMVG9QYXRoKG5ldyBVUkwoJy4vbm9kZV9tb2R1bGVzL3N3aXBlci9zd2lwZXIuZXNtLmpzJywgaW1wb3J0Lm1ldGEudXJsKSksXHJcbiAgICAgIFwiQFN3aXBlclZ1ZVwiOiBmaWxlVVJMVG9QYXRoKG5ldyBVUkwoJy4vbm9kZV9tb2R1bGVzL3N3aXBlci92dWUvc3dpcGVyLXZ1ZS5qcycsIGltcG9ydC5tZXRhLnVybCkpLFxyXG4gICAgfVxyXG4gIH0sXHJcbiAgc2VydmVyOiB7XHJcbiAgICBodHRwczoge1xyXG4gICAgICBrZXk6IGZzLnJlYWRGaWxlU3luYyhlbnYuVklURV9TU0xfS0VZX1BBVEgpLFxyXG4gICAgICBjZXJ0OiBmcy5yZWFkRmlsZVN5bmMoZW52LlZJVEVfU1NMX0NFUlRfUEFUSClcclxuICAgIH1cclxuICB9LFxyXG59KSJdLAogICJtYXBwaW5ncyI6ICI7QUFBd1MsU0FBUyxlQUFlLFdBQVc7QUFDM1UsU0FBUyxjQUFjLGVBQWU7QUFDdEMsT0FBTyxTQUFTO0FBQ2hCLE9BQU8sWUFBWTtBQUNuQixPQUFPLFFBQVE7QUFKMEssSUFBTSwyQ0FBMkM7QUFPMU8sSUFBTSxNQUFNO0FBQUEsRUFDVjtBQUFBLEVBQ0EsUUFBUSxJQUFJO0FBQ2Q7QUFHQSxJQUFPLHNCQUFRLGFBQWE7QUFBQSxFQUMxQixTQUFTO0FBQUEsSUFDUDtBQUFBLElBQ0E7QUFBQSxJQUNBO0FBQUEsSUFDQTtBQUFBLElBQ0E7QUFBQSxJQUNBO0FBQUEsSUFDQTtBQUFBLElBQ0E7QUFBQSxJQUNBO0FBQUEsSUFDQTtBQUFBLElBQ0E7QUFBQSxJQUNBO0FBQUEsSUFDQTtBQUFBLElBQ0E7QUFBQSxJQUNBO0FBQUEsSUFDQTtBQUFBLElBQ0E7QUFBQSxJQUNBO0FBQUEsSUFDQTtBQUFBLElBQ0E7QUFBQSxJQUNBO0FBQUEsSUFDQTtBQUFBLElBQ0E7QUFBQSxFQUNGO0FBQUEsRUFDQSxPQUFPO0FBQUEsSUFDTCxXQUFXLENBQUMsUUFBUTtBQUFBLEVBQ3RCO0FBQUEsRUFDQSxTQUFTO0FBQUEsSUFDUCxJQUFJO0FBQUEsSUFDSixPQUFPO0FBQUEsRUFDVDtBQUFBLEVBQ0EsU0FBUztBQUFBLElBQ1AsT0FBTztBQUFBLE1BQ0wsS0FBSyxjQUFjLElBQUksSUFBSSxTQUFTLHdDQUFlLENBQUM7QUFBQSxNQUNwRCxpQkFBaUIsY0FBYyxJQUFJLElBQUksOENBQThDLHdDQUFlLENBQUM7QUFBQSxNQUNyRyxvQkFBb0IsY0FBYyxJQUFJLElBQUksK0NBQStDLHdDQUFlLENBQUM7QUFBQSxNQUN6RyxXQUFXLGNBQWMsSUFBSSxJQUFJLHVDQUF1Qyx3Q0FBZSxDQUFDO0FBQUEsTUFDeEYsY0FBYyxjQUFjLElBQUksSUFBSSwyQ0FBMkMsd0NBQWUsQ0FBQztBQUFBLElBQ2pHO0FBQUEsRUFDRjtBQUFBLEVBQ0EsUUFBUTtBQUFBLElBQ04sT0FBTztBQUFBLE1BQ0wsS0FBSyxHQUFHLGFBQWEsSUFBSSxpQkFBaUI7QUFBQSxNQUMxQyxNQUFNLEdBQUcsYUFBYSxJQUFJLGtCQUFrQjtBQUFBLElBQzlDO0FBQUEsRUFDRjtBQUNGLENBQUM7IiwKICAibmFtZXMiOiBbXQp9Cg==
