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

