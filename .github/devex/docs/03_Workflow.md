Debido a recientes regresiones me he dado cuenta de la importancia de mantener un historial limpio en git. Por esta razón voy es establecer workflow estandarizado de ahora en adelante:

1. Se crea rama nueva para cada feature con nomenclatura:

features/nombrefeature

2. Se realizan los cambios a ser posible en commits pequeños.
3. Se traen los cambios de main.
4. Se comprueba funcionalidad OK en desktop.
5. Se pasan tests.
6. Se pushea y se lanza pipeline de build apk de esa rama
7. La apk se prueba manualmente, puntos a revisar:
 - Permite seleccionar el rom
 - Permite conectarse al servidor
 - Permite lanzar el emulador
 - El gamepad responde
 - Calidad de la emulación (no se ve a tirones)
 - Calidad sonido (se escucha bien sin ruidos extraños)
 - Permite guardar partida (Cerrar y volver a abrir)
 - Permite mandar mensajes en chat
 - (pendiente) cable link
8. Se hace pr a main en un único commit.
(la rama feature con cada commit pequeño no se borra, se puede reutilizar y/o usar de historial)
 