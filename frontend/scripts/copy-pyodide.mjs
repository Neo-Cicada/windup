/**
 * Copy the Pyodide runtime into public/pyodide/ so the browser "Run" button can
 * execute Python locally.
 *
 * Self-hosted rather than loaded from a CDN: it keeps the academy working
 * offline, and it means the page makes no third-party requests, which is what
 * lets a strict connect-src content-security-policy stay strict.
 *
 * ~11MB of assets, so public/pyodide/ is gitignored and this runs from
 * `npm install` (postinstall) or by hand: `node scripts/copy-pyodide.mjs`.
 */
import { cp, mkdir, stat } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const from = join(root, "node_modules", "pyodide");
const to = join(root, "public", "pyodide");

// Only the core runtime — not the bundled scientific packages, which the
// academy never touches.
const FILES = [
  "pyodide.mjs",
  "pyodide.asm.mjs",
  "pyodide.asm.wasm",
  "python_stdlib.zip",
  "pyodide-lock.json",
];

try {
  await stat(from);
} catch {
  console.error("pyodide is not installed — run `npm install` first.");
  process.exit(1);
}

await mkdir(to, { recursive: true });
let total = 0;
for (const file of FILES) {
  await cp(join(from, file), join(to, file));
  total += (await stat(join(to, file))).size;
}
console.log(`✓ pyodide runtime -> public/pyodide (${(total / 1e6).toFixed(1)} MB)`);
