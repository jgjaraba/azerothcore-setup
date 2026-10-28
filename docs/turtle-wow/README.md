# Migración Turtle WoW — índice

Objetivo a largo plazo: todo el contenido custom de Turtle sobre WotLK335,
preservando lo nativo y lo propio. Karazhan Crypt tiene aceptación geográfica
práctica del usuario. Highlands/Alah'Thalas en mapa0 tiene composición,
publicación regular e instalación servidor comprobadas; el usuario confirmó el
acceso y la corrección de líquidos. Hay pruebas acotadas de render, minimapas y
clic continental en cliente real, no de todo el gameplay ni de todas las rutas.

## Empezar aquí

- **[Instalación cliente vigente: consolidado regular/HD](../../client_patches/README.md)**.
  Los paquetes r5, new-races y las personalizaciones por raza descritos abajo
  conservan contratos históricos; no son capas adicionales para esa entrega.
  Las variantes parciales, v2 Troll y la prueba facial están en
  `client_patches/archive/`; no reaplicar su SQL opcional como paso de instalación.
- **[Aplicación con los scripts existentes](deployment.md)**: SQL/parches y
  recursos servidor conservados en el repositorio; MPQ de cliente con copia
  manual. Incluye comprobaciones, reaplicación y recuperación de archivos.
- **[Guía de migración](migration-guide.md)**: procedimiento vigente, fuentes,
  herramientas, paquetes, integración, pruebas, rollback y límites reales de
  reconstrucción. Es la receta curada, no la cronología de ensayos.
- **[Skill `turtle-zone-import`](../../.opencode/skills/turtle-zone-import/SKILL.md)**:
  flujo para importar otra región o reparar un port, con
  [plantilla de contrato regional](../../.opencode/skills/turtle-zone-import/references/region-contract-template.md).
  La guía sigue siendo el procedimiento canónico; la skill evita omitir etapas.
- **[Hoja de ruta](roadmap.md)**: evolución hasta todo el contenido custom y
  próximo hito recomendado: viabilidad de Tel'Abim y merge continental húmedo.

## Referencias técnicas y evidencia

- [`high-elf-maps.md`](high-elf-maps.md) — contrato geográfico Highlands/Alah'Thalas:
  terreno/agua, assets, source lock, entrega regular y límites de fidelidad.
- [`high-elf-server-data.md`](high-elf-server-data.md) — extracción mapa0, cierre
  VMap completo, MMaps regionales/halo y soporte de instalación schema2 existente.
- [`new-races-client.md`](new-races-client.md) — Altos Elfos22/Goblins23 aditivos:
  contrato del candidato y corrección de texturas aceptada por el usuario para22
  masculino/23 femenino. Preview consolidado regular enUS/esES observado PASS en
  Linux/Wine Direct3D9, incluidos encabezados y18 posiciones de cycling Goblin
  femenino; no acredita gameplay, Windows nativo ni ejecución HD.
- [`tauren-customizations.md`](tauren-customizations.md) — base acumulativa
  histórica en `client_patches/Data/` y `client_patches/archive/optional-extra-skins/Data/`;
  tauren completo/parcial, pelo/cuernos/adornos y preservación de Troll.
- [`troll-customizations.md`](troll-customizations.md) — ediciones excluyentes de
  Troll de base: principal Forest/pelo/rasgos y opcional con las demás pieles y36 caras
  convertidas; perfiles SQL separados y procedimientos históricos de copia manual.
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
