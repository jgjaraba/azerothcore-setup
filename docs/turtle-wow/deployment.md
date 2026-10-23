# Aplicación de Turtle con los scripts del proyecto

## Puntos de entrada

Se reutilizan los dos instaladores existentes, no un instalador Turtle paralelo:

- **`scripts/apply-core-patches.sh`**: solo código fuente. Su manifiesto incluye
  `turtle-pilot-extractors.patch`; no requiere cambios en el script para aceptar
  ese parche. Los extractores sirven para regenerar datos, no para ejecutar el
  piloto ya generado. Otros parches conservan sus propias necesidades de build.
- **`scripts/apply-db-world.sh`**: SQL del proyecto y, con `--with-server-data`,
  archivos servidor. Sin argumentos mantiene el comportamiento anterior: SQL
  solamente. No instala ni modifica el cliente.

Instrucciones breves y copia manual de MPQ: [README principal](../../README.md).
No se afirma que estos dos scripts instalen el sistema operativo, core/módulos
o sus bases upstream desde cero. Son el overlay de customizaciones del proyecto.

## Fuentes conservadas en el repositorio

| Datos | Fuente |
|---|---|
| Código de extractores | `patches/core/turtle-pilot-extractors.patch`, en su manifiesto |
| Instancia y acceso: diez filas SQL | `turtle_wow_maps.sql` y `turtle_wow_crypt_access.sql`, en el manifiesto world |
| Geometría, colisión, navegación y metadatos | `data/server/turtle-crypt/`, inventariados en `data/server/manifest.json` |
| Cliente custom esES aceptado | `client_patches/turtle_crypt/r5-coordinated/Data/`: T y los dos Z coordinados |
| Cliente stock esES opcional | `client_patches/turtle_crypt/stock-esES/`: T aislado e informe de base |

El manifiesto servidor actual verifica tamaños/SHA256 y cobertura de431 archivos:
425 binarios —seis mapas, árbol y seis tiles VMap, parámetros y seis tiles MMap,
405 modelos de colisión—, cinco DBC geográficas **compactas con filas propias**
y un delta natural de siete rasgos Troll y cuatro Tauren de la
[entrega acumulativa](tauren-customizations.md).
La cripta original conserva sus430 archivos; la ampliación no los reemplaza.
Los nombres de164 modelos físicos terminan en `.m2`; son colisión servidor con
cabecera VMAP_4.8, no modelos cliente MD20. Copiar solo `800*` es insuficiente.

Los archivos de cliente se conservan separados de las distribuciones regular/HD
anteriores. Ninguna de esas dos distribuciones se reemplaza automáticamente.
La stock no incorpora las104 filas ajenas de WorldMapArea del T r5 ni su cambio
de Ruby Sanctum; los Z coordinados no son un reemplazo compatible con HD.
Comprobar `client_patches/turtle_crypt/SHA256SUMS` antes de la copia manual.

Estos artefactos finales no dependen de que exista `work/` para instalarse. En
el árbol de trabajo son material destinado al repositorio privado; conservarlos
en su historia/copia privada corresponde al usuario. No se publican ni se hacen
commits/pushes automáticamente. La receta de preservación inicial es
`tools/stage_turtle_project_assets.py`; repetirla no es requisito de instalación.
Reconstruir desde clientes fuente sigue siendo un problema distinto y requiere
las entradas y el arte manual de la [guía](migration-guide.md).

## Validación y aplicación

```sh
scripts/apply-core-patches.sh --validate
scripts/apply-db-world.sh --validate --with-server-data
```

El segundo comando verifica manifiestos y hashes, **sin acceso a BD ni destino**.
Para comprobar el destino sin modificarlo:

```sh
python3 tools/apply_project_server_data.py check \
  --manifest data/server/manifest.json --data-dir /ruta/DataDir
```

Aplicación, con servidor detenido y acceso exclusivo:

```sh
REPO=/ruta/azerothcore scripts/apply-core-patches.sh
scripts/apply-db-world.sh --with-server-data \
  --data-dir /ruta/DataDir --state-dir /ruta/estado-fuera-de-DataDir/turtle \
  --offline
```

Requisitos: Bash, Git, Python3.11+, cliente MySQL y un AzerothCore compatible ya
preparado con datos335, esquema world y dependencias de módulos del manifiesto.
Configurar `LOGIN_PATH` fuera del repositorio; el destino SQL sigue siendo
`acore_world`, como especifican los SQL canónicos. `SQL_DIR`/`MANIFEST` permiten
fixtures o inventarios explícitos; por defecto se aplica **todo** el manifiesto
world, no solo Turtle. El SQL general mantiene su orden y semántica previa.

`--data-dir` es el DataDir efectivo que contiene `dbc`, `maps`, `vmaps` y `mmaps`.
`--offline` declara que el servidor está parado y no habrá otro escritor desde
el preflight hasta terminar; no para servicios por sí mismo. El estado debe
quedar fuera de DataDir y del directorio de fuentes de los assets.

El instalador captura el plan completo de archivos antes de cualquier SQL.
Comprueba compatibilidad binaria nativa mediante muestras de mapa0
(MAPS9/build12340, VMAP_4.8, MMap20/Detour7), colisiones y fusiones DBC. Después
ejecuta el SQL en su orden habitual y vuelve a comprobar el plan antes de
instalar. Conserva las filas/cadenas DBC ajenas y ordena AreaTrigger por MapID.
Los binarios existentes solo se aceptan si son idénticos; no se sobrescriben
otros modelos o geometría. Los subdirectorios DBC de locales se rechazan porque
necesitan migración explícita de sus overrides.

Se mantienen los cinco deltas DBC en archivos, en vez de convertirlos a nuevos
overlays SQL. En particular, WorldMapArea se indexa por AreaID, mientras el
loader SQL ordena por ID y dimensiona usando la primera fila: añadir674/5086
sin revisar los overrides superiores existentes puede infradimensionar su
índice. No introducir ese cambio como una supuesta equivalencia automática.

Map800 conserva LoadingScreenID0 en servidor y511 en cliente; LoadingScreens
solo se añade al cliente. El helper de archivos no escribe metadatos SQL ni
reemplaza DBC enteras por las de DEV.

## Reaplicación, fallos y recuperación

Repetir el mismo comando con el mismo estado comprueba archivos instalados y
los reutiliza; las dos unidades SQL Turtle aceptan repetición idéntica y fallan
ante conflictos. Esto no certifica la idempotencia de cada personalización
ajena del manifiesto general ni hace atómico el lote completo.

**SQL + archivos no son una sola transacción.** Si falla un SQL, el script para
y no instala los archivos, pero pueden permanecer SQL anteriores ya aplicados.
Si falla la copia posterior, el SQL ya puede estar aplicado. Diagnosticar ese
estado antes de arrancar el servidor; no usar `mysql --force`.

Los originales de los archivos, su ausencia anterior, sus permisos y los
temporales propios quedan en un diario durable. Reversión de **archivos solo**:

```sh
python3 tools/apply_project_server_data.py rollback \
  --manifest data/server/manifest.json --data-dir /ruta/DataDir \
  --state /ruta/estado-fuera-de-DataDir/turtle --offline
```

Ante una copia/reversión interrumpida, cambiar `rollback` por `recover` con los
mismos argumentos. Revierte, no continúa. Se rechazan cambios ajenos en los
archivos propios; no se borra por prefijos. Conservar fuentes/manifiesto y
estado para recuperar. Un fallo anterior al primer diario solo deja backups
en preparación: se diagnostica y puede usarse otro estado, siempre que no se
haya borrado manualmente un diario instalado. Después de revertir, conservar
ese estado y usar otro para instalar de nuevo.

La reversión anterior **no retira instancia, triggers, spawns ni reglas SQL**.
Para desinstalar una función hay que usar su rollback SQL específico y auditar
dependencias; este helper no deshace todo el manifiesto world. Ninguna operación
de estos scripts cambia MPQ del cliente: su backup/rollback sigue siendo manual.

## Evidencia y alternativa de exportación

Las pruebas del flujo existente incluyen aplicación/reaplicación de ambos
parches sobre fuentes limpias, pruebas sintéticas del hook, y MySQL privado
con el SQL canónico Turtle y los430 archivos reales. Ver
[validation.md](validation.md) para resultados y límites: no equivalen al
arranque de un reino completo pristine ni a probar un nuevo cliente en juego.

El [formato portable anterior](portable-release.md) se conserva como exportación
autónoma y fixture. No se encadena con este flujo: tiene otras condiciones
iniciales y un diario que también posee sus propias diez filas SQL.
