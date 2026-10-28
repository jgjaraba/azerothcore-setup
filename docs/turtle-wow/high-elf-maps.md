# Altos Elfos — geografía de mapa0

Contrato del port geográfico de **Highlands (área5225) y Alah'Thalas
(área2040)** del snapshot Turtle a AzerothCore/WotLK335. Es una ampliación del
continente nativo mapa0, no un mapa independiente ni la activación servidor de
la raza22. No añade SQL, NPC, quests ni zonas iniciales de razas jugables.

## Fuentes y reconstrucción

- `tools/high-elf-map.json`: asignaciones DBC; `tools/high-elf-terrain-selection.json`:
  selección explícita del compositor. No interpretar un bounding box de mapa como
  permiso para reemplazar todos sus ADT.
- `tools/high_elf_map_dbc.py`, `high_elf_terrain.py`, `high_elf_map_assets.py` y
  `high_elf_map_cartography.py`: traducción/merge de DBC, terreno, recursos y
  cartografía respectivamente; los paths de herramientas son relativos a `tools/`.
- [`client_patches/archive/source-inputs/high-elf-map/`](../../client_patches/archive/source-inputs/high-elf-map/README.md):
  payload compartido, baselines independientes, deltas relocalizables, resultados
  esperados y manifiestos de evidencia. `source-lock.json` fija SHA256/tamaños y
  está a su vez fijado por `tools/package_high_elf_map.py`.
- El hook de `tools/consolidate_client_patches.py` reconstruye primero la base
  histórica y aplica después las ediciones declaradas. Los paths de `work/` en
  evidencia son procedencia, no dependencias que el hook normal deba abrir.
  Reconstruir desde snapshots originales sigue requiriendo esos inputs y las
  herramientas de conversión; no equivale a reconstruir desde el archivo durable.
- [`high-elf-server-data.md`](high-elf-server-data.md) posee la extracción, el
  cierre servidor y la instalación por el manifiesto existente.

## Terreno y agua

El compositor conserva **24 tiles**, con **3899 celdas fuente y2245 nativas**
(MCNK). Preserva WDT y geografía335 ajena a la selección. El tile `33_22` es
nativo sin delta geográfico: su reserialización no justifica desplegar un
`.map` distinto. El servidor instala23 Maps regionales.

Las capas residuales erróneas del terreno nuevo de origen se retiran mediante
selección explícita; no es una limpieza global de texturas. Se conserva el
**MH2O ya presente en la fuente** como autoridad de agua y se desactiva el MCLQ
duplicado correspondiente. Esto no requiere ni demuestra un conversor general
MCLQ→MH2O. El layout MHDR de parser/serializador está corregido; véase
[compatibilidad](compatibility.md).

Desactivar flags y offsets no retira el bloque físico MCLQ: el cliente335 recorre
los subchunks MCNK secuencialmente. Antes de desactivar el líquido legacy se
normaliza **su propio tamaño** a partir del offset y tamaño todavía activos,
verificados contra los límites y referencias de la celda. El payload no cambia.
Un MCLQ retenido con tamaño interno0 y `sizeLiquid=0` hace que el cliente interprete
agua opaca como cabeceras y puede fallar en `0x007C3A42`. `tools/adt_client.py`
valida ese recorrido; `tools/probe_adt_client.py` ejecuta la rutina x86 fijada por
hash para contrastarlo, sin sustituir la prueba del renderizador completo.

La comprobación estructural de costuras examinó **12464 bordes** y no encontró
regresiones nuevas en las comparaciones disponibles; **16 carecen de baseline**
y no se consideran una comparación superada. No demuestra continuidad visual
ni recorrido en juego.

## Identidad y dependencias

- Las áreas fuente3881–3883 se remapean a6500–6502. Se preservan las áreas
  originales de Outland; padres, MCNK y referencias nuevas deben usar el remap.
- Se añaden22 áreas y18 filas WMOAreaTable para las familias custom. Las13
  claves WMO heredadas de root4772/nameSet1 permanecen nativas, no se reinterpretan
  como áreas de mapa0. Asignaciones completas en
  [registro de IDs](id-mappings.md#altos-elfos-en-mapa0).
- Los recursos nuevos incluyen **4 modelos de props y20 WMO**. Los namespaces
  aislados evitan reemplazos globales de modelos nativos. Cerrar referencias de
  modelos, grupos, materiales y texturas sigue siendo obligatorio.
- `high1elf_inn` tiene MOHD root6002, MODF nameSet0 y MOGP group0.
  El mapping explícito fuente50334→60017 traduce group19746→0; fuente50333→60016
  conserva group−1. El lookup de WMOAreaTable es exacto: group−1 **no** cubre
  una consulta de group0. Builder, cartografía y captura validan las claves
  colocadas contra ADT/WMO fijados por el manifiesto final de assets. Se conserva
  metadata fuente de grupos no colocados (p. ej.60014), sin inventar filas para
  grupos colocados que no tenían metadata fuente.
- El conversor de modelos tiene validación estructural de los **10 emisores de
  partículas del árbol**, contrastados con OracleTree nativo. No es una validación del renderizador ni
  una garantía universal de fidelidad M2.

### Líquidos de edificios WMO

Quince familias fuente tienen `MOHD.flags & 0x4` y sus27 grupos conservan
`MOGP.liquidType=15`, sin MLIQ ni flag de líquido. El cliente335 interpreta esa
combinación como19 (WMO Magma), incluyendo consultas de volumen sin grid.
La referencia nativa de las casas usa el sentinel legacy15 con el bit0x4 apagado.
`tools/high-elf-wmo-liquids.json` fija las quince familias y sus grupos por
identidad/hash; el builder comprueba que todos son secos y limpia **solo ese bit
del root**. Conserva geometría, bounds, grupos, materiales, MFOG y todo el terreno
MH2O/MCLQ. No es una política general de borrar agua donde falta MLIQ: los
volúmenes legítimos sin grid requieren conservar su semántica.

Los casos reproducidos son el muelle `highelfdock`, en
`4558.568,-2869.236`, y `highelfhousevariantf`, en `3167.174,-2422.720`.
El efecto anterior ocupaba sus bounds hasta Z42.625 y171.601 respectivamente.
La comparación cliente real antes/después confirmó el fin de la natación aérea
y del velo rojo; el control de mar con agua Z0 siguió siendo nadable y azul.

La reextracción completa con los binarios instalados produjo los mismos Maps,
VMaps y MMaps anteriores, por lo que esta entrega no modifica servidor ni SQL.
No se debe deducir el resultado del extractor solo por el contrato cliente:
los modelos servidor inspeccionados ya carecían de WmoLiquid en esos27 grupos.

## Entrega coordinada

La geografía se publica en el **perfil regular** consolidado: T contiene
**316 miembros sin DBC**; root Z queda con28 miembros y cada locale Z (enUS/esES)
con6. Son totales finales, no el número de miembros añadidos por el port.
AreaTable/WMOAreaTable residen en locale Z;
WorldMapArea/WorldMapOverlay, en root Z. Las demás tablas/recursos cartográficos
siguen la propiedad declarada en el source lock. El TRS completo conserva las
asignaciones nativas y de la cripta fuera de la lista regional explícita.

S, el launcher y el perfil HD se conservan sin cambios por esta ampliación.
El cliente se copia manualmente según el
[README vigente](../../client_patches/README.md); no instalar el archivo de
fuentes como otro perfil ni superponer antiguos paquetes r5 al consolidado.

El servidor usa el manifiesto **schema2** existente:23 Maps, árbol mapa0 y sus
374 tiles VMap completos, cierre de2951 modelos (2914 nativos idénticos +37
nuevos),34 MMaps (23 regionales +11 de halo) y parámetros compatibles, más cuatro
deltas DBC aditivos. No copiar solo los VMaps regionales junto al árbol nuevo.

## Cartografía nativa de cliente

- El lector335 guarda el valor físico de `md5translate.trs` en40 bytes: máximo39
  caracteres más terminador. Los recursos regionales usan36 (`sha256[:32].blp`),
  con detección de colisiones y SHA256 completo en el manifiesto. Los BLP de
  origen se conservan byteexactos; las líneas `dir:` no establecen scope nativo.
- El lookup WMO elimina seis caracteres del path antes de formar
  `<prefijo>_<índiceGrupo>_<ix>_<iy>.blp`, incluso para paths `Character\...`.
  Por eso los22 interiores custom usan claves `ter\Custom\HighElfMap\...`.
  Once son imágenes fuente NetherMicro; los once restantes se rasterizan desde
  sus suelos WMO reales mediante `tools/high_elf_interior_minimaps.py` y un plan
  explícito de hashes/materiales, sin aliases de casas de geometría diferente.
  Los57 grupos interiores de recursos nativos conservan su cartografía nativa.
- Los planos nuevos tienen2 píxeles por unidad local, origen en bbox.minXY y
  padding transparente, sin estirar al tamaño del BLP. Son planos simplificados
  estáticos; un grupo con pisos solapados no adquiere selección dinámica por Z.
- El hover/clic continental depende de `Interface\WorldMap\Azeroth.zmp`,
  matriz128×128 de AreaTable IDs uint32 little-endian, no de los IDs WorldMapArea
  ni del BLP highlight. Se componen44 celdas auditadas para2040/5225; las celdas
  fronterizas `(72,52)=28` y `(73,52)=139` conservan sus clics nativos. El resto
  permanece byteexacto. `tools/high-elf-map-clickmask.json` fija esa selección.
  No cambia FrameXML, DBC ni el artwork continental completo.

## Límites de fidelidad y validación

WDL y Light nativos se retienen deliberadamente; no se importa la iluminación
Turtle. El audio se traduce a recursos nativos de Eversong, no a audio Turtle
idéntico. La cartografía2D/minimapa combina fuentes y puede diferir del terreno
compuesto. No se afirma fidelidad total.

La publicación de archivos, generación estructural y aplicación/reaplicación
servidor están comprobadas en su ámbito; la evidencia de ejecución se mantiene
en [validation.md](validation.md#altos-elfos-mapa0--alcance-de-la-evidencia).
El probe `tools/build_high_elf_nav_probe.py` carga los datos instalados mediante
los lectores nativos GridTerrainData/VMap/Detour y permite comprobar altura,
rayos y corredores **offline**. Sus resultados acotados están en la sección de
evidencia enlazada; un corredor parcial o un destino sin polígono no se convierte
en éxito por haber cargado el archivo.

Una comprobación puntual con cliente real enUS/Wine/D3D9 cargó ambos destinos
indicados abajo, dibujó el entorno y permaneció responsive durante60 segundos
en cada uno, sin Error132. Es cobertura de carga limitada, no aceptación completa:
**agua, alineación cartográfica, LoS, navegación y gameplay en juego siguen sin
validación exhaustiva.** Las comprobaciones posteriores corrigieron los líquidos
falsos y el minimapa verde/negro. En cliente real enUS/Wine se comprobaron movimiento
y minimapa exterior en Alah/Brinthilien, plano de HouseVariantF y mapa de la mina;
hover/clic nativos abren ambas regiones desde el continente. La cobertura no
equivale a recorrer cada grupo/piso ni a probar todos los clientes/addons.

### Puntos para exploración manual

Con el cliente regular actualizado, estos puntos tienen suelo medido por el
lector nativo, polígono NAV_GROUND y espacio vertical libre en la comprobación
offline. La Z del comando incluye dos unidades de margen. No son puntos de
aparición racial ni una aceptación en juego:

```text
# Brinthilien
.go xyz 3122.13330 -2479.13330 115.34452 0

# Alah'Thalas
.go xyz 4275.35986 -2761.38647 8.66027 0
```
