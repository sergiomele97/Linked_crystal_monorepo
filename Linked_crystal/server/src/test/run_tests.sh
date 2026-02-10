#!/bin/bash

# Colores ANSI
GREEN='\033[1;32m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Iniciando tests de servidor...${NC}"
echo ""

# Ejecutamos go test -v y procesamos con awk para dar color y contar
# Usamos un archivo temporal para capturar el código de salida final
EXIT_CODE_FILE=$(mktemp)
echo 0 > "$EXIT_CODE_FILE"

go test -v ./... | awk -v green="$GREEN" -v red="$RED" -v yellow="$YELLOW" -v nc="$NC" -v exit_file="$EXIT_CODE_FILE" '
BEGIN { passed=0; total=0; failed=0 }
/=== RUN/ { 
    total++
    print 
    next
}
/--- PASS:/ { 
    printf "%s%s%s\n", green, $0, nc
    passed++
    next 
}
/--- FAIL:/ { 
    printf "%s%s%s\n", red, $0, nc
    failed++
    system("echo 1 > " exit_file)
    next 
}
/PASS/ && !/--- PASS:/ && !/ok/ { 
    printf "%s%s%s\n", green, $0, nc
    next
}
/FAIL/ && !/--- FAIL:/ { 
    printf "%s%s%s\n", red, $0, nc
    next
}
{ print }
END {
    print ""
    print "------------------------------------------------"
    if (failed == 0) {
        printf "%sSUMMARY: PASS %d/%d%s\n", green, passed, total, nc
    } else {
        printf "%sSUMMARY: FAIL (%d/%d passed, %d failed)%s\n", red, passed, total, failed, nc
    }
    print "------------------------------------------------"
}'

# Capturamos el código de salida y limpiamos
FINAL_EXIT=$(cat "$EXIT_CODE_FILE")
rm "$EXIT_CODE_FILE"
exit "$FINAL_EXIT"
