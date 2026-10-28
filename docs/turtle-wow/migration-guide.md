# Guía de migración Turtle → AzerothCore 3.3.5a

## 1. Objetivo y contrato

El objetivo a largo plazo es incorporar **todo el contenido custom de Turtle**,
manteniendo WotLK y las personalizaciones del proyecto. Esta guía consolida el
procedimiento geográfico probado con Karazhan Crypt y ampliado con la
[geografía alto elfo de mapa0](high-elf-maps.md): composición continental,
modelos, líquidos, cartografía, instalación y pruebas acotadas en cliente real.
El usuario confirmó acceso y corrección de los líquidos; minimapas y clics
continentales también tienen comprobaciones en cliente real. Eso no certifica
todas las rutas, pisos, clientes ni todo el contenido Turtle.

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
- [Altos Elfos mapa0](high-elf-maps.md) y su [extracción/instalación servidor](high-elf-server-data.md).
- [Skill local de importación](../../.opencode/skills/turtle-zone-import/SKILL.md):
  flujo para el agente y plantilla de contrato, subordinados a esta guía.

### Tres operaciones distintas

| Operación | Entradas necesarias | Lo que no demuestra |
|---|---|---|
| Port desde snapshots | Clientes fuente/referencia, extracciones, esquemas, selección regional y conversiones auditadas | No existe un importador universal desde dos carpetas de cliente |
| Rebuild de cliente preservado | Source locks y archivos durables de `client_patches/archive/source-inputs/`, herramientas de packaging | No necesita los paths históricos de `work/` de la evidencia, pero tampoco reconstruye el port desde Turtle |
| Build/aplicación servidor | Para generar: cliente integrado, staging terreno/assets, extractores y dependencias nativas. Para instalar: payload durable y manifiesto compatibles | Archivar el cliente no elimina las entradas de staging del generador servidor |

Seguir §§2–9 para diseñar otra región. §10 conserva la cadena histórica de la
cripta; §12 muestra las interfaces de la implementación High Elf, **no parámetros
genéricos para cualquier zona**. §13 recoge diagnóstico y §14 el criterio de cierre.

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
salidas nuevas y reversibles; comprobar la política real de cada herramienta:
assets/cartografía exigen salida nueva, DBC admite repetición idéntica y algunos
generadores reanudan únicamente con hashes/cache compatibles. No asumir que
`exist_ok` significa que se puede mezclar otro conjunto de inputs.
Los recursos propietarios finales se conservan en el repositorio privado según
sus manifiestos; snapshots, extracciones y tooling externo permanecen aparte.
No crear commits ni hacer push. Publicar un perfil local del repositorio no
equivale a instalarlo en el cliente jugado ni a publicarlo externamente.

## 3. Preparar herramientas y conservar entradas

### Tooling mínimo

- Python3, CMake, compilador C/C++ y bibliotecas zlib/bzip2.
- StormLib construido localmente con bibliotecas crypto incluidas; `tools/mpq.cpp`.
- Listfile externo, además del interno de cada MPQ cuando exista. Una lista
  incompleta no demuestra que un recurso esté ausente.
- Para editar/decodificar imágenes: versiones fijadas en
  `tools/crypt-map-localization-requirements.txt`.
- Para extractores/consultas nativas: checkout y build compatibles de AzerothCore.
- Para M2 propios: SDK .NET8 y convertidor fijado por
  `scripts/build-new-races-model-converter.sh`; consultar el contrato de
  [M2Lib/driver](../../patches/third-party/m2lib/README.md) y sus límites.
- Para ejecutar el scanner x86 sin lanzar WoW: entorno aislado con
  `tools/probe-adt-client-requirements.txt`; [uso del probe](../../tools/probe_adt_client.md).

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

Dar espacio suficiente a temporales y comprobar lectura, escritura y cierre:
un fichero truncado por falta de espacio no es un nuevo baseline válido. El CLI
comprueba esos errores; los tests de `test_mpq_io.py` incluyen escritura fallida.
Puede fijarse `TMPDIR` a un directorio verificado en disco bajo `work/`, sin
limpiar trabajo ajeno ni usar una ruta temporal como input durable.

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
7. Crear un contrato regional con inputs y decisiones auditables: mapa/áreas,
   selección de celdas, halo, remaps, recursos, idioma y límites. La
   [plantilla de la skill](../../.opencode/skills/turtle-zone-import/references/region-contract-template.md)
   evita omitir partes; no es una reserva automática de IDs ni un historial de tarea.

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

### Composición por celda y placements

Cuando un ADT contiene región nueva y contenido nativo, no sustituirlo entero.
Comparar los145 vértices, agujeros, materiales y bordes por MCNK; expandir el halo
hasta cerrar los contactos fuente→nativo sin inventar terreno. La selección
High Elf conserva3899 celdas fuente y2245 nativas en24 tiles: es un ejemplo
fijado, no el perímetro de la próxima región. Un tile reserializado pero
semánticamente nativo puede omitirse del despliegue servidor.

Reconstruir MTEX/MCLY/MTXF y ambas tablas de objetos, sus indirectiones y MCRF
con sus dos contadores. Determinar ownership de placements en el conjunto
regional: copiar referencias de un vecino puede resucitar un objeto reemplazado
o dejarlo flotando sobre el relieve nuevo. No deduplicar solo por posición.
Los cambios de decoración requeridos por la nueva geografía son adaptaciones
explícitas; las celdas nativas ajenas al delta deben conservar su contenido.

**Los UID de MDDF/MODF comparten namespace de instancias para VMap.** Auditar el
mapa completo efectivo de ambos snapshots, incluidos tiles no portados. Conservar
la identidad de una instancia repetida entre tiles, resolver variantes de bounds
solo con evidencia y reservar remaps globales realmente libres. No asignar
`max(UID de los tiles seleccionados)+1`. Un conflicto nativo/nativo inesperado
requiere investigación, no una reasignación indiscriminada.

## 6. Conversión y recursos visuales

- Validar chunks/tamaños/referencias y el esquema real de cada versión.
- El **layout MHDR ya está corregido**: MFBO9/MH2O10/MTXF11. Validar offsets,
  tamaños y fixtures reales; véase [compatibilidad](compatibility.md). El port
  alto elfo conserva MH2O existente en origen y desactiva MCLQ duplicado: no
  necesita conversión MCLQ→MH2O. Un conversor general de ese tipo sigue sin existir.
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

### Terreno húmedo: framing y semántica son comprobaciones distintas

Los offsets MCNK incluyen los8 bytes exteriores; los offsets internos MH2O se
miden desde su payload. En las celdas legacy examinadas, MCNR declara435 bytes
pero ocupa448 con padding, y `sizeAlpha` incluye la cabecera MCAL. No cambiar esas
convenciones por intuición. El serializador debe actualizar tamaños MCNK, MCIN
y MHDR después de cualquier splice.

Mantener del mismo lado que el terreno todas las capas MH2O, atributos, rectángulos,
máscaras, tipos y vértices; relocalizar referencias internas, no copiar offsets
del archivo anterior. Un ID de LiquidType no es un enum de categoría ni un
formato de vértices: el ID2 stock es Ocean, no magma.

En el compositor High Elf, MH2O es autoridad donde existe. **Antes** de desactivar
el MCLQ duplicado se valida su extent todavía activo y se normaliza su tamaño
propio. Después se limpian flags líquidos legacy y offset/tamaño, reteniendo el
payload opaco. El cliente recorre también bloques físicos: un MCLQ retenido con
ambos tamaños0 le hace leer agua como cabeceras y puede fallar en `0x007C3A42`.
Las celdas legacy-only no se desactivan. No presentar esa política scoped como
un conversor general de líquidos.

Exigir tests positivos y negativos de framing (`adt_client.py`) y, para un EXE
compatible con el pin, ejecución de la rutina x86 (`probe_adt_client.py`). Que el
scanner retorne no basta: comprobar tags, límites y presupuesto de instrucciones.
Después probar render, profundidad y natación reales; el scanner no dibuja agua.

### M2 y WMO propios

Un `.M2` Turtle con MD20 versión256 necesita conversión real a264, SKIN y cierre
de texturas/animaciones; no basta renombrar `.mdx`. Conservar vertices, bind bones,
materiales y clips; registrar fallbacks y rechazar semánticas no soportadas.
El árbol High Elf exigió adaptar diez emisores de partículas, con control nativo
OracleTree, sin sustituir el modelo ni eliminar efectos. La conversión de cuatro
modelos reales no acredita todas las variantes M2. Especificación y límites:
[partículas Classic→Wrath](../../patches/third-party/m2lib/particles.md).

Para WMO, validar también estructuras anidadas, referencias de materiales,
doodads/sets, UV, colores, portales y BSP, no únicamente MVER17 y presencia de
grupos. **Sin MLIQ no significa sin líquido**: con `MOHD.flags & 0x4`, el valor
15 de MOGP se interpreta como19/WMO Magma y puede inundar el volumen del grupo.
Las quince familias secas High Elf se adaptan limpiando solo ese bit del root,
tras comprobar por hash todos sus grupos sentinel15, sin MLIQ ni flag líquido.
No limpiar genéricamente edificios, cambiar todos los15 a0 ni borrar agua real.

Separar efectos cliente y servidor con mediciones: en este caso la reextracción
con los binarios instalados dio los mismos datos servidor, que ya eran secos.
El contrato cliente no permite deducir qué escribió un extractor concreto.

## 7. Fusionar DBC y construir paquetes coordinados

Preservar registros/strings nativos y propios y producir un diff acotado.
Translatear los campos de origen al layout335: no copiar tablas Turtle enteras.
En tablas con requisito de orden físico, conservar cada registro opaco pero
insertar correctamente las altas: **AreaTrigger debe ordenarse establemente
por MapID**. La existencia por ID no bastaba para que el cliente lo examinase.

Auditar también los exploreFlags y las claves naturales, no solo IDs de fila.
Ejemplos High Elf: áreas3881–3883 ocupadas en Outland se remapean a6500–6502;
el exact lookup WMO necesita `(root,nameSet,group)` realmente colocado. El
grupo−1 no sustituye al grupo0 de la posada. No importar filas heredadas que
todavía describen correctamente un WMO nativo ajeno a la región.

Cada tabla se fusiona sobre su **baseline independiente** de servidor y de cada
locale cliente; los deltas no son tablas completas instalables en un MPQ. La
entrega regular actual sitúa recursos geográficos en T sin DBC, tablas no
localizadas en root Z y AreaTable/WMOAreaTable localizadas en los Z de idioma.
Respetar el resto de la propiedad descrita en el
[README de distribución](../../client_patches/README.md), sin duplicar tablas
de mayor prioridad que oculten traducciones. HD exige su propio contrato: no
trasplantar el perfil regular para simular paridad.

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
- El TRS335 almacena el nombre físico en40 bytes: como máximo39 caracteres más
  NUL. Los nuevos recursos regionales usan `sha256[:32].blp` (36 caracteres),
  con detección de colisiones y hash completo en evidencia. `dir:` no crea scope
  nativo. Un lookup Python que acepta74 caracteres no prueba que el juego lo haga.
- El lookup de minimapa WMO elimina los primeros6 caracteres del path de forma
  incondicional y usa **índice de grupo**, no GroupID. Derivar la clave del
  contrato real incluso con namespaces no `World\`; conservar mappings ajenos.
- Si no existe arte interior, demostrar equivalencia de geometría/grid antes de
  reutilizar otra imagen. Compartir GroupID o dimensiones BLP no basta. La
  alternativa implementada genera planos simplificados desde suelos WMO fijados
  por hash/materiales:2px/unidad local, origen bbox.minXY, padding transparente y
  sin estirar. Son cartografía estática, no pisos dinámicos ni artwork original.
- El hover/clic continental requiere el `.zmp` correspondiente al token del
  continente: matriz128×128 uint32 little-endian de **AreaTable IDs**, no IDs
  WorldMapArea. Highlights BLP y overlays no reemplazan esa máscara. Fusionar
  únicamente celdas regionales auditadas; el ejemplo High Elf porta44 y conserva
  dos celdas de Plaguelands. El resto debe permanecer byteexacto. No reemplazar
  el arte continental completo ni FrameXML para resolver un dato ausente.
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

### Continente compartido: extracción regional no implica VMap local

Preparar un cliente de extracción derivado: archivos oficiales permitidos,
copias privadas de los MPQ integrados y overrides DBC de la baseline servidor.
T-last no garantiza que el extractor vea los Z de idioma del juego. Un Map.dbc
recortado o WDT de selección puede acelerar Maps, pero es **solo para extraer**;
no instalar esos recortes sobre el cliente o servidor completos.

Al ensamblar VMaps de un continente, usar WDT completo y desplegar el árbol nuevo
con **todos sus tiles coordinados**, no solo los del delta. Los índices de nodos
son globales a la asamblea. Cerrar todos los modelos realmente nombrados por
esos tiles, incluidos los binarios servidor `.m2` con cabecera VMAP_4.8 cuando
el nombre serializado termina en NUL: un glob `*.vmo` es insuficiente.

Generar navegación sobre Maps/VMaps coordinados, tiles modificados y halo
cardinal, fijando también las dependencias de los strips vecinos. Distinguir un
tile legítimamente vacío de un fallo sin salida. Antes de retener MMaps nativos,
comparar origen, dimensiones, coordenadas únicas y capacidad de tiles/polígonos
de Detour. No sustituir parámetros incompatibles solo porque el header sea válido.
En el wrapper High Elf, ADT `(X,Y)` usa `--tile X,Y`, nombres Maps/MMaps `000YYXX`
y VMaps `000_XX_YY`; comprobar la convención de cada API en vez de intercambiar ejes.

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

El flujo High Elf preserva la entrega con `stage_high_elf_server_data.py` en el
manifiesto existente schema2: replacements contra preimágenes reconocidas, todos
los donantes DBC ordenados, fullset VMap/modelos y dependencias del halo. No crear
otro instalador. Conservar fuentes/manifiesto anteriores fuera del árbol activo
antes de cambiarlo; para otro mapa habrá que adaptar y probar ese contrato.

La instalación requiere servidor parado y acceso exclusivo. Hay escritura
atómica **por archivo** con journal/backups, no un swap simultáneo del DataDir;
SQL y archivos tampoco forman una transacción. Mismo manifiesto usa su estado
propio; manifiesto cambiado exige estado nuevo. Conservar estados anteriores
con sus fuentes/manifiestos, sin editar diarios para saltar guards. Tras una
interrupción, `recover` revierte el conjunto, no continúa la copia. Procedimiento
canónico y separación de rollback SQL/archivos: [deployment.md](deployment.md).

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
desde los dos clientes originales. La cadena alto elfo tiene su propio archivo
durable/source lock y fixtures húmedos; no convierte esta cadena histórica r1–r5
en un bootstrap genérico de toda la geografía Turtle.

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

## 12. Cadena High Elf: herramientas reutilizables y entradas reales

Esta es una referencia de interfaces, **no un script para importar una zona
desconocida ni para regenerar encima del cliente validado**. Los JSON High Elf
contienen selecciones, IDs y hashes propios: otra región necesita su contrato,
fixtures y auditoría, no un cambio de nombre en los comandos.

### Del snapshot al staging

| Etapa | Herramientas/contrato | Entrada que debe existir | Salida y condición de avance |
|---|---|---|---|
| Inventario y perímetro | `mpq`, `adt.py`, auditoría regional | Snapshots, prioridad efectiva, extracciones por nombre | Selección explícita de MCNK y vecinos, hashes y conflictos resueltos |
| Composición | `high_elf_terrain.py`, `high-elf-terrain-selection.json` | `RESEARCH/{335,turtle}/World/Maps/Azeroth`, WDT, mapa de áreas y auditoría global UID | ADT nuevos; bordes, referencias, framing y remaps comprobados |
| Recursos | `high_elf_map_assets.py`, política WMO y convertidor M2 | Terreno previo, snapshots y convertidor validado | `files/` y manifiesto sin dependencias ni semánticas bloqueadas |
| Metadata | `high_elf_map_dbc.py`, `high-elf-map.json` | DBC fuente fijadas, baselines independientes y overlays DEV inspeccionables | Deltas compactos; merge sin pérdida e idempotente |
| Cartografía/ambiente | `high_elf_map_cartography.py` | Assets, terreno, deltas anteriores, artwork/TRS/ZMP y baselines | Imágenes y DBC coordinadas; `--strict` sin faltantes |
| Interiores generados | `high_elf_interior_minimaps.py` | Plan de suelos y assets con hashes compatibles | Integrado por cartografía; no es otro parche adicional |

Ejemplos con variables que representan **rutas ya elegidas y auditadas**:

```sh
python3 tools/high_elf_terrain.py \
  --research "$RESEARCH" --selection "$SELECTION_JSON" \
  --native-client "$CLIENT_335" --source-client "$CLIENT_TURTLE" \
  --output "$TERRAIN"

python3 tools/high_elf_map_assets.py \
  --terrain "$TERRAIN" --research "$RESEARCH" \
  --source "$CLIENT_TURTLE" --native "$CLIENT_335" \
  --dotnet "$DOTNET" --converter "$CONVERTER_DLL" --output "$ASSETS"

python3 tools/high_elf_map_dbc.py \
  --config "$CONFIG_JSON" --login-path azeroth-dev --output "$DBC_STAGE"

python3 tools/high_elf_map_cartography.py \
  --config "$CONFIG_JSON" --terrain "$TERRAIN" --assets "$ASSETS" \
  --dbc "$DBC_STAGE" --source "$CLIENT_TURTLE" --native "$CLIENT_335" \
  --output "$CARTOGRAPHY" --strict
```

`CONFIG_JSON` sigue controlando directorios fuente, servidor, regular y assets:
`--output` **no relocaliza las entradas**. El comando DBC consulta overlays en
lectura y rechaza filas incompatibles; sobre una DEV ya integrada no convertir
un fallo de ownership en autorización para sobrescribir. Recuperar baselines
pre-región verificadas o diseñar una migración explícita de la fila propia.
El convertidor se construye/valida con `DOTNET=... scripts/build-new-races-model-converter.sh`
y su modo `--validate`; no quitar guards para reutilizar un binario obsoleto.

### Del staging al archivo cliente durable

```sh
python3 tools/package_high_elf_map.py --capture \
  --assets "$ASSETS" --terrain "$TERRAIN" --cartography "$CARTOGRAPHY"
```

La captura exige que el destino durable activo **no exista**. En una actualización,
preservar primero la fuente anterior y su lock como una edición independiente;
`--baseline-source "$PREVIOUS_SOURCE" --baseline-source-sha256 "$PREVIOUS_LOCK_SHA256"`
permite recuperar sus baselines nativas verificadas. No borrar la fuente anterior
para que el comando pase ni tomar tablas ya integradas como base pre-región.
Verificar los cambios byte a byte, capturar y fijar explícitamente el nuevo
source-lock hash en el hook. Ni el lock histórico de la consolidación ni sus
fuentes se refreezean para ocultar diferencias.

Con el archivo durable completo, el rebuild normal ya no abre los paths de
`work/` de la evidencia regional:

```sh
# TMPDIR debe existir, tener espacio y estar destinado a este trabajo.
export TMPDIR="$TMP_STAGE"
"$IMAGE_PY" tools/consolidate_client_patches.py \
  --output "$CLIENT_STAGE" --reproducible
"$IMAGE_PY" tools/consolidate_client_patches.py --verify "$CLIENT_STAGE" --publish
```

`--publish` cambia la distribución local del repositorio, no el cliente del
usuario. Exigir dos builds idénticos, readback de todos los miembros, allowlist,
ownership DBC, hashes y conservación de S/HD/cripta/otras personalizaciones según
el delta autorizado. La copia al juego permanece manual y con WoW cerrado.

### Generación, preservación e instalación servidor

```sh
python3 tools/build_high_elf_server_data.py all \
  --output "$SERVER_BUILD" --terrain "$TERRAIN" --assets "$ASSETS" \
  --stock "$CLIENT_335" --client client_patches/regular_client \
  --server /home/dev/azerothcore/env/dist/bin --jobs 2

python3 tools/stage_high_elf_server_data.py \
  --build "$SERVER_BUILD" --manifest data/server/manifest.json \
  --recovery "$PREVIOUS_SERVER_SOURCE_TREE"

scripts/apply-db-world.sh --validate --with-server-data
```

El wrapper usa `prepare|geometry|locales|navigation|report|all`. En una actualización
puede necesitar `--previous-manifest` con la fuente anterior fijada; cambiar la
revisión de un wrapper con cache exige inspección antes de
`--reuse-previous-wrapper`. No reutilizar un éxito cacheado con otros inputs.
El staging preserva fuentes/datos y recuperación, **no instala**. Instalación,
parada, preflight, reaplicación y recuperación usan [el flujo existente](deployment.md).
Si la reextracción demuestra igualdad completa, no reinstalar ni reiniciar por
analogía; documentar qué datos se compararon. No se añade SQL para estas
correcciones geográficas High Elf.

### Pruebas escalonadas

1. Tests puros de estructuras, referencias, datos negativos, DBC y packaging.
2. [Scanner x86](../../tools/probe_adt_client.md) con EXE cuyo código coincida
   con el pin: `--adt-dir`, `--exe`, `--output`; opcional `--mpq` para comprobar
   lo **publicado**, no solo el staging.
3. `build_high_elf_nav_probe.py --runtime "$DATADIR" --source "$SOURCE_ADT_DIRECTORY" --output "$PROBE_STAGE"`:
   compila contra objetos/bibliotecas nativos existentes. Tiene inventario y
   cobertura High Elf específicos; adaptarlos para otra región y leer su ayuda.
   Separar carga, altura/LoS, corredor completo, parcial y destino ausente.
4. Cliente real en instalación/prefix aislados, perfiles y hashes medidos, cuenta
   y personaje de prueba propios. No ejecutar un viejo `prepare/cleanup` contra
   un clon/prefix compartido; conservar evidencias previas y cerrar solo procesos
   propios. Comprobar XYZ reales, altura, cámara y flags cuando una captura sea
   ambigua. No exigir al usuario que ejecute primero la investigación rutinaria.

## 13. Diagnóstico que debe quedar como regresión

| Síntoma | Causa demostrada / comprobación | Reparación y control negativo |
|---|---|---|
| Error132 al cargar, lectura en `0x007C3A42` | MCLQ físico retenido con tamaño propio0 después de borrar su extensión legacy | Normalizar extensión verificada antes de desactivar; ejecutar parser nativo sobre MPQ y probar carga completa. No parchear EXE ni borrar agua |
| Natación aérea, rojo y partículas dentro de un bbox | Semántica WMO15 con `MOHD.flags & 0x4` produce magma sin grid | Política acotada de familias secas por hash; A/B a igual XY/Z, suelo/aire sin SWIMMING y mar legítimo aún nadable. No deducir el cambio servidor |
| Minimapa exterior verde aunque el fichero existe | Nombre TRS largo truncado por cliente a39 caracteres | Nombre corto con colisión comprobada; probar ruta efectivamente formada, imagen visible y movimiento |
| Minimapa interior negro | Prefijo WMO incorrecto, arte ausente o grid no equivalente | Clave derivada del path cliente; usar arte equivalente demostrado o plano real. Caminar y comprobar punto/alineación, no solo píxeles no negros |
| Región aparece en la lista pero no se puede clicar | No existe AreaTable ID en la máscara continental `.zmp` | Merge mínimo con bordes nativos preservados; hover y clic izquierdo reales, retorno al continente y controles vecinos |
| Interior sigue mostrando otra área | Clave exacta root/nameSet/group no coincide; group−1 no es fallback | Contrastar MOHD/MODF/MOGP con WMOAreaTable; migrar fila propia guardada, sin tocar área nativa ajena |
| Follower se para o tile no aparece con exit0 | Mesh ausente, simplificación, corredor parcial, halo o parámetros incompatibles | Confirmar salida física y lectores nativos; no convertir un parcial en PASS ni importar un perfil local de otra región |
| Hash de miembro MPQ no coincide | Deriva real, prioridad distinta o extracción/escritura truncada | Comprobar archivo efectivo, tamaños y espacio antes de cambiar pins. Mantener expected hashes originales mientras se investiga |

Un mock, un parser Python que comparte código con el productor o un test que
solo enumera nombres no es oráculo independiente suficiente. Aislar la variable
en A/B, conservar muestras fallidas y probar también el comportamiento legítimo
que la corrección podría eliminar. Si el resultado es solo inferido, decirlo.

## 14. Criterio de cierre de una región

- Contrato regional e IDs auditados, adaptaciones y límites explícitos; no hay
  pérdida silenciosa de WotLK ni regresión de contenido propio aceptado.
- Terreno, agua y assets cerrados; no markers, referencias faltantes, semánticas
  no soportadas presentadas como compatibles ni UID conflictivos sin resolver.
- Cartografía funcional: exterior/interior pertinente, punto y escala al moverse,
  mapa regional, hover/clic continental, idioma y loading/acceso cuando apliquen.
- Paquete reproducible desde fuentes durables con inventarios/locks y rollback;
  no depende para instalarse de un scratch o PNG manual que se ha perdido.
- Servidor coordinado, cierre de modelos/árbol/tiles y halo, instalación y
  reaplicación comprobadas; rollback/recover en fixture y arranque si se desplegó.
- Cliente real con controles secos/húmedos e interiores/exteriores, visitas a
  los límites de los defectos reparados y regresiones nativas/previas pertinentes.
- Revisión independiente, hallazgos materiales corregidos y revalidación.
- Resultado por comprobación: **PASS / FAIL / NOT RUN / NOT APPLICABLE / BLOCKED**.
  Diferenciar agente, usuario y pruebas offline; no certificar todos los pisos,
  rutas, HD o gameplay por una visita puntual. Guardar evidencia local, pero
  llevar a conocimiento durable solo contratos y hechos reutilizables, no un
  diario de comandos ni el estado Git del día.

Este cierre es geográfico. NPC, quests, loot, objetos, hechizos, transportes
scriptados y activación de razas nuevas requieren contratos/migraciones propios;
no se consideran importados por estar presentes sus edificios o mapas.
