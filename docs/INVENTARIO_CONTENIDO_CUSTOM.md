# Inventario clasificado del contenido custom de AzerothCore Setup

**Fecha de revisión:** 2 de octubre de 2026.  
**Repositorio:** [jgjaraba/azerothcore-setup](https://github.com/jgjaraba/azerothcore-setup).  
**Rama y versión analizadas:** `main`, commit [`c288958ceb7c`](https://github.com/jgjaraba/azerothcore-setup/commit/c288958ceb7c382f34123fbba6946101879f66c3), fechado el 1 de octubre de 2026 a las 17:40:24 UTC.  
**Ámbito principal:** `data/sql/custom/db_world/`: 18 archivos SQL y `manifest.txt`.

**Nota de vigencia:** el inventario y su sección de manifiesto son una captura
histórica del commit indicado arriba; no describen el inventario operativo
actual. Desde esa captura se añadieron SQL, incluido `reagent_bank_npc.sql`.
El manifiesto vigente y su orden se mantienen en
[`docs/project/components/custom-world-sql.md`](project/components/custom-world-sql.md);
valídalo con `scripts/apply-db-world.sh --validate`.

Este documento inventaría lo que los archivos **definen o modifican**, no certifica que esté instalado en DEV o producción. Se han leído los 18 SQL completos y extraído sus sentencias, identificadores y relaciones. Como comprobación auxiliar se han consultado el instalador, los DBC `Item`/`ItemExtendedCost` versionados y documentación de dependencias. No se ha accedido a la base de datos del servidor, ejecutado los SQL sobre ella ni inspeccionado el contenido de los MPQ.

Los enlaces apuntan al commit analizado para que el inventario pueda reproducirse aunque cambie `main`.

## 1. Resumen del contenido

| Categoría | Contenido definido |
|---|---|
| Equipo de bandas | 4 monedas, 4 vendedores, 428 entradas de venta y recompensas de encuentro en MC/BWL/AQ40/Naxx40. |
| Equipo de mazmorras | 26 monedas, 26 vendedores y 928 entradas de venta; un token en cada jefe final. |
| Transfiguración | 1 moneda propia y recompensas configuradas en mazmorras de nivel alto y bandas clásicas. |
| Paladines Renegados | Combinación inicial no muerto/paladín, 2 instructores, 12 misiones y 5 objetos propios. |
| Guerrero | 1 talento propio, 2 hechizos propios y ajustes a 15 rangos de talentos existentes. |
| Monturas | Requisitos de nivel 30/60 y retirada de cuatro bloqueos de progresión de vendedores. |
| Botín y equilibrio | Aumento de referencias BoE, ajuste de un drop concreto y modificación de cuatro objetos existentes. |

**Totales de entidades propias en estos SQL:** 31 monedas —4 de banda, 26 de mazmorra y 1 de transfiguración—; 36 plantillas de objeto nuevas contando los cinco objetos de paladín; 32 plantillas de NPC nuevas —30 vendedores y 2 instructores—; 12 misiones; 1 talento y 2 hechizos. Los catálogos suman **1.356 entradas de venta** y reutilizan objetos del juego: no equivalen a 1.356 objetos custom nuevos.

### 1.1. Estado del manifiesto

[manifest.txt](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/manifest.txt) incluye **11 de los 18 SQL**. La validación de [scripts/apply-db-world.sh](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/scripts/apply-db-world.sh) exige que todo `.sql` del directorio aparezca exactamente una vez en el manifiesto.

Al ejecutar únicamente `--validate` sobre la copia descargada, el instalador devolvió error y se detuvo **antes de acceder a MySQL**. Los siete archivos ausentes son:

- `dungeon_gear_vendor.sql`
- `dungeon_gear_vendor_npc.sql`
- `dungeon_gear_vendor_item.sql`
- `dungeon_gear_vendor_loot.sql`
- `single_minded_fury.sql`
- `spells_override.sql`
- `rebalance_drop_rate.sql`

Por tanto, **«incluido en el manifiesto» no significa «desplegado»**; además, con este directorio y este manifiesto, el instalador completo no puede avanzar. Una aplicación manual previa es posible, pero queda fuera de esta revisión.

## 2. Índice de archivos

| Categoría | SQL | Contenido | Orden en manifiesto |
|---|---|---|---|
| Equipo y protección frente a mala suerte | [raid_gear_vendor.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/raid_gear_vendor.sql) | 4 monedas propias de MC, BWL, AQ40 y Naxx40. | 5 |
| Equipo y protección frente a mala suerte | [raid_gear_vendor_npc.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/raid_gear_vendor_npc.sql) | 4 Jinetes Oscuros, modelos, diálogos, traducciones y apariciones. | 6 |
| Equipo y protección frente a mala suerte | [raid_gear_vendor_item.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/raid_gear_vendor_item.sql) | 428 entradas de venta en cuatro catálogos de banda. | 7 |
| Equipo y protección frente a mala suerte | [raid_gear_vendor_loot.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/raid_gear_vendor_loot.sql) | Recompensas de moneda de banda en jefes y dos cofres de encuentro. | 8 |
| Equipo y protección frente a mala suerte | [dungeon_gear_vendor.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/dungeon_gear_vendor.sql) | 26 monedas propias de mazmorra o ala. | No incluido |
| Equipo y protección frente a mala suerte | [dungeon_gear_vendor_npc.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/dungeon_gear_vendor_npc.sql) | 26 Jinetes Oscuros, diálogos enUS/esES y posiciones personalizadas. | No incluido |
| Equipo y protección frente a mala suerte | [dungeon_gear_vendor_item.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/dungeon_gear_vendor_item.sql) | 928 entradas de venta, correspondientes a 927 objetos distintos. | No incluido |
| Equipo y protección frente a mala suerte | [dungeon_gear_vendor_loot.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/dungeon_gear_vendor_loot.sql) | Una moneda por jugador elegible, en el jefe final de cada ruta. | No incluido |
| Transfiguración | [transmog_currency_loot.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/transmog_currency_loot.sql) | Marca de Transfiguración y recompensas en contenido de nivel 60. | 11 |
| Paladines Renegados | [forsaken_paladin.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/forsaken_paladin.sql) | Datos iniciales de raza/clase y dos instructores propios. | 3 |
| Paladines Renegados | [forsaken_paladin_quests.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/forsaken_paladin_quests.sql) | 12 misiones de clase y cinco objetos propios. | 4 |
| Guerrero | [single_minded_fury.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/single_minded_fury.sql) | Talento Furia enfilada y aura de bonificación física. | No incluido |
| Guerrero | [spells_override.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/spells_override.sql) | Ampliación del filtro de armas de 15 rangos de especializaciones. | No incluido |
| Monturas y progresión | [ground_riding_override.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/ground_riding_override.sql) | Monturas terrestres lentas al 30 y rápidas al 60, sin tocar precios. | 1 |
| Monturas y progresión | [remove_regular_mounts_ip_requisites.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/remove_regular_mounts_ip_requisites.sql) | Elimina cuatro condiciones de progresión para monturas raciales. | 10 |
| Botín y economía | [increase_world_boe_drop_rate.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/increase_world_boe_drop_rate.sql) | Probabilidades de referencias de BoE del mundo ×5, con valores base fijos. | 2 |
| Botín y economía | [rebalance_drop_rate.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/rebalance_drop_rate.sql) | Pata de reptador monstruoso: probabilidad de tabla fijada al 70 %. | No incluido |
| Equilibrado de objetos | [rebalance_items.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/rebalance_items.sql) | Ajustes a tres armas Torbellino y al Talismán etéreo. | 9 |

## 3. Equipo y protección frente a mala suerte

### 3.1. Jinetes Oscuros de bandas

La funcionalidad se distribuye en cuatro archivos: moneda, NPC, catálogo y recompensas de botín. Los NPC comparten el nombre **Dark Rider / Jinete Oscuro** y el modelo custom `90100`. Se configuran a nivel 60, neutrales, no atacables, estacionarios, con diálogo, comercio y reparación; disponen de títulos y diálogos en español.

| Banda | Moneda | NPC | GUID | Título esES | Entradas de venta | Precios usados en el catálogo |
|---|---:|---:|---:|---|---:|---|
| Núcleo de Magma | 90002 | 90200 | 900000 | Coleccionista de reliquias ígneas | 118 | 10, 50 y 100 monedas |
| Guarida de Alanegra | 90003 | 90201 | 900001 | Coleccionista de reliquias dracónicas | 129 | 5 y 10 monedas |
| Templo de Ahn'Qiraj | 90004 | 90202 | 900002 | Coleccionista de reliquias qiraji | 72 | 10 y 50 monedas |
| Naxxramas clásico | 90005 | 90203 | 900003 | Coleccionista de reliquias profanadas | 109 | 5, 10 y 50 monedas |

Los precios anteriores se han resuelto a partir de los registros reales de `dbc/ItemExtendedCost.dbc`, no suponiendo que el número del ID sea el precio. Distribución: MC tiene 115 entradas a 10, 2 a 50 y 1 a 100; BWL, 128 a 10 y 1 a 5; AQ40, 71 a 10 y 1 a 50; Naxx, 104 a 10, 4 a 5 y 1 a 50.

**Monedas:** calidad épica, ligadas al recoger, pila de 200, nivel requerido 1, sin precio de compra o venta en oro, `Flags = 2048` y `BagFamily = 0`. Las cuatro se crean clonando el objeto base `29434`. El inventario utiliza existencias ilimitadas (`maxcount = 0`, `incrtime = 0`).

**Obtención de curiosidades de banda:**

| Banda | Distribución del botín |
|---|---|
| MC | 1 por cada uno de los 9 jefes con cadáver configurados y 1 en el cofre de Mayordomo Executus, objeto del mundo `179703`. |
| BWL | 1 por cada uno de los 8 jefes. |
| AQ40 | 2 por encuentro; cada miembro del trío tiene 2 porque solo se saquea el último superviviente; los emperadores tienen 1 cada uno. El SQL contiene 12 entradas de criatura. |
| Naxx40 de Individual Progression | 1 por cada uno de los 14 jefes configurados mediante IDs custom `351xxx`, y 1 en el cofre de los Cuatro Jinetes `361000`. |

Los drops tienen `Chance = 100`, cantidades fijas y grupo de botín 0. El SQL resuelve el `lootid` de cada criatura y el `Data1` de cada cofre. Las monedas llevan el indicador de botín por jugador elegible. **No debe documentarse como entrega automática por ser moneda:** el comentario de `raid_gear_vendor_loot.sql` habla de `BagFamily = 8192`, pero la creación efectiva fija `BagFamily = 0` y el archivo de botín no cambia ese campo.

**Dependencias:** plantillas nativas, jefes/cofre de Naxx40 aportados por Individual Progression, modelo `90100`, `Item.dbc`, `ItemExtendedCost.dbc` y parche del cliente. Los menús y textos utilizan `92000–92003`.

Fuentes: [raid_gear_vendor.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/raid_gear_vendor.sql), [raid_gear_vendor_npc.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/raid_gear_vendor_npc.sql), [raid_gear_vendor_item.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/raid_gear_vendor_item.sql), [raid_gear_vendor_loot.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/raid_gear_vendor_loot.sql).

### 3.2. Jinetes Oscuros de mazmorras

Mismo reparto en cuatro archivos y mismo modelo/comportamiento básico que los vendedores de bandas. En el repositorio, el catálogo se llama **`dungeon_gear_vendor_item.sql`**. Ese es su nombre real; el comentario erróneo en el SQL NPC se corrigió después de la captura histórica descrita aquí.

Cada una de las 26 rutas o alas tiene moneda propia, vendedor propio y un jefe final designado. La recompensa es **1 token por jugador elegible al saquear al jefe final**, con 100 % de probabilidad, `MinCount = MaxCount = 1`, `Flags = 2048` y `BagFamily = 0`.

El catálogo está definido para **2 tokens por entrada de compra**, mediante un `ExtendedCost` específico por moneda. Los precios de 5/10 no aparecen utilizados en estos SQL. La tabla siguiente conserva el nombre de la moneda en español para evitar ambigüedades entre alas.

| Moneda / ruta | ID moneda | NPC | GUID | Jefe final (ID) | Entradas de venta | ExtendedCost |
|---|---:|---:|---:|---|---:|---:|
| Sima Ígnea | 90010 | 90300 | 900010 | Taragaman the Hungerer (11520) | 6 | 97010 |
| las Cuevas de los Lamentos | 90011 | 90301 | 900011 | Mutanus the Devourer (3654) | 24 | 97011 |
| las Minas de la Muerte | 90012 | 90302 | 900012 | Edwin VanCleef (639) | 22 | 97012 |
| Castillo de Colmillo Oscuro | 90013 | 90303 | 900013 | Archmage Arugal (4275) | 22 | 97013 |
| las Cavernas de Brazanegra | 90014 | 90304 | 900014 | Aku'mai (4829) | 16 | 97014 |
| las Mazmorras de Ventormenta | 90015 | 90305 | 900015 | Bazil Thredd (1716) | 4 | 97015 |
| Gnomeregan | 90016 | 90306 | 900016 | Mekgineer Thermaplugg (7800) | 22 | 97016 |
| Horado Rajacieno | 90017 | 90307 | 900017 | Charlga Razorflank (4421) | 17 | 97017 |
| Cementerio Escarlata | 90018 | 90308 | 900018 | Bloodmage Thalnos (4543) | 16 | 97018 |
| la Biblioteca Escarlata | 90019 | 90309 | 900019 | Arcanist Doan (6487) | 6 | 97019 |
| la Armería Escarlata | 90020 | 90310 | 900020 | Herod (3975) | 4 | 97020 |
| la Catedral Escarlata | 90021 | 90311 | 900021 | High Inquisitor Whitemane (3977) | 10 | 97021 |
| la Zahúrda Rajacieno | 90022 | 90312 | 900022 | Amnennar the Coldbringer (7358) | 20 | 97022 |
| Uldaman | 90023 | 90313 | 900023 | Archaedas (2748) | 25 | 97023 |
| Zul'Farrak | 90024 | 90314 | 900024 | Chief Ukorz Sandscalp (7267) | 19 | 97024 |
| Maraudon | 90025 | 90315 | 900025 | Princess Theradras (12201) | 34 | 97025 |
| Templo Sumergido | 90026 | 90316 | 900026 | Shade of Eranikus (5709) | 39 | 97026 |
| las Profundidades de Roca Negra | 90027 | 90317 | 900027 | Emperor Dagran Thaurissan (9019) | 132 | 97027 |
| la Cumbre de Roca Negra inferior | 90028 | 90318 | 900028 | Overlord Wyrmthalak (9568) | 70 | 97028 |
| la Cumbre de Roca Negra superior | 90029 | 90319 | 900029 | General Drakkisath (10363) | 78 | 97029 |
| La Masacre Este | 90030 | 90320 | 900030 | Alzzin the Wildshaper (11492) | 32 | 97030 |
| La Masacre Oeste | 90031 | 90321 | 900031 | Prince Tortheldrin (11486) | 44 | 97031 |
| La Masacre Norte | 90032 | 90322 | 900032 | King Gordok (11501) | 30 | 97032 |
| Scholomance | 90033 | 90323 | 900033 | Darkmaster Gandling (1853) | 107 | 97033 |
| Stratholme: sector vivo | 90034 | 90324 | 900034 | Balnazzar (10813) | 62 | 97034 |
| Stratholme: sector no muerto | 90035 | 90325 | 900035 | Baron Rivendare (10440) | 67 | 97035 |

**Criterio de catálogo:** equipo de jefes, raros y encuentros invocados; también bolsas/carcajes, recetas de drop y objetos especiales propios. Incluye cofres vinculados a encuentros —Los Siete, Theldren, Jarien/Sothos—. Excluye drops genéricos de trash/mundo, objetos solo de misión, llaves, munición, materiales, recetas compradas, tributo Gordok y el cofre de Knot.

Las 928 entradas corresponden a **927 IDs de objeto distintos**: un mismo objeto puede pertenecer a dos vendedores de alas diferentes. El catálogo más grande es Profundidades de Roca Negra, con 132 entradas. Sima Ígnea contiene los seis objetos `14145`, `14147`, `14148`, `14149`, `14150` y `14151`. Se usa `28972` para Flightblade Throwing Axe, la versión equipable de 3.3.5, en lugar de su ID clásico roto `13173`.

**Reglas de encuentro relevantes:** Taragaman concede la moneda de Sima Ígnea; Mutanus, tras el evento de Naralex, la de Cuevas de los Lamentos; en Catedral solo la concede Whitemane; Rey Gordok la concede desde su cadáver, también al hacer tributo; Maraudon y BRD no se dividen en monedas de subrutas. Una tabla de botín compartida o una moneda ausente hacen que el script de recompensas omita esa inserción y lo muestre en sus consultas de diagnóstico.

**NPC y localización:** los 26 spawns utilizan mapas exteriores `0` o `1`, con coordenadas y orientaciones personalizadas que el propio SQL identifica como facilitadas el 01/10/2026. Los menús/textos son `92100–92125`. El archivo contiene nombres, títulos, diálogos y opciones de comercio en enUS/esES. El documento no certifica la comprobación visual de esas ubicaciones.

**Dependencia pendiente en Git:** faltan las entradas `90010–90035` en el `Item.dbc` versionado y `97010–97035` en el `ItemExtendedCost.dbc` versionado. El SQL de catálogo por sí solo no crea esos registros DBC. Los rangos `98010–98035` y `99010–99035` tampoco están en ese DBC del commit analizado.

Fuentes: [dungeon_gear_vendor.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/dungeon_gear_vendor.sql), [dungeon_gear_vendor_npc.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/dungeon_gear_vendor_npc.sql), [dungeon_gear_vendor_item.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/dungeon_gear_vendor_item.sql), [dungeon_gear_vendor_loot.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/dungeon_gear_vendor_loot.sql).

## 4. Transfiguración

La **Marca de Transfiguración**, objeto `90001`, es una moneda independiente de las curiosidades de equipo. Es rara, ligada al recoger, apilable a 200, nivel requerido 1, con `Flags = 2048`, `BagFamily = 0` y display `40753`. Se crea/actualiza mediante upsert y tiene nombre/descripción esES.

| Contenido seleccionado | Recompensa definida |
|---|---|
| Jefes finales de BRD, LBRS, UBRS, Scholomance, Stratholme vivo/no muerto y las tres alas de La Masacre | 1 marca por cada jefe final de esas 9 rutas. |
| Onyxia `10184` | 2 marcas. |
| MC | 1 en cada entrada de jefe seleccionada salvo Ragnaros `11502`, que tiene 3. Incluye la criatura Mayordomo `12018`. |
| Hakkar `14834` | 2 marcas. |
| Ossirian `15339` | 2 marcas. |
| BWL | 1 por jefe salvo Nefarian `11583`, que tiene 3. |
| C'Thun `15727` | 3 marcas. |
| Kel'Thuzad `15990` | 3 marcas en esa entrada concreta. |

La probabilidad configurada es 100 % y la cantidad es fija. Se resuelve `creature_template.lootid` y se omiten filas sin lootid. **El SQL no configura el gasto de marcas en mod-transmog**: el uso de `90001` y su tarifa deben estar configurados en el módulo correspondiente.

Hay dos diferencias frente al sistema de monedas de bandas que conviene conservar en el inventario:

- La marca de transfiguración de Mayordomo está asignada a la criatura `12018`; este archivo no añade recompensa al cofre `179703`. El total de 12 marcas de MC indicado en un comentario no queda garantizado solo por estas sentencias.
- Kel'Thuzad se referencia como `15990`, mientras que el SQL de curiosidades Naxx40 utiliza `351019`. Este archivo no demuestra cobertura del Kel'Thuzad custom de Individual Progression.

Fuente: [transmog_currency_loot.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/transmog_currency_loot.sql).

## 5. Paladines Renegados

### 5.1. Datos de creación e instructores

`forsaken_paladin.sql` define la combinación **raza 5 / clase 2** en `playercreateinfo`, con inicio en mapa 0, zona 85, posición `(1676.71, 1678.31, 121.67)`. Añade seis acciones iniciales: ataque, Sello de rectitud, Luz Sagrada, Canibalismo, agua y comida. Los atuendos `9000` y `9001` cubren ambos sexos y utilizan los objetos `45`, `43`, `44`, `6948`, `2361`, `159` y `4604`.

| NPC propio | ID | Lugar | GUID | Plantilla base | TrainerId |
|---|---:|---|---:|---:|---:|
| Abraham West | 90210 | Brill | 5300690 | 2129 | 4 |
| Pancratius Ward | 90211 | Camposanto | 5300691 | 2123 | 6 |

Ambos tienen modelos nativos —1583/1578—, equipo definido, apariciones estacionarias y título esES «Instructor de paladines». El SQL reutiliza servicios de entrenamiento existentes, no inserta un catálogo nuevo en `trainer_spell`.

**Límite de alcance:** estos datos cubren creación e instructores. La habilitación completa de la combinación racial en el cliente y cualquier ajuste requerido del core son dependencias externas a este archivo; no se deben deducir de la presencia del SQL.

Fuente: [forsaken_paladin.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/forsaken_paladin.sql).

### 5.2. Cadena de Redención: nivel mínimo 12

Misiones restringidas a Renegados (`AllowableRaces = 16`) y paladines (`AllowableClasses = 2`). La cadena tiene siete pasos con prerrequisitos consecutivos y textos enUS/esES. La entrega final muestra Redención `7328` y ejecuta el hechizo de recompensa `7329`.

| ID | Misión esES | Objetivo | NPC de inicio → entrega |
|---:|---|---|---|
| 91010 | Un puñado de ceniza | Hablar con Abraham West. | 90211 → 90210 |
| 91011 | Bondad sin testigos | Entregar 10 paños de lino (`2589`) a Caice. | 90210 → 2307 |
| 91012 | Lo que aún necesitan los muertos | Regresar a Abraham West. | 2307 → 90210 |
| 91013 | La medida de la compasión | Hablar con el magistrado Sevren. | 90210 → 1499 |
| 91014 | La Luz sin piedad | Matar 8 guerreros Escarlata (`1535`). | 1499 → 1499 |
| 91015 | Un informe en ceniza | Informar a Abraham West. | 1499 → 90210 |
| 91016 | La Luz no nos da tregua | Completar la instrucción y obtener Redención. | 90210 → 90210 |

NPC reutilizados: celador Caice `2307` y magistrado Sevren `1499`, además de los dos instructores propios. La narrativa introduce la «Mano de Ceniza» como trasfondo; no crea una facción o reputación jugable nueva.

### 5.3. Cadena de arma: nivel mínimo 20

Cinco pasos consecutivos, también restringidos a paladines Renegados. Comienza en Abraham West y continúa con el herrero existente Basil Frye (`4605`).

| ID | Misión esES | Objetivo | NPC de inicio → entrega |
|---:|---|---|---|
| 91020 | Un arma de esta tierra | Hablar con Basil Frye en Entrañas. | 90210 → 4605 |
| 91021 | Madera y tendón | Entregar un mango Agamand y una atadura Putrepellejo. | 4605 → 4605 |
| 91022 | El peso del cuervo | Obtener el contrapeso de Thule Corvozarpa. | 4605 → 4605 |
| 91023 | Hierro cautivo | Obtener hierro forjado de Durnholde. | 4605 → 4605 |
| 91024 | Vigilia de Lordaeron | Entregar/cerrar la cadena y recibir Vigilia de Lordaeron. | 4605 → 4605 |

### 5.4. Objetos propios de las misiones

| ID | Nombre esES | Función y procedencia |
|---:|---|---|
| 92060 | Contrapeso Corvozarpa | Objetivo de `91022`; Thule Corvozarpa `1947`. |
| 92061 | Mango de arma Agamand | Objetivo de `91021`; expositor de armas `105172`, tabla de botín `4767`. |
| 92062 | Hierro forjado de Durnholde | Objetivo de `91023`; velador del Sindicato `2261`. |
| 92063 | Atadura Putrepellejo | Objetivo de `91021`; criaturas `1939`, `1940`, `1942`, `1943`. |
| 92064 | Vigilia de Lordaeron | Recompensa final de `91024`; maza rara de dos manos exclusiva de paladines. |

Los cuatro materiales tienen límite de una unidad y son objetos de misión. Sus drops están al 100 %, exigen misión y tienen condiciones explícitas de misión activa; se añaden también relaciones `creature_questitem`/`gameobject_questitem` para la información de objetivos.

**Vigilia de Lordaeron:** nivel de objeto 31, daño 65–99, velocidad 3,2 s, +7 aguante, +12 espíritu y +6 intelecto; ligada al recoger. El requisito de acceso al nivel 20 está en la cadena; el objeto tiene `RequiredLevel = 0`.

Se modifican relaciones de inicio/entrega, textos de petición/recompensa y sus traducciones. No se añaden nuevos NPC de combate ni scripts C++ en este SQL. La forja final se describe mediante texto de misión; el archivo no define una escena temporizada.

Fuente: [forsaken_paladin_quests.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/forsaken_paladin_quests.sql).

## 6. Cambios de guerrero

### 6.1. Furia enfilada / Single-Minded Fury

| Registro | ID | Contenido |
|---|---:|---|
| Talento | 3000 | Árbol Furia `164`, `TierID = 10`, `ColumnIndex = 2`, un rango. |
| Hechizo visible | 90000 | Marca pasiva del talento; icono `533`; nombre y descripción enUS/esES. |
| Aura de bonificación | 90001 | +20 % de daño físico; base de efecto `19` y escuela física `1`. |

El SQL declara las filas en `talent_dbc` y `spell_dbc`. La condición «un arma de una mano en cada mano» requiere el módulo **`mod-warrior-rework`** y los DBC de cliente/servidor correspondientes. El README del módulo presente en el repositorio documenta la comprobación de talento en la especialización activa y la retirada de la bonificación al dejar de cumplir la condición.

El SQL no establece exclusión mutua con Empuñadura de titán. Tampoco convierte por sí mismo el equipamiento de dos manos en válido para la nueva bonificación.

Fuentes: [single_minded_fury.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/single_minded_fury.sql) y [modules/mod-warrior-rework/README.md](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/modules/mod-warrior-rework/README.md).

### 6.2. Especializaciones de armas generalizadas

`spells_override.sql` contiene 15 inserciones `INSERT IGNORE` con datos completos de hechizo y 15 actualizaciones. Para los siguientes rangos fija `EquippedItemSubclass = 42483` y sustituye la descripción en inglés:

| Familia original | IDs modificados | Efecto que conserva el talento |
|---|---|---|
| Especialización en hachas y armas de asta | 12700, 12781, 12783, 12784, 12785 | Probabilidad de crítico y daño crítico. |
| Especialización en mazas | 12284, 12701, 12702, 12703, 12704 | Ignorar parte de la armadura. |
| Especialización en espadas | 12281, 12812, 12813, 12814, 12815 | Probabilidad de ataque adicional. |

La máscara `42483` activa las subclases `0, 1, 4, 5, 6, 7, 8, 10, 13, 15`: hachas, mazas y espadas de una y dos manos, armas de asta, bastones, armas de puño y dagas. El cambio amplía el filtro de armas de las tres familias, sin renombrar sus talentos.

La actualización explícita afecta al filtro y al texto enUS; no actualiza `Description_Lang_esES`. `INSERT IGNORE` conserva una fila que ya exista: no debe interpretarse como una restauración completa de todos sus campos. La efectividad de condiciones adicionales del core o de procs no se ha probado en juego.

Fuente: [spells_override.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/spells_override.sql).

## 7. Monturas y progresión

### 7.1. Nivel de las monturas terrestres

`ground_riding_override.sql` fija:

- Aprendiz jinete, hechizo `33388`: nivel de entrenamiento **30**.
- Oficial jinete, hechizo `33391`: nivel de entrenamiento **60**.
- Objetos de montura terrestre con equitación 75: nivel **30**, con excepciones explícitas.
- Objetos de montura terrestre con equitación 150: nivel **60**.
- Listas adicionales de monturas antiguas, PvP y excepciones rápidas: nivel **60**, incluso si su metadato de equitación no coincide con la regla genérica.

Entre las excepciones rápidas figuran sable de hielo de Cuna del Invierno `13086`, monturas de guerra, tanques qiraji, riendas de Destrero de la Muerte `13335`/`23193`, ravasaurio `46102` y destrero carmesí `52200`. Los cambios no alteran precios, reputación, calidad ni los requisitos de vuelo 225/300; tampoco reescriben cadenas de montura de clase.

Son seis `UPDATE`: dos sobre entrenamiento y cuatro sobre objetos. El número efectivo de objetos afectados depende de los datos existentes en la base de datos. Debe ejecutarse después de los cambios de monturas de Individual Progression.

Fuente: [ground_riding_override.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/ground_riding_override.sql).

### 7.2. Disponibilidad de cuatro monturas raciales

`remove_regular_mounts_ip_requisites.sql` borra condiciones de misión/progresión (`SourceTypeOrReferenceId = 23`, `ConditionTypeOrReference = 8`) de estas parejas vendedor–objeto:

| Vendedor | Objeto | Nombre nativo |
|---:|---:|---|
| 3362 | 46099 | Horn of the Black Wolf |
| 3685 | 46100 | White Kodo |
| 4731 | 46308 | Black Skeletal Horse |
| 4731 | 47101 | Ochre Skeletal Warhorse |

El archivo no crea entradas de venta ni elimina condiciones de otro tipo. Su cabecera también anuncia un cambio de retirada de monturas épicas pre-1.4 después de MC, pero **no contiene ninguna sentencia que implemente ese segundo objetivo**. El alcance ejecutable es exclusivamente el borrado de las cuatro parejas anteriores.

Fuente: [remove_regular_mounts_ip_requisites.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/remove_regular_mounts_ip_requisites.sql).

## 8. Botín y economía

### 8.1. Referencias de BoE del mundo ×5

`increase_world_boe_drop_rate.sql` contiene una instantánea de **2.512 parejas `Entry`/`Item`**, distribuidas en **315 IDs de tabla de referencia**. Fija `Chance = LEAST(BaseChance × 5, 100)` sobre filas de `reference_loot_template` que tengan `Reference <> 0` y comentarios que coincidan con grupos Vanilla/TBC/WotLK de verdes, azules o épicos.

Se trata de probabilidades de **referencias anidadas**: esas 2.512 filas no son 2.512 objetos nuevos. Tampoco equivale a multiplicar por cinco todo el botín o todos los jefes. El efecto final depende de la cadena de referencias y de las tasas configuradas en el servidor.

La base de cálculo está embebida en el SQL. Su reaplicación fija el mismo valor y evita acumular ×5 sucesivos. Si cambia la base de loot de upstream, la instantánea puede requerir regeneración.

Fuente: [increase_world_boe_drop_rate.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/increase_world_boe_drop_rate.sql).

### 8.2. Pata de reptador monstruoso

`rebalance_drop_rate.sql` fija `Chance = 70.0` para el objeto **6184** en la tabla de botín **1088**. No crea una fila si falta ni resuelve dinámicamente el lootid de la criatura; tampoco modifica grupos, referencias o cantidades. El 70 % es el valor de esa fila, no una medición del porcentaje efectivo bajo todas las configuraciones del servidor.

Fuente: [rebalance_drop_rate.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/rebalance_drop_rate.sql).

## 9. Equilibrado de objetos existentes

| Objeto | ID | Modificación explícita |
|---|---:|---|
| Whirlwind Axe / Hacha de Torbellino | 6975 | Tercera estadística: tipo `3` (agilidad), valor `11`. |
| Whirlwind Warhammer / Martillo de guerra de Torbellino | 6976 | Tercera estadística: tipo `3` (agilidad), valor `11`. |
| Whirlwind Sword / Espada de Torbellino | 6977 | Tercera estadística: tipo `3` (agilidad), valor `11`. |
| Ethereal Talisman / Talismán etéreo | 4430 | Calidad `3` (rara), nivel de objeto `48`, `stat_value1 = 8` y `stat_value3 = 5`. |

En el talismán no se cambian los tipos de estadística: la interpretación de los valores depende de los tipos que ya tenga el objeto. Estas sentencias modifican objetos existentes; no añaden cuatro objetos nuevos.

Fuente: [rebalance_items.sql](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/data/sql/custom/db_world/rebalance_items.sql).

## 10. Registro de identificadores propios

Los espacios de nombres son independientes: por ejemplo, el hechizo `90001` y el objeto `90001` no colisionan por compartir número.

| Espacio de nombres | IDs | Función |
|---|---|---|
| Objetos | 90001 | Marca de Transfiguración. |
| Objetos | 90002–90005 | Curiosidades de bandas. |
| Objetos | 90010–90035 | Curiosidades de mazmorras. |
| Objetos | 92060–92064 | Componentes y arma de las misiones de paladín. |
| Plantillas NPC | 90200–90203 | Vendedores de bandas. |
| Plantillas NPC | 90210–90211 | Instructores de paladín Renegado. |
| Plantillas NPC | 90300–90325 | Vendedores de mazmorras. |
| GUID de criatura | 900000–900003 | Apariciones de vendedores de bandas. |
| GUID de criatura | 900010–900035 | Apariciones de vendedores de mazmorras. |
| GUID de criatura | 5300690–5300691 | Apariciones de los instructores. |
| Menús y textos | 92000–92003 | Diálogos de vendedores de bandas. |
| Menús y textos | 92100–92125 | Diálogos de vendedores de mazmorras. |
| Misiones | 91010–91016, 91020–91024 | Las dos cadenas de paladín. |
| Atuendos iniciales | 9000–9001 | Paladín Renegado masculino/femenino. |
| Talentos | 3000 | Furia enfilada. |
| Hechizos | 90000–90001 | Marca del talento y bonificación condicional. |
| Modelo/display DBC | 90100 | Jinete Oscuro; referencia consumida por los SQL, no creada por ellos. |
| ExtendedCost de bandas usado por SQL | 93010, 93050, 93100; 94005, 94010; 95010, 95050; 96005, 96010, 96050 | Precios de los cuatro catálogos de banda. |
| ExtendedCost de mazmorras requerido | 97010–97035 | Precio previsto de dos tokens; ausente del DBC versionado revisado. |

El registro es un inventario de usos, no una reserva global de IDs frente a cualquier módulo o base de datos externa.

## 11. Dependencias y estado comprobado

| Dependencia | Evidencia en el commit analizado | Qué no queda acreditado |
|---|---|---|
| `dbc/Item.dbc`: monedas de raid/transmog | Presentes `90001–90005`. | Igualdad con el DBC instalado y con los MPQ. |
| `dbc/Item.dbc`: objetos de paladín | Presentes `92060–92064`. | Igualdad con las copias de servidor/cliente. |
| `dbc/Item.dbc`: monedas de mazmorra | Ausentes `90010–90035`. | No se puede reproducir ese contrato solo con el DBC de Git. |
| `dbc/ItemExtendedCost.dbc`: bandas | Presentes los costes usados por los cuatro vendedores. | Despliegue real de esas filas. |
| `dbc/ItemExtendedCost.dbc`: mazmorras | Ausentes `97010–97035`, `98010–98035` y `99010–99035`. | Los SQL no crean costes DBC ni prueban su instalación. |
| Modelo Jinete Oscuro | Los SQL consumen `90100`. | Modelo y recursos del MPQ no inspeccionados en esta revisión. |
| `mod-warrior-rework` | Carpeta y README presentes; contrato con talento/hechizos documentado. | Compilación, carga y pruebas de juego. |
| Individual Progression | Los SQL dependen de Naxx40 y ajustan monturas/condiciones. | Versión y estado instalado del módulo. |
| Transfiguración | El SQL crea y distribuye `90001`. | Configuración del módulo que consume la moneda. |
| Instalador SQL | `--validate` falla por siete archivos fuera del manifiesto. | Qué SQL se aplicaron antes por otras vías. |

Fuentes auxiliares: [dbc/Item.dbc](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/dbc/Item.dbc), [dbc/ItemExtendedCost.dbc](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/dbc/ItemExtendedCost.dbc), [docs/project/components/client-assets.md](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/docs/project/components/client-assets.md), [modules/mod-warrior-rework/README.md](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/modules/mod-warrior-rework/README.md) y [scripts/apply-db-world.sh](https://github.com/jgjaraba/azerothcore-setup/blob/c288958ceb7c382f34123fbba6946101879f66c3/scripts/apply-db-world.sh). Los hechos sobre registros DBC anteriores proceden de la lectura de los binarios de este commit; la documentación histórica no se ha tratado como prueba del estado actual del servidor.

## 12. Observaciones de coherencia y mantenimiento

Estas observaciones describen lo encontrado; no se ha modificado el repositorio.

| Observación | Consecuencia para el inventario |
|---|---|
| 7 SQL sin entrada en `manifest.txt` | El instalador se detiene antes de MySQL, aunque los otros 11 estén enumerados. |
| Monedas y costes de mazmorras ausentes de los DBC de Git | Los SQL y los binarios versionados no representan aún el mismo conjunto de contenido. |
| `dungeon_gear_vendor_item.sql` frente a `dungeon_gear_item.sql` en comentarios | Inconsistencia histórica de comentario, corregida en el SQL NPC vigente. |
| Comentario de raid loot con `BagFamily = 8192`, creación con `0` | No atribuir distribución automática al conjunto actual por ese comentario. |
| Transmog usa Mayordomo criatura y Kel'Thuzad `15990` | No equivale al tratamiento de cofre/IDs Naxx40 del sistema de curiosidades de banda. |
| Limpieza de monturas anuncia dos objetivos pero ejecuta uno | Solo está implementado el borrado de cuatro condiciones concretas. |
| Cambios de especialización de armas actualizan texto solo enUS | La descripción esES no queda sincronizada por ese SQL. |

### Reaplicación: alcance de lo observado

Los archivos usan principalmente `DELETE` + `INSERT` sobre IDs propios, upserts o asignaciones absolutas mediante `UPDATE`. El aumento BoE calcula desde una base fija, no desde el valor que encuentre instalado. El catálogo de cada vendedor se reemplaza completo; los NPC se recrean con GUIDs fijos y las posiciones declaradas. `spells_override.sql` conserva campos preexistentes fuera de sus actualizaciones explícitas por usar `INSERT IGNORE`.

Este apartado describe los patrones del código. **Esta revisión de inventario no es una certificación de ejecución de los 18 archivos en el MySQL desplegado**, ni garantiza compatibilidad con una versión arbitraria del esquema o IDs ocupados por otros módulos. Reaplicar un archivo puede restaurar sus valores y deshacer ajustes manuales sobre los registros que administra.

## 13. Fuera de alcance

- SQL internos de módulos que no estén en `data/sql/custom/db_world/`.
- Contenido de los MPQ, modificaciones gráficas y complementos de interfaz.
- Cambios del core, salvo referencias necesarias para entender una dependencia.
- Configuración de AHBot, playerbots, transfiguración y otros módulos externos.
- Archivos entregados por chat que no estén incorporados al commit revisado.
- Inventarios de personajes, despliegue real y validación visual o funcional dentro del juego.

Para futuras actualizaciones del inventario, revisar primero la lista de SQL y el manifiesto; después recalcular entidades y catálogos, comprobar sus DBC y actualizar el commit de referencia. Mantener separados el contenido definido, las dependencias versionadas y la evidencia de despliegue.
