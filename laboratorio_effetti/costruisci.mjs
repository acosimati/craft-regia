// Costruisce la pagina statica del gradiente: effetti/gradiente/dist/{index.html,app.js}. Uso: npm run build
import { build } from "esbuild";
import { copyFileSync, mkdirSync } from "node:fs";
mkdirSync("effetti/gradiente/dist", { recursive: true });
await build({
  entryPoints: ["effetti/gradiente/src/main.jsx"], bundle: true, format: "iife", minify: true,
  outfile: "effetti/gradiente/dist/app.js", jsx: "automatic", define: { "process.env.NODE_ENV": '"production"' },
  legalComments: "eof", logLevel: "info",
});
copyFileSync("effetti/gradiente/index.html", "effetti/gradiente/dist/index.html");
