# Client Functional Specification

## Menu Screen
1. La app debe abrirse sin errores. 
2. Debe permitir cargar un archivo GBC
3. Debe permitir importar y exportar un archivo de ram en android desde el icono de opciones en la esquina superior derecha.
4. Debe permitir seleccionar un servidor.
    4.1. Debe comprobar la versión y si nuestra versión es menor que la del servidor, debe indicarnos que debemos actualizar la app.
5. Debe permitir iniciar el juego, cambiando de pantalla.

## Emulator Screen
1. Debe iniciar el juego correctamente.
    1.1. El juego debe verse fluido (SUBJETIVO).
    1.2. El audio debe tener calidad correcta (SUBJETIVO).
2. El gamepad debe funcionar correctamente.
3. El icono de chat debe permitir mandar y recibir mensajes.
4. En el overworld, el jugador debe poder ver a los otros jugadores con calidad correcta y sin solapar con menus (SUBJETIVO).
5. El icono de menu debe permitir usar el cable link.
    5.1. Sin intento de conexión, el emulador y la ui no deben bloquearse nunca.
    5.2. Durante el intento de conexión, el emulador y la ui no deben bloquearse nunca. El jugador debe poder elegir cerrar el intento de conexión.
    5.3. Durante el bridge, el emulador y la ui deben bloquearse mientras esperan respuesta del otro jugador durante un máximo de 30 segundos.
