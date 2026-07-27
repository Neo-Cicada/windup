#!/usr/bin/env bash
# Fetch the WASI builds the judge executes submitted code inside.
#
# One interpreter per language, all run by the same wasmtime sandbox — fuel caps
# CPU, a store limit caps memory, and no preopened directory means no filesystem.
# They are binary artifacts, so vendor/ is gitignored and this runs once after
# `uv sync`.
#
#   ./scripts/fetch_language_wasm.sh              # every language
#   ./scripts/fetch_language_wasm.sh javascript   # just one
#
# A language whose artifact is missing simply isn't offered: keep JUDGE_LANGUAGES
# to the ones you have fetched.
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p vendor

PY_TAG="python%2F3.11.4%2B20230714-11be424"
PY_BASE="https://github.com/vmware-labs/webassembly-language-runtimes/releases/download"
QJS_BASE="https://github.com/quickjs-ng/quickjs/releases/download/v0.15.1"

# language|destination|url
LANGUAGES=(
  "python|vendor/python.wasm|${PY_BASE}/${PY_TAG}/python-3.11.4.wasm"
  "javascript|vendor/quickjs.wasm|${QJS_BASE}/qjs-wasi.wasm"
)

fetch() {
  local language="$1" dest="$2" url="$3"
  if [ -f "$dest" ]; then
    echo "✓ $language: $dest already present ($(du -h "$dest" | cut -f1))"
    return
  fi
  # Braced because bash reads the following multibyte "…" as part of the name.
  echo "Fetching ${language}…"
  curl -fL --progress-bar -o "$dest.tmp" "$url"
  mv "$dest.tmp" "$dest"
  echo "✓ $language: $dest ($(du -h "$dest" | cut -f1))"
}

wanted="${1:-}"
found=0
for entry in "${LANGUAGES[@]}"; do
  IFS='|' read -r language dest url <<<"$entry"
  if [ -z "$wanted" ] || [ "$wanted" = "$language" ]; then
    fetch "$language" "$dest" "$url"
    found=1
  fi
done

if [ "$found" = "0" ]; then
  echo "No such language: $wanted" >&2
  printf 'Known:' >&2
  for entry in "${LANGUAGES[@]}"; do printf ' %s' "${entry%%|*}" >&2; done
  echo >&2
  exit 1
fi
