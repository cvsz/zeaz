import { defineConfig } from "vite"; import react from "@vitejs/plugin-react"; export default defineConfig({base:"/platform/",plugins:[react()],build:{outDir:"dist"}});
