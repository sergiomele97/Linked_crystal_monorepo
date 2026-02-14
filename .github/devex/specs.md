# Developer experience TFS

Este documento define todos los comportamientos esperados por parte del repositorio para facilitarle la vida al desarrollador.

## 1. Wiki

La wiki y sus páginas se definen en el directorio docs y se actualizan automáticamente con cada push a la rama main.

- La wiki tiene solo lo fundamental, prioriza minimizar la frustación del desarrollador y el ruido.

## 2. Makefile y launch.json

Contienen comandos fáciles de lanzar para cada paso del flujo del desarrollo:

- make setup            - Install system and local dependencies
- make clean            - Resets environment
- make run-app          - Start the Python Desktop app
- make run-server       - Start the Go server
- make run-client-mock  - Start the Python mock client
- make test-app         - Run app tests
- make test-server      - Run server tests
- make build-apk        - Build the Android APK using Buildozer

## 3. Settings.json

Oculta directorios como .venv, pycache, etc. para minimizar el ruido.
