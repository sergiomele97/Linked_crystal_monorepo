# Definir especificación funciónal pipelines

El objetivo es:

1 CI + 1 CD por producto (sin contar wiki) y por entorno (sin contar local).

Entornos: local, development (dev) rama: main, production (prod) rama: release.

Productos: app, server, wiki.

CI:
- Correr los tests.
- Ejecuta benchmarks.

CD:
- Despliega

Nomenclatura:

"CD/CI_product_environment.yml"
