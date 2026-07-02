#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERRO: python3 nao encontrado no Ubuntu."
    exit 1
fi

python3 -u scripts/package-windows.py "$@"
