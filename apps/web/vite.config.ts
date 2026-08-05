import {resolve} from "node:path";
import {defineConfig} from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "/platform/",
  plugins: [react()],
  build: {
    outDir: "dist",
    rollupOptions: {
      input: {
        ai: resolve(__dirname, "ai.html"),
        admin: resolve(__dirname, "admin.html"),
        apiMonitor: resolve(__dirname, "api-monitor.html"),
        dashboard: resolve(__dirname, "dashboard.html"),
        documentAdmin: resolve(__dirname, "document-admin.html"),
        documents: resolve(__dirname, "documents.html"),
        main: resolve(__dirname, "index.html"),
        menuPreview: resolve(__dirname, "menu-preview.html"),
        merchantRegister: resolve(__dirname, "merchant-register.html"),
        ops: resolve(__dirname, "ops.html"),
        riderRegister: resolve(__dirname, "rider-register.html"),
        salesDemo: resolve(__dirname, "sales-demo.html"),
      },
    },
  },
});
