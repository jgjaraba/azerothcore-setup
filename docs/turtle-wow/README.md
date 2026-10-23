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

- [`tauren-customizations.md`](tauren-customizations.md) — entrega acumulativa
  vigente en `client_patches/Data/` y `client_patches/optional-extra-skins/Data/`;
  tauren completo/parcial, pelo/cuernos/adornos y preservación de Troll.
- [`troll-customizations.md`](troll-customizations.md) — ediciones excluyentes de
  Troll de base: principal Forest/pelo/rasgos y opcional con las demás pieles y36 caras
  convertidas; perfiles SQL separados e instrucciones de copia manual.
- [`troll-customizations-v2.md`](troll-customizations-v2.md) — histórico v2 y
  diagnóstico de caras verdes; no es la receta de instalación vigente.
- [`forest-troll-skins.md`](forest-troll-skins.md) — primer piloto de pieles
  nativas: seis tonos por sexo, SQL/MPQ e instalación manual; aceptación práctica
  confirmada por el usuario, sin cobertura exhaustiva DK/HD.
- [`character-skins.md`](character-skins.md) — investigación de pieles raciales
  gratuitas/de tienda como personalización nativa de creación335; viabilidad,
  recursos y límites frente a transformaciones. No instalado.
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
