# Seguimiento automático de rendimiento

La pipeline CH_server.yml ejecuta automáticamente el test de estrés y lo plasma en el dashboard de GitHub pages:

https://sergiomele97.github.io/Linked_crystal_monorepo/dev/bench/

# Guía de cuantificación de rendimiento

## 1. Medir

* **Capacidad Máxima Sostenida**
Cómo medir: Sube numClients en 
stress.go hasta que Fallos sea mayor que 0 tras 2 minutos.

* **Métricas de Salud (El "Coste")**
Cómo medir: Consulta /health cuando el test de estrés esté estable.

## 2. Encontrar culpable

* **Profiling / pprof (El "Culpable")**
Objetivo: Saber qué línea de código optimizar después. Ejecuta pprof.

