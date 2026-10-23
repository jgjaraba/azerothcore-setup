# Trolls Turtle — contrato histórico v2 y diagnóstico de caras

**Documento histórico.** La entrega vigente son las
[ediciones principal/opcional v3](troll-customizations.md). La v2 completa se
conserva en `client_patches/turtle_forest_troll/v2/`, no en el path principal.
Los SQL364 históricos están en `data/sql/history/troll-v2-full/`; no aplicar
esas copias como instalación actual. La prueba A/B conserva su resultado acotado.

## Alcance y cobertura

El archivo archivado `client_patches/turtle_forest_troll/v2/Data/patch-S.MPQ` ampliaba el
[piloto ForestTroll aceptado](forest-troll-skins.md). No cambia raza8, modelos,
animaciones, facción, displays ni hechizos. No importa M2/SKIN Turtle ni morphs.
Los recursos finales y SQL se conservan en el repositorio; cliente manual.

| Componente | Cobertura |
|---|---|
| ForestTroll aceptado |90 registros y162 texturas exactamente conservados; colores18–23 por sexo |
| Nuevas pieles |12 masculinas y9 femeninas:18 cuerpos alternos más3 bakes masculinos de tienda |
| Caras de esas pieles |Un rostro prefijado derivado del mismo atlas, con aliases para Face0–4 hombre /0–5 mujer; no son caras diferentes inventadas |
| Rasgos faciales |3 masculinos (11–13),4 femeninos (6–9); texturas con alpha y geosets de colmillos ya nativos |
| Pelo |Se habilitan en creación4 peinados masculinos6–9 y5 femeninos5–9 antes limitados a barbería |
| Colores de pelo |No hay opciones fuente adicionales; se mantienen0–9 normales y10–12 DK |

El snapshot no tiene nuevas variantes de **cara ordinaria** aparte de las ya
nativas0–4/0–5. Las siete novedades son rasgos de textura/colmillos del quinto
control, no siete índices nuevos del selector Face. Tampoco hay nuevos meshes
de peinado: CharHairGeosets tiene las mismas claves0–9. Se conservan sus valores
WotLK de scalp/Bald, incluidos los que difieren de Vanilla.

### Mapa de pieles nuevas

| Color destino | Hombre | Mujer |
|---|---|---|
|24–32|TrollMaleSkin00_100–108|TrollFemaleSkin00_100–108|
|33|trollmaleshop1|—|
|34|trollmaleshop2|—|
|35|zombietrollshop|—|

Las fuentes numeradas permanecen con esos identificadores neutros: no se ha
demostrado una correspondencia completa con los nombres actuales Dark/Ice/Sand
de la tienda. Son21 recursos distintos, no21 productos comerciales certificados.
El cuerpo masculino `_109` es un alias byte-idéntico del Forest18 ya aceptado
y **no añade otra opción duplicada**. Normales0–5, NPC6–14 y DK15–17 no se mueven
ni se habilitan indiscriminadamente.

## Componentes y preservación

CharSections pasa de8958 filas base +90 Forest a **9295**. Se añaden247 registros
con IDs **20100–20346**:156 de piel/cara/ropa interior y91 de rasgos faciales.
Las117 filas originales de pelo mantienen ID, tupla y texturas: solo se añade
PLAYER a sus flags, **0x12→0x13** normal y **0x06→0x07** DK, conservando barbería.
No hay otros cambios a las8958 filas originales ni a las90 Forest aceptadas.

El SQL adicional contiene364 overlays:247 nuevos +117 de pelo. Junto al SQL
Forest original resultan454 filas. Se rechazan IDs o tuplas ocupados por datos
diferentes; no se adopta silenciosamente un overlay previo con los flags antiguos.
La base binaria CharSections del servidor permanece intacta.

La tabla **CharacterFacialHairStyles no tiene ID**: su clave es
`Race,Sex,Variation`. Se añaden siete filas a las222 nativas, dando229, tanto en
el cliente como en servidor. Su formato es8 enteros; en Turtle es9, donde los
tres valores legacy intermedios no son los cinco geosets WotLK. La traducción
comprobada es `primeros3 + últimos3 + 0,0`. Todos los meshes necesarios ya existen.

El helper servidor admite el tipo opcional `facial-style-delta` y fusiona los
siete registros compactos sin reemplazar la tabla por el donor. La entrada en
`data/server/manifest.json` apunta a
`turtle-customizations/dbc/CharacterFacialHairStyles.dbc`; las430 entradas previas
permanecen iguales. Ahora se verifican431 archivos fuente.

### Atlas y ropa interior

Los cuerpos alternos no tienen familias DBC completas. Sus componentes NPC con
el mismo sufijo no coinciden con los atlas efectivos; algunos nombres de ropa
interior usados por Turtle ni siquiera existen. No se reutilizan a ciegas.

Se conserva el cuerpo fuente, se escala256→512 por nearest-neighbor cuando
corresponde y se recorta su propio rostro. Las caras repetidas en las tuplas
permiten cambiar piel sin alterar el byte Face; el resultado visual sigue siendo
un único rostro prefijado por apariencia. Se conservan las caras de Forest.

Para ropa interior se recupera una máscara del **atuendo nativo** usando los seis
pares cuerpo/ropa originales y un ajuste `U≈alpha*F+(1-alpha)*B`. Se conserva la
mayor componente conexa, se dilata un píxel y se descarta ruido cuantizado. La
prenda recuperada se compone sobre el recorte del nuevo cuerpo, no sobre piel
azul ajena. MAE RGB de reconstrucción:2.745 pelvis masculina,3.308 pelvis femenina,
3.373 torso femenino, escala0–255. Es adaptación aproximada, no recuperación
matemáticamente exacta. Los detalles de ropa ya pintados en el atlas se conservan.
No se hornea la ropa interior en Base0: sigue siendo una capa Base4 normal.

### Transparencia facial y DK

Las nuevas texturas faciales usan alpha BLP2 real. No se elimina negro o blanco
por color-key. Se corrigió el decoder de investigación: en BLP2 paletted el alpha
es un plano separado de1/4/8 bits, **no el cuarto byte de la paleta**. Pillow13
puede dar un alpha incorrecto en este caso; el builder tiene decoder y tests
propios. Los fondos aparentemente opacos no justifican borrar píxeles del dibujo.

Solo dos fuentes tenían metadatos de mip terminal malformados:
`FacialLowerHair08_00` y `FacialUpperHair08_00`. Se regeneran como BLP2 BGRA con
mips válidos hasta1×1 y RGBA superior pixel-idéntico. Las demás fuentes se
conservan, incluidas las162 Forest. Las304 texturas publicadas pasan validación
estricta; no se entrega el tamaño uint32 inválido del exportador Turtle.

Las siete opciones faciales tienen fuente HairColor0–9. Para DK se proporcionan
aliases explícitos **10/11→8,12→9** (gris/blanco), no supuestas paletas Turtle
adicionales. Las nuevas filas usan0x11. Las caras DK exclusivas conservan el
acoplamiento Face/Skin nativo descrito en el contrato Forest; no se promete que
cualquier cara DK combine independientemente con cualquier piel.

## Construcción y aplicación

Manifiesto reproducible: `tools/troll-customizations.json`; dependencias fijadas
en `tools/troll-customizations-requirements.txt` (NumPy2.2.6/Pillow13.0.0).
El builder lee MPQ fuente fijados por hash, no los informes ignorados de `work/`:

```sh
python3 tools/build_troll_customizations.py --output work/troll-build-nuevo
```

Usar un entorno Python aislado con esas dependencias. `--publish` verifica la
publicación anterior, conserva v1 y solo acepta upgrades conocidos/verificados;
no es una orden de instalación. Una reconstrucción v1 no debe publicarse encima
de la v2. La publicación actual contiene dos DBC,304 texturas y su listfile.

Servidor nuevo: aplicar los manifiestos existentes en su orden, con servidor
detenido, `--with-server-data`, DataDir y **nuevo estado** para esta versión del
manifiesto. Incluye el SQL Forest90 antes de
el SQL364 ahora archivado como `data/sql/history/troll-v2-full/apply.sql` y el delta facial.
El SQL hereda la preparación MyISAM→InnoDB y las guardas transaccionales; esa DDL
no se deshace y el lote SQL+archivos no es una transacción única.

Cliente manual: verificar `SHA256SUMS` y reemplazar el patch-S propio v1 por el
actual **en el mismo path `Data/patch-S.MPQ`**, con WoW cerrado. Mantener T/Z y
locale-Z; no poner dos versiones S ni guardar backups en Data. No sobrescribir
un S ajeno. El directorio `v1/` es archivo de rollback, no otra carpeta que copiar
al cliente. Los clientes que vean estas apariencias necesitan la misma versión.

SHA256 v2: `d63ecb0e583a77f4283dde8f39e253d4dee5694f6978ae5326d1120e164165a9`.
La base es el cliente de referencia auditado; otros mods de CharSections/modelos
y HD requieren auditoría propia. Los snapshots originales no se modifican.

## Rollback a Forest-only v1

Recustomizar primero Trolls que usen pieles nuevas24+, rasgos masculinos11–13 o
femeninos6–9. Los peinados siguen existiendo en v1 como opciones de barbería,
pero se revierte su acceso ampliado en creación. No se borran personajes ni se
migran sus bytes automáticamente.

Con servidor detenido, el rollback SQL específico
`data/sql/history/troll-v2-full/rollback.sql` elimina los364 overlays históricos
idénticos: quedan las90 filas Forest. No ejecutar el rollback Forest original.
Retirar también los siete registros faciales añadidos al servidor, preservando
los demás registros. El estado de instalación incremental de esta ampliación
permite restaurar el archivo previo mediante el helper de datos.

**Cuidado:** `apply_project_server_data.py rollback` restaura todos los archivos
que posee su estado, no solo la tabla facial. Solo usarlo para volver a v1 si el
estado fue capturado sobre una v1 ya instalada y sus demás archivos eran idénticos.
En una instalación limpia ese estado puede poseer también geografía; no usarlo
como desinstalador selectivo de skins. Conservar manifiesto/fuentes/estado y
auditar esa restauración antes de ejecutarla.

Restaurar `v1/Data/patch-S.MPQ` en el cliente, no ambos S. El manifiesto normal
vuelve a instalar v2 mientras mantenga registrada la extensión. Usar otro estado
para una instalación nueva después de revertir.

## Validación

- **FAIL — informe del usuario:** las pieles añadidas en v2 presentan rostros
  verdes/sin textura. No se detalló una matriz por color/sexo; no es un diagnóstico
  de causa ni invalida por sí solo las pieles Forest v1 aceptadas.
- **PASS — informe del usuario:** peinados y opciones faciales funcionan
  correctamente y deben conservarse. No retirar toda la v2 para quitar las pieles.
- **PASS:**16 pruebas de codec/build/publicación/MySQL privado, con dos builds
  idénticos, validación estricta de304 texturas y preservación de Forest.
- **PASS:**27 pruebas del helper, incluidas222→229 filas, colisiones, repetición,
  recuperación y rollback;14 pruebas v1 y4 del auditor sin regresión.
- **PASS:** en DEV, apply/reapply→454 filas; rollback/repetición→90 Forest;
  restauración del archivo facial y nueva instalación/repetición→229 filas.
  Consulta final: los454 overlays coinciden campo a campo con el informe; la
  DBC facial servidor coincide con la cliente y CharSections binaria no cambió.
- **PASS:** revisión independiente de artefactos/código y arranque DEV observado
  hasta worldserver ready, con authserver activo. Esto no implica que el agente
  haya visto los nuevos looks ni cada lookup del store en memoria.
- **NOT RUN por el agente / sin confirmación específica:** matriz exhaustiva de
  cycling, equipo, creación/relog, recustomización, bots, otro cliente y HD.
  Las comprobaciones de datos anteriores no equivalen a aceptación de renderizado.

### Valoración rápida del fallo de rostro

La primera hipótesis a probar es la representación de las caras generadas:
BLP2 encoding3 BGRA, preferredFormat0 (DXT1), mip inicial en148. Las caras Forest
aceptadas usan paleta. Los atlas fuente examinados sí contienen caras, así que
no se ha demostrado que los recortes estén vacíos. El ejecutable auditado tiene
ramas encoding3; no afirmar que todo BGRA es incompatible con335. El campo de
formato preferido sí interviene en la selección de formato del cliente; falta
aislar su efecto y el del compositor de texturas de personaje.

Los dos rasgos faciales reparados también usan BGRA y el usuario confirma en
general que los rasgos funcionan. Es evidencia contra una incompatibilidad
universal, aunque no confirma que probara esos dos recursos concretos.

Se preparó la **única prueba A/B solicitada por el usuario**, sin reparar todavía
la publicación normal. El candidato está separado en
`client_patches/turtle_forest_troll/face-format-test/`, con INSTALL/checksums y
reproducción mediante `tools/build_troll_face_format_test.py`. Parte del v2
SHA256 `d63ecb0e583a77f4283dde8f39e253d4dee5694f6978ae5326d1120e164165a9`.

Solo cambian `Male\100_FaceLower.blp` y `Male\100_FaceUpper.blp` bajo el namespace
Custom\TurtleTroll: **trol masculino Skin24, primer tono v2, morado**. Los cinco
Face normales son aliases de esa misma pareja. Se cambia BGRA por paleta BLP2
con preferredFormat8 y mip inicial1172, como las caras Forest aceptadas. Los
RGBA superiores son **pixel-idénticos**, sin cuantización del rostro base; el
alpha permanece exacto en todos los mips y el informe mide aproximación RGB
de los mips inferiores. No se cambia el recorte, las dimensiones, paths ni DBC.

**PASS:** cinco tests, incluidos dos candidatos deterministas y comparación
de todos los miembros. De306 payloads solo difieren esas dos caras; las DBC,
restantes pieles, Forest, pelo y rasgos faciales permanecen byte-idénticos.
**PASS — resultado visual confirmado por el usuario:** «ahora si funciona
perfectamente», tras la prueba de esa pareja de caras. No es una ejecución
del cliente por el agente ni una certificación de las demás pieles/sexos/DK.
El cambio de representación corrige el caso probado sin cambiar sus píxeles
principales, recortes o DBC; no identifica por separado cuál de los campos del
formato/compositor causaba el fallo. La publicación normal y el servidor siguen
sin cambios; el agente no instala archivos en el cliente jugado. Candidato SHA256:
`a9a7fc72157a963f5c1235b4c5684d88c3420058c11cc19c68a3fe4b5eef9777`.

Para comprobarlo, sustituir temporalmente el S propio con WoW cerrado y elegir
**esa piel masculina**, clase normal y un rasgo facial original sin maquillaje
nuevo que oculte la cara. No instalar un segundo S ni tocar T/Z. Restaurar el S
normal para volver al estado anterior. No se requiere reiniciar el servidor.
Si no se prueba esa combinación y ese archivo, el resultado no aísla la hipótesis.
Un roundtrip de nuestro codec no prueba compatibilidad del cliente. La decisión
de extender la corrección o retirar las pieles adicionales sigue correspondiendo
al usuario, conservando peinados, rasgos faciales y Forest en ambos casos. El
resultado favorece extender esta conversión, pero todavía no se ha aplicado a
las demás caras ni sustituido el parche normal por una reparación general.

Prueba práctica: ambos sexos, todos los colores/rostros prefijados, pelo0–9,
rasgos masculinos11–13/femeninos6–9 y sus transparencias; DK con sus aliases;
comparar Forest18–23 con la versión aceptada; desnudo/equipado, crear y relog.
Las opciones deben ser pieles/rasgos nativos y el equipo debe seguir visible.
