.PHONY: setup run-server run-app run-client-mock test-server test-app build-apk apk-setup copy-source clean help apt-install

# NOTE: This Makefile is optimized for Linux (Debian/Ubuntu).
# For other OSs, you may need to install system dependencies manually.

# Default target
help:
	@echo "Linked Crystal - Development Environment"
	@echo ""
	@echo "Usage:"
	@echo "  make setup            - Install system and local dependencies"
	@echo "  make run-server       - Start the Go server"
	@echo "  make run-client-mock  - Start the Python mock client"
	@echo "  make test-server      - Run server tests"
	@echo "  make test-app         - Run app tests"
	@echo "  make build-server     - Build the Go server binary"
	@echo "  make apk-setup        - Install dependencies for Android build"
	@echo "  make build-apk        - Build the Android APK using Buildozer"
	@echo "  make clean            - Remove artifacts and temporary files"

apt-install:
	@echo "Instalando dependencias del sistema (requiere sudo)..."
	sudo apt-get update && sudo apt-get install -y \
		build-essential python3-pip python3-venv golang-go \
		libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
		libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev \
		zlib1g-dev libgstreamer1.0-dev gstreamer1.0-plugins-base \
		gstreamer1.0-plugins-good

apk-setup:
	@echo "Instalando dependencias adicionales para Android/Buildozer..."
	sudo apt-get update && sudo apt-get install -y \
		openjdk-17-jdk-headless zip unzip autoconf libtool \
		libffi-dev libssl-dev cmake

setup:
	@if [ -f /etc/debian_version ]; then $(MAKE) apt-install; fi
	@if [ ! -d ".venv" ]; then python3.10 -m venv .venv; fi
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r Linked_crystal/app/requirements.txt
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
