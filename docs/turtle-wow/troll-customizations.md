# Trolls Turtle — ediciones principal y opcional de patch-S

Las rutas de este contrato son las **bases Troll congeladas**. La entrega vigente
incluye tauren y se instala desde las [rutas acumulativas canónicas](tauren-customizations.md),
según ADR-0007. No cargar estos MPQ de base junto al S acumulativo.

## Entrega y elección

Se distribuyen **dos ediciones completas y excluyentes**, ambas instaladas como
`Data/patch-S.MPQ`. No son capas que deban cargarse juntas. No se cambian raza8,
modelos, animaciones, facción, displays o hechizos; no se importan M2/SKIN Turtle.

| Edición | Ruta en el repositorio | Contenido |
|---|---|---|
| Principal | `client_patches/turtle_forest_troll/Data/patch-S.MPQ` | ForestTroll, pelo y rasgos faciales; excluye las pieles adicionales |
| Opcional completa | `client_patches/turtle_forest_troll/optional-extra-skins/Data/patch-S.MPQ` | Todo lo principal más18 apariencias adicionales,9 por sexo, con todas sus caras convertidas |

Cada directorio contiene `report.json` y `SHA256SUMS`. Copiar **solo el archivo
elegido**, con WoW cerrado, reemplazando el S propio; guardar backups fuera de
Data y conservar T/Z/locale-Z. No renombrar la opcional como otro patch ni copiar
los directorios históricos al cliente. Auditar antes de sustituir un S ajeno.

La base es el cliente de referencia auditado y sus DBC fijadas por hash; no se
certifica cualquier mod de modelos/CharSections ni la variante HD.

## Contenido preservado

Las dos ediciones mantienen byte-idénticos los90 registros y162 texturas del
[ForestTroll v1 aceptado](forest-troll-skins.md), colores18–23 para ambos sexos.
También conservan los117 cambios PLAYER de las filas nativas de pelo y los91
registros de rasgos faciales que el usuario confirmó correctos en v2:

- Peinados masculinos6–9 y femeninos5–9 habilitados en creación. Ya existían en
  WotLK como barber-only; se preservan geometría, IDs, texturas y scalp nativos.
- Tres rasgos masculinos11–13 y cuatro femeninos6–9, usando geometría de
  colmillos existente y texturas con alpha real. No son nuevos meshes.
- HairColor0–9 permanece nativo; los rasgos en colores DK10/11 usan alias fuente8
  y12 usa9. No se inventan paletas de pelo ni caras DK adicionales.
- CharacterFacialHairStyles sigue siendo222 filas nativas +7 =229 en ambos
  clientes y el servidor. Es clave natural Race/Sex/Variation, no una tabla con ID.

No se modifica el binario CharSections del servidor; los metadatos se aplican
mediante SQL. Los índices normales0–5, NPC6–14 y DK15–17 no se renumeran ni se
habilitan indiscriminadamente. La cara y la piel siguen acopladas en el selector
nativo; las caras DK exclusivas pueden requerir cambiar Face antes de Skin.

### Principal

- **Aceptación del usuario:** «el parche principal es perfecto». Su MPQ se
  conserva byte-idéntico al retirar las tres pieles masculinas del opcional.
- CharSections **9139** filas; **211** texturas; **213** payloads con las dos DBC.
- Elimina las156 filas de piel/cara/ropa interior con Color24+ y sus93 recursos:
  21 cuerpos,42 caras y30 componentes de ropa interior.
- Conserva todos los demás registros/recursos de v2. Puede conservar cadenas
  antiguas no referenciadas para no alterar offsets; eso no habilita las pieles.

### Opcional

- CharSections **9274** filas; **292** texturas; **294** payloads.
- Añade9 apariencias masculinas y9 femeninas, colores24–32 en ambos sexos.
- Corresponden a fuentes numeradas100–108; no asignarles nombres comerciales no
  demostrados. El masculino109 ya era alias exacto de Forest18, no otra piel.
- Se retiraron exclusivamente los tres últimos colores masculinos33/34/35,
  fuentes trollmaleshop1/2 y zombietrollshop:21 registros y12 recursos asociados.
  No se investigaron sus fallos ni se modificaron las demás pieles o rasgos.
  Los IDs e índices retirados no se reutilizan ni se renumeran los conservados.
- Sus rostros son prefijados del mismo atlas, con aliases Face0–4/0–5; no son
  cinco/seis caras distintas. Se mantienen ropa interior adaptada y prendas ya
  pintadas en las fuentes; no se retocan esos cuerpos en esta conversión.

## Corrección de todas las caras opcionales

La prueba A/B masculina Skin24 fue confirmada por el usuario: «ahora si funciona
perfectamente». Las **36 texturas conservadas**,18 masculinas y18 femeninas,
usan esa representación, exclusivamente FaceLower/FaceUpper de las18 pieles.

- BLP2 paletizado, encoding1/preferredFormat8, mip inicial1172.
- Dimensiones, recortes, paths, referencias DBC y alpha de todos los mips
  conservados. No se cambian pelo, rasgos faciales, Forest, cuerpos o ropa interior.
- **36 caras mantienen exactamente el RGBA superior**, sin cuantización.
- Las seis caras de tienda que necesitaban reducción RGB pertenecían a las tres
  pieles retiradas; ya no forman parte del opcional. No se ha alterado la
  conversión ni el contenido de las36 caras que permanecen.
- La pareja masculina100 es byte-idéntica al A/B aceptado. La conversión no
  demuestra qué campo concreto del formato anterior causaba el fallo, ni que
  todo BGRA sea incompatible con el ejecutable.

Las dos texturas de rasgos faciales reparadas durante v2 permanecen sin cambios;
no se confunden con estas36 caras de piel. Su alpha paletizado debe leerse del
plano separado, no del cuarto byte de paleta que Pillow13 puede interpretar mal.

El [contrato histórico v2](troll-customizations-v2.md) conserva la investigación,
composición aproximada de ropa y diagnóstico originales; no es la receta actual.

## SQL principal y opcional

| Unidad | Filas SQL propias | Registro |
|---|---:|---|
| Forest |90| Manifiesto normal, archivo original intacto |
| Principal: pelo +rasgos |208 =117 overrides nativos +91 nuevos| `data/sql/custom/db_world/turtle_troll_customizations.sql` |
| Pieles opcionales |135| `data/sql/optional/db_world/turtle_troll_extra_skins.sql`, fuera del manifiesto normal |

**Principal:298 overlays** en total y9139 registros lógicos efectivos (117
overlays sustituyen IDs binarios ya existentes). **Con opcional:433 overlays**
y9274 registros efectivos. Las asignaciones originales20100–20346 se conservan,
excepto21 IDs retirados; no se renumeran para hacer rangos nuevos contiguos.

La instalación estándar usa los dos scripts existentes: parches fuente y world
SQL con `--with-server-data` para los siete estilos naturales. Esta división
no cambia el manifiesto de archivos servidor de431 entradas ni sus binarios.
Ambas ediciones usan los mismos229 estilos faciales servidor.

Para activar los metadatos opcionales después de la instalación principal,
detener el servidor y, desde el checkout:

```sh
SQL_DIR="$PWD/data/sql/optional/db_world" scripts/apply-db-world.sh --validate
SQL_DIR="$PWD/data/sql/optional/db_world" scripts/apply-db-world.sh
```

El manifiesto opcional tiene una sola entrada. El SQL exige coincidencia exacta
de Forest90 +principal208 antes de insertar135. Comprueba también los21 registros
retirados y elimina únicamente copias presentes e idénticas, migrando perfiles
opcionales antiguos156→135 sin otro paso manual. Acepta repetición idéntica y
rechaza colisiones de ID/tupla/campos, incluidos los retirados. La instalación principal normal **no
desactiva un opt-in existente** al repetirse. Para perfiles heredados de v2 hay
que ejecutar el rollback selectivo opcional si se quiere volver a principal.

Los scripts mantienen preparación InnoDB/guardas transaccionales; la migración
MyISAM→InnoDB no se revierte. SQL+archivos siguen sin ser una sola transacción.
No usar --force ni borrar rutinas ajenas ante conflictos.

### Bots, personajes existentes y clientes mezclados

La configuración principal excluye las156 filas opcionales de su store, para
que las rutas de generación de bots basadas en CharSections no elijan esas
caras/pieles nuevas. Esto no implementa un validador de apariencia: el core
inspeccionado conserva su TODO. Quitar un overlay no cambia los bytes ya
guardados ni constituye un bloqueo de paquetes de creación modificados.

Un personaje existente con Skin24+ sigue necesitando la edición opcional para
ser representado correctamente. **No se cambian sus apariencias automáticamente.**
Para volver a principal, recustomizar esos colores con el cliente opcional aún
instalado. Activar SQL no distribuye texturas: todos los clientes que vean esos
personajes necesitan la edición con los recursos opcionales. No se garantiza
renderizado correcto en un cliente principal que carece de ellos.

## Desactivar opcional y rollback

Con servidor detenido, el rollback selectivo es:

```sh
mysql --login-path=azeroth-dev acore_world \
  < data/sql/rollback/turtle_troll_extra_skins.sql
```

Elimina las135 filas actuales y limpia los21 registros retirados si proceden
de una versión anterior, siempre presentes e idénticos; deja Forest90 y principal208.
Repetirlo es seguro, siempre sujeto a sus guardas. Después de recustomizar
personajes opcionales, sustituir el S por la edición principal y reiniciar.
No quitar los siete estilos de servidor ni volver a v1: se perderían rasgos
faciales que se quieren conservar.

El rollback principal `data/sql/rollback/turtle_troll_customizations.sql`
elimina208 filas, **no** Forest; rechaza ejecutarse si permanecen IDs opcionales.
Es desinstalación de pelo/rasgos, no el cambio opcional→principal solicitado.
Los SQL364 de `data/sql/history/troll-v2-full/` son referencias para reconstruir
y probar v2, no scripts actuales de activación/desactivación.

## Construcción y comprobación

```sh
python3 tools/build_troll_patch_editions.py --output work/troll-editions-nuevo
```

Usar el entorno de `tools/troll-customizations-requirements.txt`. Por defecto
reconstruye la base v2 desde MPQ originales fijados por hash. La opción
`--base-version current` utiliza la v2 archivada y verificada, no acepta la principal como base
completa. Los dos caminos generan los mismos productos. `--publish` verifica
identidades y todos los destinos antes de reemplazar archivos propios; no es
un instalador de clientes/BD y no admite un force genérico.

La v2 sin corrección se preserva bajo `client_patches/turtle_forest_troll/v2/`;
v1 y el A/B aceptado también permanecen intactos. El builder v2 antiguo debe
rechazar publicar encima de las ediciones actuales. Sus tests usan la copia
histórica, no confunden el SQL208 con el anterior364.

SHA256 de las publicaciones:

| Edición | MPQ |
|---|---|
| Principal | `2bd2ce7adb7bf678f110b8be43d8e0fd5eb168c522e6857eff17f15c3d455ce8` |
| Opcional | `2890f2b54fc99edfae948d8dceccb21edbfee26fd8089ec7f2a5a370b2dda6e4` |

## Validación y límites

- **PASS:** retirada exacta de21 filas y12 recursos del opcional, conservación
  de todas las filas/recursos restantes y hash principal sin cambios. La edición
  queda9+9, sin colores masculinos33–35. Sin investigación de sus problemas.
- **PASS:** seis pruebas de ediciones, con reconstrucciones deterministas,
  upgrade SQL156→135, rollback a298 y preservación de datos ajenos. El SQL y los
  archivos principales conservan sus bytes; solo se refresca metadata informativa.

- **PASS:** las regresiones previas de v2/A-B/helper y la comparación de paquetes
  establecieron la conservación de Forest, pelo y rasgos. La retirada actual
  verifica adicionalmente que el MPQ principal y cada payload opcional conservado
  coinciden byte a byte, sin nuevos cambios de píxeles.
- **PASS:** las pruebas privadas de SQL cubren principal208, opt-in135 y limpieza21,
  requisitos exactos, conflictos, repetición y rollback sin perder Forest ni
  pelo/rasgos. La publicación verifica desconocidos/estados parciales.
- **PASS:** consulta de DEV:298 overlays principales y ningún registro ni
  personaje masculino con los colores retirados33–35. No hizo falta aplicar SQL
  ni reiniciar servicios para esta retirada. No se modificaron personajes.
- **PASS:** validación de manifiestos/checksums y revisión independiente de la
  retirada. La DBC facial y los SQL principales permanecen intactos.
- **NOT RUN:** aceptación visual exhaustiva de todas las caras conservadas;
  combinaciones exhaustivas/DK, equipo, relog, otro cliente
  y HD. El éxito del A/B no se extrapola a todas ellas. Los clientes originales
  y el cliente jugado no fueron modificados por el agente.
