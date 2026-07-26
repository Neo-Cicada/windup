#!/usr/bin/env bash
# Fetch the CPython-WASI build the judge executes submitted code inside.
#
# It's a 20MB binary artifact, so it is not committed — run this once after
# `uv sync`, or set JUDGE_RUNNER=subprocess to skip it entirely.
set -euo pipefail

VERSION="3.11.4"
TAG="python%2F3.11.4%2B20230714-11be424"
URL="https://github.com/vmware-labs/webassembly-language-runtimes/releases/download/${TAG}/python-${VERSION}.wasm"

cd "$(dirname "$0")/.."
mkdir -p vendor
DEST="vendor/python.wasm"

if [ -f "$DEST" ]; then
  echo "✓ $DEST already present ($(du -h "$DEST" | cut -f1))"
  exit 0
fi

echo "Fetching CPython ${VERSION} for WASI…"
curl -fL --progress-bar -o "$DEST.tmp" "$URL"
mv "$DEST.tmp" "$DEST"
echo "✓ $DEST ($(du -h "$DEST" | cut -f1))"
