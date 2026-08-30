#!/usr/bin/env bash
# flatten_tools.sh
# Sube cada herramienta un nivel: cat/subcat/esp/tool/tool.py -> cat/subcat/esp/tool.py
# Borra las carpetas propias vacías resultantes.
#
# Uso:
#   ./flatten_tools.sh           # dry-run
#   ./flatten_tools.sh --apply # ejecuta de verdad
#   ./flatten_tools.sh --force  # sobrescribe destinos existentes

set -euo pipefail

ROOT="$(pwd)"
APPLY=false
FORCE=false

for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=true ;;
    --force) FORCE=true ;;
    -h|--help)
      sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "Argumento desconocido: $arg" >&2; exit 2 ;;
  esac
done

log()  { printf '\033[1;34m[info]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*" >&2; }
err()  { printf '\033[1;31m[err ]\033[0m %s\n' "$*" >&2; }

if [[ ! -d "$ROOT" ]]; then
  err "El directorio actual no existe"; exit 1
fi

# Detectar automáticamente todos los cat/subcat/esp/tool/tool.py
# (estructura de 4 segmentos + archivo con mismo nombre que la carpeta)
moves_count=0
declare -a MOVES=()

while IFS= read -r -d '' py; do
  # py = .../cat/subcat/esp/tool/tool.py
  dir="$(dirname "$py")"
  tool_name="$(basename "$dir")"
  parent="$(dirname "$dir")"
  dst="${parent}/${tool_name}.py"

  # Ignora si por algún motivo no coincide el nombre
  if [[ "$(basename "$py" .py)" != "$tool_name" ]]; then
    warn "nombre inconsistente, salto: $py"; continue
  fi

  # Seguridad: no subir si ya hay un archivo en el destino (a menos que --force)
  if [[ -e "$dst" && "$FORCE" != true ]]; then
    err "destino ya existe, salto: $dst (usa --force)"
    continue
  fi

  MOVES+=("$py|$dst")
  moves_count=$((moves_count + 1))
done < <(find "$ROOT" -mindepth 5 -maxdepth 5 -name "*.py" -not -name "__init__.py" -print0)

log "Detectadas $moves_count herramientas a aplanar."
log "MODO = $([[ "$APPLY" == true ]] && echo 'APPLY' || echo 'DRY-RUN')"
log "FORCE = $FORCE"

for entry in "${MOVES[@]}"; do
  src="${entry%|*}"
  dst="${entry#*|}"

  if [[ "$APPLY" == true ]]; then
    mv "$src" "$dst"
    log "movido: $src -> $dst"
  else
    printf 'DRY-RUN mv %s -> %s\n' "$src" "$dst"
  fi
done

# Borrar carpetas propias (cat/subcat/esp/tool/) que hayan quedado vacías
# Recorremos las mismas que acabamos de mover
log "Borrando carpetas propias vacías…"

clean_dirs=()
for entry in "${MOVES[@]}"; do
  src="${entry%|*}"
  d="$(dirname "$src")"
  clean_dirs+=("$d")
done

# Borrar __pycache__ que pueda haber dentroif [[ "$APPLY" == true ]]; then
  find "$ROOT" -type d -name __pycache__ -prune -exec rm -rf {} +
else
  find "$ROOT" -type d -name __pycache__ -printf 'DRY-RUN rm -rf %p\n'
fi

for d in "${clean_dirs[@]}"; do
  [[ -d "$d" ]] || continue
  if [[ -n "$(ls -A "$d" 2>/dev/null)" ]]; then
    warn "no vacía, no borro: $d"; continue
  fi
  if [[ "$APPLY" == true ]]; then
    rmdir "$d" && log "borrada: $d"
  else
    printf 'DRY-RUN rmdir %s\n' "$d"
  fi
done

log "Listo."
