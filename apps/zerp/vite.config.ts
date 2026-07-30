import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3001,
  },
  preview: {
    host: "127.0.0.1",
    port: 3001,
    allowedHosts: ["zerp.zeaz.dev"],
  },
});
