#!/usr/bin/env bash
# Wrapper fino (Linux/macOS): localiza o Python 3 e executa o núcleo menu-reversa-openclaude.py.
# Não contém lógica de negócio; toda a lógica vive em menu-reversa-openclaude.py.
# Compatível com bash 3.2+.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORE="$SCRIPT_DIR/../menu-reversa-openclaude.py"

detect_python() {
  local candidate
  for candidate in python3 python py; do
    if command -v "$candidate" >/dev/null 2>&1; then
      if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' >/dev/null 2>&1; then
        echo "$candidate"
        return 0
      fi
    fi
  done
  return 1
}

if [ ! -f "$CORE" ]; then
  echo "ERRO: menu-reversa-openclaude.py não encontrado em $CORE" >&2
  exit 1
fi

PY="$(detect_python || true)"
if [ -z "${PY:-}" ]; then
  echo "ERRO: Python 3 não encontrado. Instale Python 3 e tente novamente." >&2
  exit 1
fi

exec "$PY" "$CORE" install "$@"
