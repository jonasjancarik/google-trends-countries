import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  base: "./",
  server: {
    host: "0.0.0.0", port: 5173, strictPort: true,
    allowedHosts: ["macbook-air-2.local", "macbook-air-2.adal-macaroni.ts.net"],
  },
  preview: { host: "0.0.0.0", port: 4173 },
});
