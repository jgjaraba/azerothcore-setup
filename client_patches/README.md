# Parches de cliente consolidados

Esta es la entrada de instalación. **No copiar todo `client_patches/` al juego.**
Los únicos perfiles de instalación son `regular_client/` y `hd_client/`.
`archive/` nunca se instala ni participa en la selección automática de fuentes.

## Alcance de las dos versiones

| Función | Regular | HD conservador |
|---|---|---|
| Datos históricos de objetos, clases, talentos y displays | Sí | Sí, conservando sus tablas HD |
| Dark Rider | Textura regular | Textura HD propia |
| Costes de vendedores personalizados | Sí | Sí, con 52 filas adicionales |
| Spell enUS / esES | Tablas originales completas | Tablas originales completas |
| Personalizaciones principales Troll/Tauren | Sí | No integradas |
| Karazhan Crypt r5 | Sí | No integrado |
| Mapa Alto Elfo Map0 (Thalassian Highlands / Alah'Thalas) | Sí, integración geográfica offline | No integrado |
| Alto Elfo/Goblin e interfaz de doce razas | Preview cliente | No integrado |
| Skins opcionales de cara fija/parciales | **Excluidas** | **Excluidas** |

**HD no tiene paridad completa con regular.** Su Z histórico necesita una tabla
`CreatureModelData.dbc` del cliente HD original que no está entre los recursos
disponibles. Reemplazarla por la regular dejaría 1.734 displays históricos con
192 ModelID inexistentes. Por eso el perfil HD conserva su dependencia original
y no instala una tabla de modelos regular, modelos Tauren clásicos ni nuevas
apariencias. Tampoco instala el launcher de nuevas razas.

La integración completa HD requiere las tablas efectivas y los modelos, SKIN,
animaciones y texturas de **ese mismo cliente HD**. No se han inventado aliases
ni sustituido sus mappings por otros de apariencia similar.

## Instalación manual

1. Cerrar WoW. Trabajar sobre una copia del cliente correspondiente.
2. Guardar los parches personalizados anteriores **fuera de `Data/`**, anotando
   los destinos que antes no existían. No borrar los MPQ oficiales ni los recursos
   originales del cliente HD. Si hay otros mods, reconciliarlos antes: esta entrega
   no fusiona automáticamente cualquier cadena de parches ajena.
3. Elegir **un solo perfil** y copiar sus archivos conservando las rutas:

```text
regular_client/                       hd_client/
  Wow-new-races.exe                     Data/
  Data/                                  patch-Z.mpq
    patch-S.MPQ                          enUS/patch-enUS-Z.MPQ
    patch-T.MPQ                          esES/patch-esES-Z.MPQ
    patch-Z.mpq
    enUS/patch-enUS-Z.MPQ
    esES/patch-esES-Z.MPQ
```

4. Instalar el Z de **la locale utilizada**. Ambos idiomas se distribuyen, pero
   `enUS` no sustituye a `esES` ni viceversa; usar el directorio que corresponda.
5. En regular, reemplazar S/T/Z y el Z localizado **como conjunto**. El nuevo S
   contiene recursos de nuevas razas que no estaban en el antiguo S principal.
   Lanzar `Wow-new-races.exe`, no el ejecutable original. En HD conservar su
   ejecutable compatible habitual; no copiar el launcher regular.

No instalar además ningún archivo de `archive/`. Las antiguas rutas fuente
`Data/`, `new-races/`, `turtle_crypt/`, `turtle_forest_troll/` y los Z sueltos de
idioma no son capas adicionales que deban restaurarse junto al cliente.
No dejar duplicados que solo cambien en mayúsculas/minúsculas.

Reversión: con WoW cerrado, restaurar el conjunto respaldado y retirar únicamente
los archivos nuevos de esta instalación. Esta consolidación no modifica SQL,
el servidor ni las apariencias guardadas de personajes. Un personaje que ya use
skins opcionales sigue necesitando su cliente antiguo compatible; no se remapea
automáticamente a una opción principal.

## Inventario por parche

Los recuentos excluyen metadatos internos del MPQ. El inventario **archivo por
archivo**, con nombre, tamaño, SHA-256, categoría y procedencia, está en
[`inventory.json`](inventory.json). Los cambios de registros DBC, dependencias y
límites están en [`validation.json`](validation.json).

### Regular

| Parche | Miembros | Contenido |
|---|---:|---|
| `Data/patch-S.MPQ` | **888** | Recursos de personajes: 872 BLP, 6 M2 y 10 SKIN. Personalizaciones principales Forest/Troll/Tauren, geometría Tauren aceptada y los modelos/texturas aislados de Alto Elfo y Goblin. Incluye la corrección paletizada de las 44 texturas. **Sin DBC ni looks opcionales.** |
| `Data/patch-T.MPQ` | **316** | Geografía de Karazhan Crypt r5 y mapa Alto Elfo Map0: 24 ADT regionales, dependencias aisladas, worldmap, overlays, minimapas exteriores/interiores y máscara de clic continental. Se conservan los recursos previos de la cripta. **Sin DBC.** |
| `Data/patch-Z.mpq` | **28** | 15 DBC no localizadas; interfaz de nuevas razas e iconos; recursos visuales/música del login regular y textura Dark Rider. |
| `Data/enUS/patch-enUS-Z.MPQ` | **6** | `ChrRaces`, `Map`, `AreaTable`, `MapDifficulty`, `Spell` y `WMOAreaTable`, con nombres/textos ingleses y las filas personalizadas correspondientes. |
| `Data/esES/patch-esES-Z.MPQ` | **6** | Las mismas seis tablas, con nombres/textos españoles/fallback fuente en las nuevas filas. Spell mantiene íntegra su edición española. |

Las 15 tablas de root Z son:

```text
AreaTrigger                    CharacterFacialHairStyles
CharBaseInfo                   CharHairGeosets
CharSections                   CharStartOutfit
CreatureDisplayInfo            CreatureDisplayInfoExtra
CreatureModelData              Item
ItemExtendedCost               LoadingScreens
Talent                         WorldMapArea
WorldMapOverlay
```

Las tablas localizadas **no se duplican en root Z**: en la cadena probada, esa
duplicación ocultaba las tablas locales. La reconstrucción conserva los tokens
de archivo y campos numéricos de ChrRaces, no solo sus nombres visibles.
El root Z incluye el selector de ojos1702 de Alto Elfo:22 campos de
`CharacterFacialHairStyles`. El S regular normaliza además todas las claves de
opacidad de la pista exclusiva de ojos1 a **6553/32767 (~20%)**, igual al valor
nativo Blood Elf, en ambos sexos. Esta normalización cambia solo los valores de
esa pista en los dos M2 de Alto Elfo; geometría, UV, texturas y materiales se
conservan. Si ya se instaló el selector corregido, actualizar únicamente
`Data/patch-S.MPQ` con WoW cerrado. Desde una entrega sin selector, actualizar
también root Z. La comparación visual nativa bajo Wine/Direct3D9 confirma un
brillo más discreto en ambos sexos, con apariencia y orientación coincidentes y
controles Blood Elf; no equivale a aceptación exhaustiva de equipo/animaciones.
Spell conserva todos los cambios heredados de cada edición, no únicamente los
IDs 90000/90001; sus cuatro diferencias heredadas de campos entre idiomas en el
ID5 se registran, no se corrigen de forma incidental.

### Mapa Alto Elfo integrado en regular

El mapa se integra sobre la consolidación regular anterior. **T es el único
propietario de los recursos geográficos compartidos y no contiene DBC**, incluidos
los modelos aislados bajo `Character/Custom/HighElfMap/`. Esos nombres no convierten
los modelos de edificios/terreno en recursos de skins ni los trasladan a S.
`AreaTable` y `WMOAreaTable` (que contiene nombres localizados) pertenecen a **ambos
Z de idioma**; `WorldMapArea` y `WorldMapOverlay` pertenecen a root Z. Se distribuyen
tablas completas reconstruidas, nunca los pequeños DBC delta como tablas cliente.

La fuente durable es [`archive/source-inputs/high-elf-map/`](archive/source-inputs/high-elf-map/).
Su `source-lock.json`, fijado por SHA-256 en `tools/package_high_elf_map.py`, enumera
recursos, baselines independientes, deltas, resultados esperados, diffs de filas y
manifiestos de procedencia. Los manifiestos completos de terreno, assets y
cartografía vigentes quedan en `evidence/`, incluyendo las correcciones de
carga, líquidos y selección/minimapas. No se reconstruye desde candidatos antiguos.
Las rutas `work/` de esa evidencia son históricas:
la construcción y el `--verify` normales no las abren ni consultan los builders.
El hook reconstruye primero la entrega anterior y exige **todos los hashes
históricos originales**, sin refreeze ni modificación del lock anterior. Después
aplica únicamente las ediciones geográficas enumeradas. Todos los miembros previos
no editados permanecen byteexact; S, launcher, skins, nuevas razas y HD conservan
su contrato previo. El TRS completo conserva los mappings de la cripta y todos
los mappings nativos fuera de los cambios regionales explícitos.

La validación offline no demuestra el render ni la alineación in-game del mapa,
el punto del jugador, pisos WMO, ambiente o gameplay. Se mantienen iluminación
nativa y audio nativo verificado/fallback Eversong; no se importa música Turtle
ni se sustituye el WDL continental. El minimapa 2D de los tiles mixtos puede
mostrar celdas retenidas con diferencias. Consultar los límites de la fuente y
`validation.json`. El packaging no instala nada en el snapshot real del usuario.

`Wow-new-races.exe` se distribuye fuera de los MPQ. Es el derivado ya utilizado,
con caché ampliada y aceptación acotada de GlueXML local. **Las razas 22/23 siguen
siendo una previsualización: esta entrega no habilita su creación/guardado/login
ni sus zonas iniciales, estadísticas o raciales en el servidor.**

### HD conservador

| Parche | Miembros | Contenido |
|---|---:|---|
| `Data/patch-Z.mpq` | **8** | `CharBaseInfo`, `CharStartOutfit`, `CreatureDisplayInfo`, `CreatureDisplayInfoExtra`, `Item`, `ItemExtendedCost`, `Talent` y Dark Rider HD. Siete miembros idénticos al Z HD histórico; en costes, solo se añaden 98010–98035 y 99010–99035. |
| `Data/enUS/patch-enUS-Z.MPQ` | **1** | Spell inglés original completo: 49.841 registros. |
| `Data/esES/patch-esES-Z.MPQ` | **1** | Spell español original completo: 49.841 registros. |

No se instalan S, T ni un `CreatureModelData` de reemplazo en este perfil.

## Archivo y fuentes

Las ediciones incompletas/parciales y candidatos históricos que las contienen
están excluidos y conservados íntegros en:

```text
archive/optional-extra-skins/
archive/new-races/optional-extra-skins/
archive/turtle_forest_troll/optional-extra-skins/
archive/turtle_forest_troll/face-format-test/
archive/turtle_forest_troll/v2/
```

[`archive/relocations.json`](archive/relocations.json) identifica los traslados y
hashes de sus archivos. `archive/baselines/` conserva los Z regular y HD anteriores
como fuentes, no como alternativas de instalación. Las demás entradas necesarias
para reconstruir la consolidación están en `archive/source-inputs/`, con hashes
y procedencia en [`recovery.json`](archive/source-inputs/recovery.json).
El constructor usa una lista explícita de entradas, **no un glob de todos los
MPQ**. Las ediciones parciales archivadas siguen excluidas del plan.

El S principal anterior se conserva en
`archive/source-inputs/Data/patch-S.MPQ`. La base Troll principal también está
archivada en `archive/source-inputs/turtle_forest_troll/`. No confundir esas
entradas históricas con el S consolidado de `regular_client/`.

El lock separa la **identidad lógica** de cada fuente de su **ruta física** en
archive. Los nombres antiguos en el inventario expresan procedencia, no rutas
activas que haya que recrear. El verificador exige los hashes fijados y no busca
alternativas en las antiguas carpetas ni en `work/`. Mantener estas fuentes bajo
control de versiones: borrar una entrada porque ya no se instala rompe la
reconstrucción, aunque los MPQ finales sigan funcionando.

## Reconstrucción y comprobación

### Actualización de cartografía, carga y líquidos de la región

Si ya está instalado el conjunto Alto Elfo actual, con WoW cerrado basta
reemplazar **`regular_client/Data/patch-T.MPQ`**. La entrega acumula la corrección
del tamaño interno de bloques MCLQ inactivos (Error132) y la interpretación de
«sin líquido» en quince edificios WMO (natación en aire y efecto rojo de magma).
Incluye además el minimapa exterior, los interiores y el clic desde Reinos del
Este. No cambia tablas, S ni ejecutable; la reextracción servidor resultó byteidéntica
y no requiere reinstalarlo. Desde una entrega anterior al mapa sigue siendo necesaria la
instalación coordinada descrita arriba.

SHA256 de T corregido:
`491b64ce0df41215d9459736a5ac207cca6f9da0d06d9c27a934bd05f3bc01c0`.

La rutina real del cliente completa las6144 celdas sin lecturas inválidas ni
tags desconocidos. Una prueba enUS/Wine/D3D9 también cargó Brinthilien y
Alah'Thalas durante60 segundos cada una sin Error132. No certifica toda la
región. El minimapa verde de aquella versión está corregido en la entrega actual.

Los dos casos `error_red_*` también se reprodujeron y comprobaron antes/después
en cliente real: muelle de Alah'Thalas y edificio de Brinthilien, sin velo rojo ni
natación en suelo/aire después del cambio. El control de mar legítimo conserva
natación, efecto azul y respiración.

La cartografía usa nombres físicos cortos compatibles con el cliente335, aliases
de mina adaptados a su lookup y once planos de suelos reales para interiores sin
arte de origen. Estos últimos son **planos simplificados**, no artwork Blizzard
ni mapas dinámicos por piso. El hover/clic continental abre Highlands y
Alah'Thalas mediante la máscara nativa; no se reemplazan Lua ni el dibujo completo
de Reinos del Este. Se preservan los clics de las Tierras de la Peste del borde.

### Construcción desde fuentes fijadas

Requiere `tools/mpq`, las entradas fijadas y las dependencias Python del pipeline
de imágenes. Desde la raíz del repositorio, usando ese entorno:

```sh
export TMPDIR="$PWD/work/tmp"
work/new-races-image-venv/bin/python tools/consolidate_client_patches.py \
  --output work/consolidacion-nueva --reproducible
work/new-races-image-venv/bin/python tools/consolidate_client_patches.py \
  --verify client_patches
```

La salida nueva debe estar ausente. Añadir `--publish` al primer comando publica
los perfiles tras construirlos dos veces y verificarlos; conserva respaldo para
rollback durante esa operación. El lock es
[`tools/client-patches-sources.json`](../tools/client-patches-sources.json).
[`checksums.json`](checksums.json) fija los archivos de distribución y los informes.
El verificador comprueba además cada miembro contra su plan y sus fuentes.

Para reconstruir y verificar la entrega exacta **anterior al mapa**, manteniendo
las correcciones de skins/ojos/nuevas razas y cripta ya aceptadas:

```sh
export TMPDIR="$PWD/work/tmp"
work/new-races-image-venv/bin/python tools/consolidate_client_patches.py \
  --native-only --output work/consolidacion-sin-mapa --reproducible
work/new-races-image-venv/bin/python tools/consolidate_client_patches.py \
  --native-only --verify work/consolidacion-sin-mapa
```

Añadir `--publish` al segundo comando revierte la distribución del repositorio
al conjunto verificado anterior. Para volver al mapa, verificar/publicar de nuevo
el staging integrado con el comando normal. Esto no instala ni revierte el cliente
del usuario; la instalación y reversión manual siguen las instrucciones de arriba.

### Validación y límites

- **PASS:** base de 22 pruebas anterior al mapa y 26 pruebas del consolidador integrado;
  dos builds idénticos, lectura posterior
  de los MPQ, contratos DBC, skins principales, exclusión de opcionales y hashes.
- **PASS:** reconstrucción de todos los hashes históricos antes del hook regional;
  22 AreaTable, 18 WMOAreaTable, 2 WorldMapArea y 9 WorldMapOverlay añadidos;
  registros/bloques de strings anteriores byteexact, sin cambios ni bajas de filas;
  T sin DBC, seis tablas por locale Z y cero duplicados localizados en root Z.
- **PASS:** cliente regular real bajo Wine/Direct3D9, enUS y esES: autenticación,
  selección/creación, diez razas originales y textos, Alto Elfo masculino y
  Goblin femenina; 18 posiciones de ciclo piel/cara Goblin y pasos de Alto Elfo.
- **PASS:** comparación visual del brillo de ojos Alto Elfo masculino/femenino
  antes/después, bajo Wine/Direct3D9; cambios muestreados de rasgos, piel/cara y
  transición desde Goblin. No es una prueba exhaustiva de todos los estilos.
- **PASS:** conservación estructural del Z HD histórico y sus dos Spell completos.
- **PASS acotado:** carga y render puntual en Brinthilien y Alah'Thalas con cliente
  real enUS/Wine/D3D9 y T corregido; sin Error132 durante60 segundos por destino.
- **PASS cartografía acotada:** minimapas exteriores, plano interior de casa y
  minimapa de mina visibles durante movimiento real; hover, clic izquierdo y
  retorno al continente para ambas zonas, con controles Tirisfal/Plaguelands.
- **NOT RUN:** alineación y gameplay completo del mapa Alto Elfo, cliente HD real,
  gameplay completo, nueva visita in-game a la cripta,
  prueba exhaustiva de equipo/animaciones y tooltips de hechizos.
- **BLOCKED:** paridad completa HD, por falta de sus bases reales compatibles.

La aceptación del arreglo de texturas por el usuario se conserva; estos checks
adicionales no equivalen a aceptar todas las combinaciones ni habilitar gameplay.
