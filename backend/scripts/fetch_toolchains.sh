#!/usr/bin/env bash
# Fetch the compilers the judge needs for C++, Rust and Go.
#
# Unlike the interpreted languages, these have no runtime to download — they
# have a *toolchain*, which runs on the host and produces a wasm module that
# then executes in the same wasmtime sandbox as everything else.
#
#   ./scripts/fetch_toolchains.sh              # everything missing
#   ./scripts/fetch_toolchains.sh cpp          # just one
#
# A language whose toolchain isn't here simply isn't offered — keep
# JUDGE_LANGUAGES to the ones a host can actually build. Only worker hosts need
# these; the API never compiles anything.
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p vendor

WASI_SDK_VERSION="33"
WASI_SDK_RELEASE="33.0"
TINYGO_VERSION="0.41.1"

case "$(uname -m)" in
  arm64|aarch64) ARCH="arm64" ;;
  x86_64) ARCH="x86_64" ;;
  *) echo "Unsupported architecture: $(uname -m)" >&2; exit 1 ;;
esac
case "$(uname -s)" in
  Darwin) OS="macos"; TINYGO_OS="darwin" ;;
  Linux) OS="linux"; TINYGO_OS="linux" ;;
  *) echo "Unsupported OS: $(uname -s)" >&2; exit 1 ;;
esac
# TinyGo spells the same architecture differently.
TINYGO_ARCH="$ARCH"
[ "$ARCH" = "x86_64" ] && TINYGO_ARCH="amd64"

fetch_cpp() {
  if [ -x vendor/wasi-sdk/bin/clang++ ]; then
    echo "✓ cpp: vendor/wasi-sdk already present"
    return
  fi
  local url="https://github.com/WebAssembly/wasi-sdk/releases/download"
  url="${url}/wasi-sdk-${WASI_SDK_VERSION}/wasi-sdk-${WASI_SDK_RELEASE}-${ARCH}-${OS}.tar.gz"
  echo "Fetching wasi-sdk ${WASI_SDK_RELEASE} (~180MB)…"
  curl -fL --progress-bar -o vendor/wasi-sdk.tar.gz "$url"
  tar xzf vendor/wasi-sdk.tar.gz -C vendor
  mv "vendor/wasi-sdk-${WASI_SDK_RELEASE}-${ARCH}-${OS}" vendor/wasi-sdk
  rm vendor/wasi-sdk.tar.gz
  echo "✓ cpp: vendor/wasi-sdk"
}

fetch_go() {
  if [ -x vendor/tinygo/bin/tinygo ]; then
    echo "✓ go: vendor/tinygo already present"
    return
  fi
  local url="https://github.com/tinygo-org/tinygo/releases/download"
  url="${url}/v${TINYGO_VERSION}/tinygo${TINYGO_VERSION}.${TINYGO_OS}-${TINYGO_ARCH}.tar.gz"
  echo "Fetching TinyGo ${TINYGO_VERSION} (~155MB)…"
  curl -fL --progress-bar -o vendor/tinygo.tar.gz "$url"
  tar xzf vendor/tinygo.tar.gz -C vendor
  rm vendor/tinygo.tar.gz
  echo "✓ go: vendor/tinygo"
  # TinyGo drives the Go toolchain and binaryen's wasm-opt rather than bundling
  # them, so it needs both on PATH to build anything.
  command -v go >/dev/null || echo "  ! go is not on PATH — install it (brew install go)" >&2
  command -v wasm-opt >/dev/null || echo "  ! wasm-opt is not on PATH — brew install binaryen" >&2
}

fetch_rust() {
  if [ -n "$(find "$HOME/.rustup/toolchains" -name rustc -maxdepth 3 2>/dev/null | head -1)" ]; then
    echo "✓ rust: a rustup toolchain is installed"
  else
    echo "Installing Rust via rustup…"
    curl -sSf https://sh.rustup.rs |
      sh -s -- -y --no-modify-path --profile minimal --default-toolchain stable
  fi
  echo "Adding the wasm32-wasip1 target…"
  "$HOME/.cargo/bin/rustup" target add wasm32-wasip1
  echo "✓ rust"
}

wanted="${1:-}"
for language in cpp rust go; do
  if [ -z "$wanted" ] || [ "$wanted" = "$language" ]; then
    "fetch_${language}"
    found=1
  fi
done

if [ -z "${found:-}" ]; then
  echo "No such language: $wanted (known: cpp, rust, go)" >&2
  exit 1
fi
