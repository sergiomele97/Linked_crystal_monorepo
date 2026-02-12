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
setup:
	@if [ -f /etc/debian_version ]; then $(MAKE) apt-install; fi
	$(MAKE) setup-app
	cd Linked_crystal/server/src && go mod download

clean:
	rm -rf .venv
	rm -rf Linked_crystal/app/APKbuilder/.buildozer
	rm -rf Linked_crystal/app/APKbuilder/bin
	find . -type d -name "__pycache__" -exec rm -rf {} +

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
	@echo "Construyendo APK (limpiando y forzando rutas de Docker)..."
	cd Linked_crystal/app/APKbuilder && \
	sed -i 's|^#\?android.sdk_path =.*|android.sdk_path = /home/developer/android-sdk|' buildozer.spec && \
	sed -i 's|^#\?android.ndk_path =.*|android.ndk_path = /home/developer/android-ndk-r25b|' buildozer.spec && \
	sed -i 's|^android.ant_path =.*|#android.ant_path =|' buildozer.spec && \
	env -u VIRTUAL_ENV APP_ACCEPT_SDK_LICENSE=1 buildozer android debug

#------- Utilities -------
copy-source:
	@echo "Copiando archivos de Go al portapapeles..."
	@find Linked_crystal/server/src/cmd/server/main.go Linked_crystal/server/src/internal/hub/*.go -type f -exec printf "\n--- FILE: %s ---\n" {} \; -exec cat {} \; | xclip -selection clipboard
	@echo "¡Copiado! Ya puedes pegar el código. (Nota: xclip se queda en segundo plano para mantener el portapapeles)"

