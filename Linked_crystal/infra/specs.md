# TFS: Arquitectura de Pipelines CI/CD

Este documento detalla la especificación técnico-funcional de la infraestructura de automatización del monorepo.

## 1. Estrategia General
- **Core**: Todas las pipelines dependen del `Makefile`. El YAML solo gestiona el flujo de GitHub; la lógica de construcción/test vive en el código.
- **Entornos**:
  - `local`: Uso manual vía `make setup`.
  - `development` (dev): Rama `main`. Despliegue automático a servidor self-hosted.
  - `production` (prod): Disparo manual (`workflow_dispatch`). Despliegue a servidor cloud vía SSH/SCP.

## 2. Especificaciones de CI (Integración Continua)
Las pipelines de CI se activan por cambios en sus respectivos directorios (`Linked_crystal/server/**` o `Linked_crystal/app/**`).

### Server (`DEV_CI_SERVER.yml`)
- **Setup**: Go 1.25 estandarizado.
- **Validación**: `make test-server`.
- **Benchmarking**: Ejecución de `stress.go` y publicación de resultados en `gh-pages` mediante `github-action-benchmark`.

### App (`DEV_CI_APP.yml`)
- **Setup**: Python 3.10.
- **Gráfico**: Uso de `xvfb-run` para simular entorno gráfico en tests de Kivy.
- **Validación**: `make test-app`.

## 3. Especificaciones de CD (Despliegue Continuo)

### Server (Dev/Pro)
- **Construcción**: `make build-server` (CGO deshabilitado para máxima compatibilidad).
- **Despliegue Dev**: Actualización de binario y reinicio de servicio `systemd` en runner local.
- **Despliegue Pro**: Transferencia vía SCP y ejecución de script de gestión vía SSH.
- **Health Check**: Bloqueo de pipeline si el servidor no responde con `status: ok` en `/health` tras 5 reintentos.

### App (APK Builder)
- **Setup**: `make setup-build-apk`.
- **Build**: Uso de `buildozer` para generar APK de debug.
- **Artifacts**: Publicación del `.apk` resultante para descarga.

## 4. Optimizaciones Técnicas (Performance)
- **Shared Caching**: Todas las pipelines comparten versiones de Go (1.25) y Python (3.10) para maximizar el "cache hit" de dependencias.
- **Venv Caching**: En CI de App, se cachea el directorio `.venv` completo para evitar la compilación de Kivy/Cython (ahorro de ~3 mins).
- **Apt-Get**: Uso de `apt-install-app` para descargar solo las librerías compartidas mínimas necesarias.

## 5. Nomenclatura de Workflows
- `DEV_CI_PRODUCT.yml`: Integración y calidad en desarrollo.
- `DEV_CD_PRODUCT.yml`: Despliegue a entorno de pruebas.
- `PRO_CD_PRODUCT.yml`: Despliegue a entorno productivo.
