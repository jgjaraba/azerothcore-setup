# Guía de migración Turtle → AzerothCore 3.3.5a

## 1. Objetivo y contrato

El objetivo a largo plazo es incorporar **todo el contenido custom de Turtle**,
manteniendo WotLK y las personalizaciones del proyecto. Esta guía consolida el
procedimiento geográfico probado con Karazhan Crypt y las condiciones para
extenderlo. No afirma que todo Turtle esté inventariado, convertido o integrado.

**335 es la base; Turtle aporta deltas.** No se sustituyen continentes, tablas
DBC ni bases de datos completas por sus equivalentes Vanilla. NPC, quests,
loot, objetos, hechizos y sistemas se migrarán después, por contratos propios;
véase [hoja de ruta](roadmap.md).

Lecturas de referencia:

- [Aplicación con los scripts del proyecto](deployment.md): instalación desde
  artefactos finales del repositorio y copia manual de cliente; distinta de
  reconstruir desde fuentes.
- [Compatibilidad y límites reales](compatibility.md).
- [Inventario preliminar](maps-inventory.md).
- [Identificadores y colisiones](id-mappings.md).
- [Acceso a mazmorra](crypt-portals.md) y [navegación](navigation.md).
- [Evidencias de validación](validation.md), separadas de esta receta vigente.
- [Contrato del piloto](../project/features/turtle-wow-maps.md).

## 2. No confundir los entornos

| Entrada / entorno | Función |
|---|---|
| `/home/dev/wow-turtle` | Snapshot fuente; leer/extractar, no editar |
| `/home/dev/wow-335` | Snapshot de referencia; **no se supone el cliente activo** |
| Cliente de juego del usuario | Instalación independiente, validada mediante hashes reales |
| `/home/dev/azerothcore-setup` | Código propio, SQL, manifiestos, documentación y recetas |
| `/home/dev/azerothcore` | Fuente, módulos, build y runtime **DEV** |
| `work/` | Extracciones, paquetes y evidencia local; excluido de Git |

Una actualización del snapshot no establece sincronización permanente con el
cliente jugado. Registrar por importación el build, locale, archivos y hashes
de ambas entradas; confirmar los del equipo de juego antes de diagnosticarlo.
La firma MPQ, MVER18, un nombre de archivo o una fecha no prueban compatibilidad.

No tocar producción, originales de cliente ni cambios ajenos. Trabajar con
salidas nuevas y reversibles; los builders fallan si una salida ya existe.
Los MPQ, imágenes y datos propietarios se guardan fuera del código versionable,
sin publicarlos automáticamente.

## 3. Preparar herramientas y conservar entradas

### Tooling mínimo

- Python3, CMake, compilador C/C++ y bibliotecas zlib/bzip2.
- StormLib construido localmente con bibliotecas crypto incluidas; `tools/mpq.cpp`.
- Listfile externo, además del interno de cada MPQ cuando exista. Una lista
  incompleta no demuestra que un recurso esté ausente.
- Para editar/decodificar imágenes: versiones fijadas en
  `tools/crypt-map-localization-requirements.txt`.
- Para extractores/consultas nativas: checkout y build compatibles de AzerothCore.

Ejemplo de construcción del CLI MPQ tras obtener las fuentes de StormLib en
`tools/stormlib-src` y fijar su revisión como input de la migración:

```sh
cmake -S tools/stormlib-src -B tools/stormlib-build \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
  -DSTORM_USE_BUNDLED_LIBRARIES=ON \
  -DCMAKE_INSTALL_PREFIX=/home/dev/azerothcore-setup/tools/stormlib
cmake --build tools/stormlib-build -j2
cmake --install tools/stormlib-build
g++ -O2 -std=c++17 -I tools/stormlib/include tools/mpq.cpp \
  tools/stormlib/lib/libstorm.a -lz -lbz2 -lpthread -ldl -o tools/mpq
```

No se ha incorporado un instalador global de dependencias: preparar un entorno
Python aislado con las versiones fijadas; no modificar el Python del sistema.
`tools/mpq` es un CLI básico: el constructor debe verificar membresía,
contenido y roundtrip, no confiar solo en su código de salida ni asumir que su
capacidad actual sirve para un archivo masivo con miles de recursos.

### Recuperación: qué no puede perderse

Conservar en almacenamiento interno con recuperación:

1. Snapshots originales y sus manifiestos SHA256, incluidos los Z originales.
2. Código propio y JSON de decisiones, SQL/manifest y parches de fuente.
3. **Arte manual no regenerable:** `fixed-es.png` del usuario y su hash;
   no puede reconstruirse solo a partir del cliente Turtle.
4. Artefactos intermedios fijados por hash que los builders siguientes leen.
5. Informes de inputs/outputs y evidencia necesaria para repetir cada etapa.
6. Backup de cada dato instalado, y registro explícito cuando un archivo antes
   **no existía**. El rollback de ese caso elimina únicamente el archivo añadido.

Los INSTALL/report bajo `work/` son útiles, pero no sustituyen esta guía ni una
política de copia de seguridad. Su contenido no aparece automáticamente en un
clon del repositorio.

Los recursos finales aprobados para aplicar el piloto se preservan aparte en
`data/server/` y `client_patches/turtle_crypt/`, con manifiestos/hashes. Instalar
desde esos archivos no requiere conservar todo `work/`; reconstruirlos desde
las fuentes sigue necesitando las entradas anteriores.

## 4. Auditoría por región

1. Leer instrucciones del repositorio y docs relevantes. Inspeccionar Git,
   core/módulos, configuración efectiva, procesos y DEV; no inferirlos de docs.
2. Enumerar **todos** los MPQ root/locale/custom y posibles loose files; guardar
   hashes de archivos y recursos efectivos y comprobar orden de carga.
3. Usar `mpq list` y extracción por nombre directo para resolver recursos:

   ```sh
   tools/mpq list ARCHIVO.MPQ LISTFILE
   tools/mpq extract-one ARCHIVO.MPQ 'RUTA\INTERNA\Recurso.dbc' SALIDA.dbc
   python3 tools/dbc.py schema SALIDA.dbc
   ```

4. Separar mapas independientes, tiles nuevos y tiles **comunes modificados**.
   Los175 paths source-only del primer inventario no cubren todas las
   modificaciones geográficas. Determinar perímetro, halo costero y vecinos.
5. Cerrar dependencias transitivas: ADT → WMO/M2 → grupos, modelos, materiales,
   texturas, skins/animaciones cuando proceda; además agua, luz, mapas y minimapas.
6. Comparar semántica, no solo hashes ni existencia de paths. Documentar la
   decisión por recurso: reutilizar, aislar, adaptar, convertir o dejar pendiente.

**Límites actuales:** `mpq_priority.py` y `asset_index.py` dependen de órdenes
estáticos/listings cacheados; no son resolutores completos del cliente de juego.
Los extractores del piloto fuerzan T al final y tampoco prueban esa prioridad.

## 5. Diseñar el delta y asignar IDs

La asignación requiere comparar cliente por locale, DBC servidor independiente,
SQL overlays y fuentes de core/módulos/proyecto. No elegir `max(DBC)+1` sin SQL:
así se perdió la dificultad normal del piloto por la colisión con Naxx40.

Consultar [registro de IDs](id-mappings.md) y
[`CUSTOM-IDENTIFIERS.md`](../project/CUSTOM-IDENTIFIERS.md). Map533 está ocupado
por **Naxxramas WotLK**, no es un slot libre porque su directorio diga
`Stratholme Raid`. Map169/269 y áreas con nombres vacíos en un locale también
requieren auditoría semántica.

Para un continente compartido:

- Preservar los ADT WotLK ajenos al delta y las entradas WDT MAIN existentes.
- Analizar conflictos en tiles comunes, agua, objetos y costuras.
- No convertir un bounding box WorldMapArea en una selección automática de tiles.
- Si una colisión no tiene solución segura, preservar335 y declarar la parte
  Turtle pendiente; no perder contenido nativo silenciosamente.

## 6. Conversión y recursos visuales

- Validar chunks/tamaños/referencias y el esquema real de cada versión.
- No aplicar el conversor inicial a mapas húmedos sin reparar su **layout MHDR**:
  véase el defecto explícito en [compatibilidad](compatibility.md). No existe
  todavía el conversor MCLQ→MH2O citado por un comentario antiguo del código.
- Al cambiar MMDX, reconstruir MMID conservando identidad de slots, incluidas
  referencias reordenadas/repetidas. Comprobar MDDF → MMID → inicio de cadena.
  Hacer lo mismo con MODF/MWID/MWMO; no basta con enumerar nombres válidos.
- Familias WMO completas y coherentes. El piloto usa una **variante nativa
  aislada**, no una conversión íntegra del WMO Turtle. Separar path **y basename**
  porque el extractor VMap aplana nombres. No mezclar grupos por sufijo cuando
  su orden difiere; comparar GroupID, límites y colisión/BSP.
- No sustituir `.MDX` dentro de todos los formatos: los MODN de WMO335 también
  pueden usar esa extensión. Inspeccionar el contrato de cada referencia.
- BLP: comprobar encoding, alfa, dimensiones y mipmaps. La pantalla de carga
  solo necesitó limpiar descriptores inactivos corruptos; sus pixels no se
  reconvirtieron. Edición del plano manual y paletizado están documentados en
  `tools/crypt_map_png.py`, no son una receta para todos los BLP.

## 7. Fusionar DBC y construir paquetes coordinados

Preservar registros/strings nativos y propios y producir un diff acotado.
Translatear los campos de origen al layout335: no copiar tablas Turtle enteras.
En tablas con requisito de orden físico, conservar cada registro opaco pero
insertar correctamente las altas: **AreaTrigger debe ordenarse establemente
por MapID**. La existencia por ID no bastaba para que el cliente lo examinase.

El hash correcto de T no prueba que se utilicen sus recursos. En el piloto,
root Z y esES Z tenían ADT antiguos y Map800 incompatibles que lo sombreaban.
La solución son **copias derivadas** con cambios justificados y comprobación
byteexact del contenido ajeno; nunca modificar los Z originales de referencia.

Antes de entregar:

- Inventario efectivo resultante y colisiones por path/locale.
- Comprobación de todas las entradas por extracción roundtrip del MPQ.
- Hash de cada archivo del conjunto, no solo T.
- Instalación y rollback juntos, con WoW cerrado y backups fuera de Data.
- Re-auditar si el cliente real tiene otras versiones de Z; no sobrescribir
  personalizaciones nuevas con copias de un snapshot anterior.

## 8. Cartografía, idioma y acceso

- Mapas regionales: artwork y WorldMapArea compatibles; mantener schemas y
  baselines cliente/servidor independientes. No importar FrameXML por defecto.
- Minimapa: fusionar el TRS **completo** con la base335. Reemplazarlo por29
  líneas habría borrado los demás minimapas. Mantener claves originales y
  añadir recursos con namespace propio, verificando sus valores efectivos.
- Interiores: comparar GroupID y límites/grid; en el piloto18 imágenes son
  Turtle y5 nativas por diferencias de alineación. No llamarlo all-Turtle.
- Idioma: nombres DBC y rótulos dibujados son cosas distintas. El plano español
  manual es una edición gráfica para cualquier locale que use ese T, no
  selección automática esES. Preservar lienzo, alfa y coordenadas del jugador.
- Loading screen: Map335 campo57 frente a Turtle38; tabla335 de4 campos frente
  a3. HasWideScreen0 si no hay recurso Wide. Actualizar **todas** las copias de
  Map/imagen de mayor prioridad implicadas; r5 actualiza T y ambos Z.
- Acceso: cliente AreaTrigger.dbc + servidor SQL `areatrigger` coincidentes,
  `areatrigger_teleport`, `instance_template`, dificultad soportada y acceso
  nativo según el diseño. El servidor de este proyecto no obtiene esos
  volúmenes de la copia de AreaTrigger.dbc.
- Puertas, muros, llaves y portales son dependencias distintas. En el piloto
  la entrada se adelanta para no modificar map0 y se mantiene min55, sin la
  llave/quest Turtle. Es una adaptación declarada, no igualdad absoluta.

## 9. Extraer e instalar datos servidor

Leer antes las instrucciones aplicables de AzerothCore. El soporte de
extractores se conserva en
[`turtle-pilot-extractors.patch`](../../patches/core/turtle-pilot-extractors.patch),
con [baseline/límites](../../patches/core/turtle-pilot-extractors.md), conforme
a ADR-0003. Validar su aplicación; no asumir que upstream lo contiene.

```sh
scripts/apply-core-patches.sh --validate
```

Con un cliente335 integrado/coordinado, desde un directorio de salida nuevo:

```sh
/home/dev/azerothcore/env/dist/bin/map_extractor -i CLIENT_ROOT -e 2
/home/dev/azerothcore/env/dist/bin/map_extractor -i CLIENT_ROOT -e 1
/home/dev/azerothcore/env/dist/bin/vmap4_extractor -d CLIENT_ROOT/Data --only 800
/home/dev/azerothcore/env/dist/bin/vmap4_assembler
```

Son los argumentos del piloto, no una orden de instalar todo lo obtenido.
El VMap extractor genera `Buildings/`; usar intermediarios nuevos. Comprobar
idioma realmente detectado, nombres de archivo en Linux y listas de archivos
que cada extractor abre. No desplegar sin comparación todos los DBC extraídos:
los extractores del piloto no reproducen toda la cadena custom Z/locale.
Preservar Item/Spell/talentos y demás DBC del proyecto no afectados.

Para SQL, respetar `data/sql/custom/db_world/manifest.txt`, respaldar antes y
usar solo el login DEV local. Aplicar/reaplicar la unidad y probar su rollback.
Los handlers transaccionales y guardas de propiedad evitan sobrescribir filas
ajenas; no usar `--force` para saltar fallos. Un CALL fallido puede dejar la
rutina auxiliar: inspeccionarla antes de retirarla/reintentar.

Preparar datos en staging y desplegar únicamente los archivos previstos, con
backup. No borrar por prefijos amplios para deshacer una región. El perfil de
navegación del piloto se genera aislado con:

```sh
python3 tools/crypt_nav_generate.py --output work/nav-nuevo --all-tiles
python3 tools/build_crypt_nav_probe.py
```

Estos wrappers son **solo mapa800** y requieren la geometría r2 y build nativo
existentes. No son el generador genérico de todos los mapas. Detalles de pruebas,
desconexiones, coordenadas y rollback: [navegación](navigation.md).

## 10. Cadena incremental del piloto: qué reproduce hoy

Los nombres de directorio siguientes son inputs fijados en builders actuales.
Los comandos de construcción requieren salidas nuevas. Si se borran esos
inputs, primero hay que recuperarlos o reconstruir y verificar su procedencia;
no se sustituyen hashes para conseguir que un build acepte datos desconocidos.

| Etapa / script | Inputs que no aparecen mágicamente en un clon |
|---|---|
| Extracción + `adt_convert.py`, `merge_pilot_dbc.py`, CLI MPQ | Clientes, seis ADT fuente, DBC335 efectivos y evidencia de IDs; módulos iniciales específicos, no un bootstrap genérico seguro |
| `build_crypt_fix.py` | MPQ previo `work/patches/patch-T-difficulty-fixed.mpq`; genera familia aislada/r1 |
| `build_pilot_overlay.py` | Snapshot Z/T conocido **y audit JSON externo**; su default del JSON apunta a `/tmp/opencode/crypt-snapshot-audit/report.json` |
| `build_crypt_refs_fix.py` | r1 T + copias Z de `work/client-overlay-r1`; reconstruye MMID y produce r2 |
| `build_crypt_cartography.py` | Conjunto r2, clientes y recursos fijados; produce r3 inglés |
| `localize_crypt_map.py` y `crypt_map_png.py export` | r3; exportación bilingüe actual también requiere la edición automática española. Fue superada artísticamente, pero sigue siendo dependencia de ese exportador |
| `align_crypt_map_png.py` + `crypt_map_png.py import --palette` | PNG original exportado y **fixed-es.png manual**, dependencias de imagen fijadas; produce el T manual aprobado |
| `build_crypt_portals.py` | Paquete manual aprobado, clientes, DBC/server baseline conocido y preflight SQL de lectura; emite orden corregido r4.1 |
| `build_crypt_loading.py` | Tres MPQ r4.1; emite conjunto r5 con pantalla Turtle |
| Navegación | Mapas/VMaps r2 completos y bibliotecas nativas compiladas; perfil local0.9, añadido solo el tile ausente |

**Estado honesto:** hay reproducción verificada por etapas y hashes, incluida
igualdad de builds para varias revisiones; no hay todavía un bootstrap único
desde los dos clientes originales. Generalizar esa cadena y añadir fixtures
húmedos es requisito del próximo hito, no trabajo ya declarado terminado.

Para **aplicar en una base compatible sin repetir la conversión**, usar los
[scripts existentes](deployment.md) con los assets del repositorio. El flujo
incluye el cierre completo de colisiones y deltas DBC, con instalación y
reaplicación probadas en fixture aislado con MySQL real; el cliente se copia
manualmente según el README. No copiar los Z custom ni las DBC completas de r5
sobre un cliente stock. La [exportación portable](portable-release.md) permanece
como formato alternativo, no un paso adicional de ese flujo.

## 11. Entrega, prueba y cierre

El conjunto cliente aceptado del piloto es r5:

| Ruta relativa | SHA256 |
|---|---|
| Data/patch-T.MPQ | 738ef0e3547f2d40ad9e7fbb7ed5608d684bbb51e640b5328b4bf26cce1813ee |
| Data/patch-Z.mpq | 3b4082bfabc3f02a1efedca81b973548d56f56e32cde6ed4609aa0a2e919d3b0 |
| Data/esES/patch-esES-Z.MPQ | 2de9f73504a6ad457942e8cdc5d9aad55fa663395fda7b4c70f0f3bbec5f19b0 |

No son hashes universales de futuros clientes. Los datos servidor incluyen
SQL/DBC del piloto y el tile de navegación de [su contrato](navigation.md).

Validar separadamente: archivos y referencias, extracción/binarios, arranque,
renderizado, colisión/LoS, rutas, acceso y regresiones. Usar estados PASS/FAIL/
NOT RUN/NOT APPLICABLE/BLOCKED y distinguir ejecución del agente de resultados
confirmados por el usuario. Archivo generado no significa ruta válida; exit0
del generador no garantiza que escribiera el tile.

KarazhanCrypt tiene aceptación **práctica** de exploración, presentación,
portales, conejo temporal, pared/entre plantas y agua/borde del pozo. No equivale
a certificar410 consultas parciales, todas las rutas acuáticas, grupos/cadáveres
o todo el contenido Turtle. Mantener excepciones explícitas por región y no
convertirlas en éxitos por repetir una conversión.
