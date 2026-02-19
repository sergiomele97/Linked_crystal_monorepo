# Workflow de Desarrollo y QA

Debido a recientes regresiones, se establece este flujo de trabajo estándar para mantener un historial limpio y asegurar la calidad del software.

## 1. Creación de Rama
Se crea una rama nueva para cada feature con la siguiente nomenclatura:
`features/nombrefeature`

## 2. Desarrollo y Commits
- Se realizan los cambios, a ser posible, en **commits pequeños**.
- Se traen los cambios de `main` a la rama de la feature periódicamente.

## 3. Verificación Pre-Merge (Desktop)
Antes de integrar, es obligatorio cumplir estos pasos:
1. Comprobar funcionalidad OK en **Desktop**.
2. Pasar los **tests** del sistema.

## 4. Pull Request y Git History
- Se pushea y se hace **PR a main en un único commit**.
- **Nota:** La rama `features/nombrefeature` con sus commits pequeños **no se borra**; se puede reutilizar y/o usar como historial detallado.

## 5. CI/CD y Compilación
Una vez integrados los cambios en `main`, se lanzarán las **CI/CDs automáticamente**, incluyendo la que compila el **APK**.

## 6. QA Manual (Checklist APK)
La APK generada debe probarse manualmente revisando los siguientes puntos:

- [ ] Permite seleccionar el rom.
- [ ] Permite conectarse al servidor.
- [ ] Permite lanzar el emulador.
- [ ] El gamepad responde.
- [ ] Calidad de la emulación (no se ve a tirones).
- [ ] Calidad sonido (se escucha bien sin ruidos extraños).
- [ ] Permite guardar partida (Cerrar y volver a abrir).
- [ ] Permite mandar mensajes en chat.
- [ ] **(Pendiente)** Cable link.