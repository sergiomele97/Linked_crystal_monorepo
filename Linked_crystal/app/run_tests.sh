#!/bin/bash

# Colores ANSI
GREEN='\033[1;32m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Iniciando tests del cliente...${NC}"
echo ""

# El script debe ejecutarse desde Linked_crystal/app
# O al menos configuramos el PYTHONPATH relativo a este script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHONPATH="$SCRIPT_DIR/src"
PYTHON_BIN="$SCRIPT_DIR/../../.venv/bin/python3"

# Ejecutamos unittest verbose y procesamos con awk
# Redirigimos stderr a stdout porque unittest escribe ahí los resultados por defecto
$PYTHON_BIN -m unittest discover -v -s "$SCRIPT_DIR/tests" 2>&1 | awk -v green="$GREEN" -v red="$RED" -v yellow="$YELLOW" -v nc="$NC" '
BEGIN { passed=0; total=0; failed=0 }

# Detectar líneas de test individuales (ej: test_something (module.Class) ... ok)
/\.\.\. ok/ {
    total++
    passed++
    printf "%s%s%s\n", green, $0, nc
    next
}

/\.\.\. (FAIL|ERROR)/ {
    total++
    failed++
    printf "%s%s%s\n", red, $0, nc
    next
}

# Líneas de resumen de unittest
/^[[:space:]]*Ran [0-9]+ tests/ {
    # No imprimimos la línea original para mostrar nuestro propio resumen al final
    next
}

/^[[:space:]]*OK$/ {
    next
}

/^[[:space:]]*FAILED \(.*\)$/ {
    next
}

# Saltarse las líneas divisorias de unittest (muchos guiones)
/^-+$/ {
    next
}

# Imprimir el resto (captura mensajes de error, logs de Kivy, etc.)
{ print }

END {
    print ""
    print "------------------------------------------------"
    if (failed == 0 && total > 0) {
        printf "%sSUMMARY: PASS %d/%d%s\n", green, passed, total, nc
    } else if (total > 0) {
        printf "%sSUMMARY: FAIL (%d/%d passed, %d failed)%s\n", red, passed, total, failed, nc
    } else {
        printf "%sNo se encontraron tests o hubo un error al iniciar.%s\n", yellow, nc
    }
    print "------------------------------------------------"
}
'
