import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // Vendored Pyodide runtime, copied in by scripts/copy-pyodide.mjs. It is a
    // minified emscripten bundle — linting it produces thousands of findings
    // about code we neither wrote nor can fix. Our own worker beside it,
    // runner.worker.js, is deliberately not ignored.
    "public/pyodide/pyodide*",
  ]),
]);

export default eslintConfig;
