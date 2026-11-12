import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The FastAPI backend runs on port 8000. Proxying /api and /images means the
// browser only ever talks to one address (http://127.0.0.1:5173).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/images": "http://127.0.0.1:8000",
    },
  },
});
