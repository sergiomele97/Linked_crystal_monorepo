.PHONY: setup setup-app setup-build-apk run-server run-app run-client-mock test-server test-app build-server build-apk apk-setup copy-source clean help apt-install apt-install-app

# Dependencias del sistema agrupadas para evitar redundancia
DEPS_SYS_CORE  := build-essential python3-pip python3-venv golang-go
DEPS_SYS_KIVY  := libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
                  libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev zlib1g-dev
DEPS_SYS_GSTR  := libgstreamer1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good
DEPS_SYS_EXTRA := libjpeg-dev libfreetype6-dev libportaudio2 xvfb


help:
	@echo "Linked Crystal - Development"
	@echo ""
	@echo "Usage:"
	@echo "  make setup            - Prepara TODO el entorno (Sistema + Python + Go)"
	@echo "  make run-server       - Lanza el servidor Go"
	@echo "  make run-app          - Lanza la aplicación Kivy"
	@echo "  make test-server      - Ejecuta tests de servidor"
	@echo "  make test-app         - Ejecuta tests de la aplicación"
	@echo "  make build-server     - Compila el binario del servidor"
	@echo "  make clean            - Limpia el entorno y archivos temporales"
	@echo ""
	@echo "Comandos adicionales:"
	@echo "  make build-apk        - Compila el APK para Android"
	@echo "  make run-client-mock  - Lanza un cliente Python de prueba"

# --- INTERNAL / CI COMMANDS ---

apt-install-app:
	@echo "Instalando dependencias mínimas para CI..."
	sudo apt-get update && sudo apt-get install -y --no-install-recommends \
		$(DEPS_SYS_KIVY) $(DEPS_SYS_EXTRA)

setup-app:
	@if [ ! -d ".venv" ]; then python3.10 -m venv .venv; fi
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r Linked_crystal/app/requirements.txt

setup-build-apk:
	@if [ ! -d ".venv" ]; then python3.10 -m venv .venv; fi
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install buildozer cython

# --- PUBLIC TARGETS ---

apt-install:
	@echo "Instalando dependencias del sistema..."
	sudo apt-get update && sudo apt-get install -y \
		$(DEPS_SYS_CORE) $(DEPS_SYS_KIVY) $(DEPS_SYS_GSTR) $(DEPS_SYS_EXTRA)

setup:
	@if [ -f /etc/debian_version ]; then $(MAKE) apt-install; fi
	$(MAKE) setup-app
	cd Linked_crystal/server/src && go mod download

run-server:
	cd Linked_crystal/server/src && go run cmd/server/main.go

run-app:
	cd Linked_crystal/app/src && ../../../.venv/bin/python3 main.py

run-client-mock:
	cd Linked_crystal/server/src && ../../../.venv/bin/python3 client-mock/client_example.py

test-server:
	@chmod +x Linked_crystal/server/src/test/run_tests.sh
	cd Linked_crystal/server/src && ./test/run_tests.sh

test-app:
	@chmod +x Linked_crystal/app/tests/run_tests.sh
	cd Linked_crystal/app && ./tests/run_tests.sh

build-server:
	cd Linked_crystal/server/src && go build -v -o ../server ./cmd/server

build-apk:
	cd Linked_crystal/app/APKbuilder && ../../../.venv/bin/buildozer android debug

copy-source:
	@echo "Copiando archivos de Go al portapapeles..."
	@find Linked_crystal/server/src/cmd/server/main.go Linked_crystal/server/src/internal/hub/*.go -type f -exec printf "\n--- FILE: %s ---\n" {} \; -exec cat {} \; | xclip -selection clipboard
	@echo "¡Copiado! Ya puedes pegar el código. (Nota: xclip se queda en segundo plano para mantener el portapapeles)"

clean:
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -rf {} +
