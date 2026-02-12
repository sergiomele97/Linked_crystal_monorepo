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
	@echo "  make clean            - Limpia el entorno y archivos temporales"
	@echo ""
	@echo "Comandos adicionales:"
	@echo "  make build-server     - Compila el binario del servidor"
	@echo "  make build-apk        - Compila el APK para Android"
	@echo "  make run-client-mock  - Lanza un cliente Python de prueba"

# --- INTERNAL / CI COMMANDS ---

apt-install-app:
	@echo "Instalando dependencias mínimas para CI..."
	sudo apt-get update && sudo apt-get install -y --no-install-recommends \
		$(DEPS_SYS_KIVY) $(DEPS_SYS_EXTRA)

setup-app:
	@if [ ! -d ".venv" ]; then \
		echo "Creando entorno virtual con Python 3.10 (requerido para dependencias críticas)..."; \
		if command -v python3.10 >/dev/null; then \
			python3.10 -m venv .venv || exit 1; \
		else \
			echo "ERROR: python3.10 es obligatorio para cumplir con numpy==1.21.6."; \
			echo "Por favor, instala python3.10 o usa el DevContainer."; \
			exit 1; \
		fi \
	fi
	@./.venv/bin/python -m pip install --upgrade pip
	@./.venv/bin/python -m pip install -r Linked_crystal/app/requirements.txt

setup-build-apk:
	@if [ ! -d ".venv" ]; then python3 -m venv .venv; fi
	./.venv/bin/pip install --upgrade pip
	./.venv/bin/pip install buildozer cython

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
	@echo "Construyendo APK (limpiando y forzando rutas de Docker)..."
	cd Linked_crystal/app/APKbuilder && \
	sed -i 's|^#\?android.sdk_path =.*|android.sdk_path = /home/developer/android-sdk|' buildozer.spec && \
	sed -i 's|^#\?android.ndk_path =.*|android.ndk_path = /home/developer/android-ndk-r25b|' buildozer.spec && \
	sed -i 's|^android.ant_path =.*|#android.ant_path =|' buildozer.spec && \
	env -u VIRTUAL_ENV APP_ACCEPT_SDK_LICENSE=1 buildozer android debug

copy-source:
	@echo "Copiando archivos de Go al portapapeles..."
	@find Linked_crystal/server/src/cmd/server/main.go Linked_crystal/server/src/internal/hub/*.go -type f -exec printf "\n--- FILE: %s ---\n" {} \; -exec cat {} \; | xclip -selection clipboard
	@echo "¡Copiado! Ya puedes pegar el código. (Nota: xclip se queda en segundo plano para mantener el portapapeles)"

clean:
	rm -rf .venv
	rm -rf Linked_crystal/app/APKbuilder/.buildozer
	rm -rf Linked_crystal/app/APKbuilder/bin
	find . -type d -name "__pycache__" -exec rm -rf {} +

deep-clean: clean
	@echo "Limpieza profunda: eliminando cualquier rastro de buildozer y temporales..."
	rm -rf ~/.buildozer
	rm -rf Linked_crystal/app/APKbuilder/.buildozer

# --- INTEGRITY TEST ---
test-devex:
	@echo "### STARTING DEVEX INTEGRITY TEST ###"
	$(MAKE) setup
	$(MAKE) test-server
	$(MAKE) test-app
	$(MAKE) build-apk
	@echo "### DEVEX INTEGRITY TEST PASSED ###"
