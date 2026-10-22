# Migración Turtle WoW — índice

Objetivo a largo plazo: todo el contenido custom de Turtle sobre WotLK335,
preservando lo nativo y lo propio. El trabajo probado hasta ahora es el piloto
geográfico Karazhan Crypt, aceptado de forma práctica por el usuario; no equivale
a una migración completa ni a navegación exhaustiva.

## Empezar aquí

- **[Aplicación con los scripts existentes](deployment.md)**: SQL/parches y
  recursos servidor conservados en el repositorio; MPQ de cliente con copia
  manual. Incluye comprobaciones, reaplicación y recuperación de archivos.
- **[Guía de migración](migration-guide.md)**: procedimiento vigente, fuentes,
  herramientas, paquetes, integración, pruebas, rollback y límites reales de
  reconstrucción. Es la receta curada, no la cronología de ensayos.
- **[Hoja de ruta](roadmap.md)**: evolución hasta todo el contenido custom y
  próximo hito recomendado: viabilidad de Tel'Abim y merge continental húmedo.

## Referencias técnicas y evidencia

- [`maps-inventory.md`](maps-inventory.md) — inventario **preliminar** de regiones
  y mapas identificados; cobertura, dependencias y destinos todavía incompletos.
- [`compatibility.md`](compatibility.md) — Vanilla→WotLK format gaps and the
  conversion strategy per category.
- [`id-mappings.md`](id-mappings.md) — identifier allocation register and
  collision analysis.
- [`navigation.md`](navigation.md) — local MMap profile, native route/LoS checks,
  remaining disconnected regions and temporary-follower test.
- [`crypt-portals.md`](crypt-portals.md) — acceso nativo, adaptación de puerta,
  SQL guardado, IDs, dificultad y pruebas.
- [`validation.md`](validation.md) — evidencia ejecutada y confirmaciones del
  usuario, con alcance y limitaciones. Las revisiones antiguas son históricas;
  no reutilizar un INSTALL anterior como instrucciones de la entrega actual.

El código propio, SQL, parches y los artefactos finales de `data/server/` y
`client_patches/turtle_crypt/` son material del repositorio privado. Los clientes
fuente, herramientas de terceros e intermedios de `work/` siguen excluidos. La
instalación del piloto no necesita reconstruirlos; convertir de nuevo desde los
clientes originales sigue dependiendo de esos inputs y del PNG manual. La
[exportación portable](portable-release.md) queda como alternativa, no otro
instalador obligatorio del proyecto.

El parche de extractores se preserva en
[`patches/core/turtle-pilot-extractors.patch`](../../patches/core/turtle-pilot-extractors.patch)
y su [contrato](../../patches/core/turtle-pilot-extractors.md). Los archivos de
cliente jugados pueden ser distintos de los snapshots de referencia: verificar
hashes y prioridad, no asumir sincronización.
