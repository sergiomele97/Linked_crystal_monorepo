.PHONY: setup run-server run-app run-client-mock test-server test-app build-server build-apk copy-source clean help 

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




#------- Dev environment -------
SHELL := /bin/bash

setup:
	@echo "1. Limpiando repositorios y añadiendo PPA para Python 3.10..."
	# Eliminamos el repo de Yarn que da error de llaves y añadimos el de Python antiguo
	sudo rm -f /etc/apt/sources.list.d/yarn.list
	sudo apt-get update -y || true
	sudo apt-get install -y software-properties-common
	sudo add-apt-repository -y ppa:deadsnakes/ppa
	sudo apt-get update -y

	@echo "2. Instalando dependencias del sistema (incluyendo Python 3.10 y Go)..."
	sudo apt-get install -y \
		python3.10 python3.10-venv python3.10-dev \
		python3-pip python3-setuptools git zip openjdk-17-jdk \
		libffi-dev libssl-dev libsqlite3-dev zlib1g-dev \
		libjpeg-dev libfreetype-dev wget unzip \
		autoconf automake libltdl-dev libtool m4 pkg-config xclip \
		golang-go

	@echo "3. Configurando entorno virtual con Python 3.10..."
	rm -rf .venv
	python3.10 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install buildozer cython kivy
	.venv/bin/pip install -r Linked_crystal/app/requirements.txt

	@echo "4. Configurando entorno de Go..."
	# Descarga y limpia módulos
	cd Linked_crystal/server/src && go mod tidy
	cd Linked_crystal/server/src && go mod download

	@echo "5. Preinstalando Android SDK build-tools..."
	mkdir -p ~/.buildozer/android/platform
	cd ~/.buildozer/android/platform && \
	if [ ! -d "android-sdk" ]; then \
		mkdir -p android-sdk && cd android-sdk && \
		wget https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip -O cmdtools.zip && \
		unzip -q cmdtools.zip -d cmdline-tools && \
		rm cmdtools.zip && \
		mkdir -p cmdline-tools/latest && \
		mv cmdline-tools/cmdline-tools/* cmdline-tools/latest/ || true && \
		yes | cmdline-tools/latest/bin/sdkmanager --licenses && \
		yes | cmdline-tools/latest/bin/sdkmanager "platform-tools" "build-tools;34.0.0" "platforms;android-34"; \
	fi

	@echo "6. Fix sdkmanager path..."
	mkdir -p ~/.buildozer/android/platform/android-sdk/tools/bin
	ln -sf ~/.buildozer/android/platform/android-sdk/cmdline-tools/latest/bin/sdkmanager ~/.buildozer/android/platform/android-sdk/tools/bin/sdkmanager

	@echo "7. Configurando python-for-android release-2024.01.21..."
	if [ ! -d "$$HOME/.buildozer/android/platform/python-for-android" ]; then \
		git clone --depth=1 --branch release-2024.01.21 https://github.com/kivy/python-for-android $$HOME/.buildozer/android/platform/python-for-android; \
	fi
	
	@echo "--- SETUP FINALIZADO ---"
	@echo "Entrando en el entorno virtual (escribe 'exit' para salir):"
	bash --rcfile <(echo "source ~/.bashrc; source .venv/bin/activate")

clean:
	@echo "Limpiando archivos temporales y entornos..."
	rm -rf .venv
	rm -rf Linked_crystal/app/APKbuilder/.buildozer
	rm -rf Linked_crystal/app/APKbuilder/bin
	rm -rf Linked_crystal/app/src/config.py
	# Mantengo el borrado de .buildozer para limpieza profunda como pediste
	rm -rf ~/.buildozer
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

	@echo "Limpiando binarios y caché de Go..."
	# Borra el binario generado por build-server
	rm -f Linked_crystal/server/server
	# Limpia la caché de tests y de construcción de Go
	go clean -cache -testcache

#------- Run code -------
run-server:
	cd Linked_crystal/server/src && go run cmd/server/main.go

run-app:
	cd Linked_crystal/app/src && ../../../.venv/bin/python3 main.py

run-client-mock:
	cd Linked_crystal/server/src && ../../../.venv/bin/python3 client-mock/client_example.py

#------- Run tests -------
test-server:
	@chmod +x Linked_crystal/server/src/test/run_tests.sh
	cd Linked_crystal/server/src && ./test/run_tests.sh

test-app:
	@chmod +x Linked_crystal/app/tests/run_tests.sh
	cd Linked_crystal/app && ./tests/run_tests.sh

#------- Build binaries -------
build-server:
	cd Linked_crystal/server/src && go build -v -o ../server ./cmd/server

build-apk:
	@echo "Construyendo APK (Debug)..."
	cd Linked_crystal/app/APKbuilder && \
	ANDROIDSDK=$$HOME/.buildozer/android/platform/android-sdk \
	ANDROIDNDK=$$HOME/.buildozer/android/platform/android-ndk-r25b \
	JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
	../../../.venv/bin/buildozer android debug

#------- Utilities -------
copy-source:
	@echo "Copiando archivos de Go al portapapeles..."
	@find Linked_crystal/server/src/cmd/server/main.go Linked_crystal/server/src/internal/hub/*.go -type f -exec printf "\n--- FILE: %s ---\n" {} \; -exec cat {} \; | xclip -selection clipboard
	@echo "¡Copiado! Ya puedes pegar el código. (Nota: xclip se queda en segundo plano para mantener el portapapeles)"

