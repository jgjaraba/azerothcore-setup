# ForestTroll: pieles nativas para creación335

Este es el contrato **v1 aceptado**, conservado byte a byte en
`client_patches/turtle_forest_troll/v1/`. Las
[ediciones actuales de patch-S](troll-customizations.md) incluyen estas pieles sin
cambiarlas. Las instrucciones/hash v1 siguientes son referencia del piloto,
no una orden de sustituir la publicación actual por una reconstrucción antigua.

## Contrato

Se añaden seis tonos para cada sexo a la **raza Troll8 existente**, usando su
modelo WotLK intacto y el control Color de piel. No se cambian raza, facción,
displays, animaciones, geosets, pelo, hechizos ni mecánicas. No es un morph.

- Colores nuevos **18–23**; se conservan normales0–5, NPC6–14 y DK15–17.
-90 filas nuevas, IDs CharSections **20000–20089**:42 masculinas y48 femeninas.
- Cuerpo, caras y ropa interior coherentes; caras masculinas0–4 y femeninas0–5.
- Flags **0x11** en los componentes nuevos: elegibles ordinarios y DK.
-162 BLP2 originales de Turtle, byte-idénticos, bajo el namespace aislado
  `Character\Custom\TurtleForestTroll\Male|Female\...`.
- Cliente: CharSections8958 filas originales →9048, sin alterar sus bytes de
  registros ni el prefijo original de cadenas. Se ordenan físicamente por
  Race/Sex/Base/Variation/Color; no se concatenan las filas al final.
- Servidor: delta SQL `charsections_dbc`; no se sustituye la DBC binaria nativa.
  Guardado y relog usan los bytes/columnas de apariencia existentes.

La cobertura deliberada no incluye inventar caras DK adicionales para estas
pieles, otros colores NPC, nuevos modelos o compatibilidad HD no probada.

## Fuentes y reproducción

Decisiones/hash de entradas: `tools/forest-troll-skins.json`. El builder lee los
snapshots originales, no JSON de auditoría o intermedios históricos de `work/`:

```sh
python3 tools/build_forest_troll_skins.py --output work/forest-build-nuevo
FOREST_TROLL_INTEGRATION=1 \
  python3 -m unittest discover -s tools -p 'test_forest_troll_skins.py' -v
```

Necesita `tools/mpq` y los archivos fijados del cliente Turtle/reference335.
`--publish` conserva los outputs propios idénticos en el repositorio; rechaza
sobrescribir archivos publicados diferentes. La instalación **no** necesita
ejecutar el builder: los MPQ y SQL finales ya se conservan en el árbol privado.

Se seleccionan solo raza8, sexo0/1, bases0/1/4, colores Turtle6–11, flag0. Los
colores destino son origen+12. Son familias completas; las referencias no
resueltas de otras filas de ropa interior de la investigación no se incluyen.

Procedencia de cuerpos masculinos4762–4767 y femeninos5105–5110, caras y ropa
interior de la misma familia. Las texturas proceden de patch-3 masculino y
patch-5 femenino; CharSections Turtle de patch-8, convertido explícitamente al
layout335. La base cliente es CharSections de esES patch-3, SHA256
`18fc8d23f6e66598ab1681a74f90239ebdf84b76f300db0865cdad7d042b833f`,
idéntico a la base enUS auditada. Los hashes completos de archivos MPQ fuente
se registran en el manifiesto; no se infiere su prioridad al construir.

## Por qué esos índices funcionan en el selector

Inspección estática del `Wow.exe` de referencia, SHA256
`bf644876709c591acc17c0da8cdf1814edcc9f1e6bc109a8c0d5c38c79dc953c`:

- Indexador CharSections `0x004F3DD0`: grupos contiguos y límites max+1.
- Lookup `0x004F3BA0`: clave Race/Sex/Base/Variation/Color; **no incluye flags**.
  Duplicar una tupla con otros flags no crea dos opciones: una fila la oculta.
- Skin adelante/atrás `0x004EB150`/`0x004EB290`: omite huecos/ineligibles y
  comprueba cuerpo, cara actual y ropa interior. No exige colores densos.
- Predicado `0x004F39A0`: ordinario requiere PLAYER y excluye bits0x0C; DK
  requiere PLAYER, algún bit0x14 y excluye NPC0x08.0x11 funciona para ambos.
- Face `0x004EB710`/`0x004EB990` busca una combinación válida y puede cambiar
  Skin si la cara candidata no sirve con el color actual. Fallbacks en
  `0x004EB962` y `0x004EBBE0`.

Por eso no hay que sobrescribir NPC6–14 ni mover DK15–17 para añadir18–23.
La evidencia es estática, **no una prueba de UI ejecutada**. Las direcciones y
nombres descriptivos corresponden a ese binario, sin símbolos, no a todo cliente.

### Particularidad de DK

Las caras DK antiguas5–9 masculinas y6–11 femeninas no existen en las nuevas
pieles. Si se parte de una de ellas, Skin puede omitir ForestTroll hasta cambiar
Face. El fallback nativo de Face permite llegar a una cara compatible y otro
color; no hay un callejón sin salida que requiera clonar caras.

Prueba concreta pendiente: varón DK Skin0/Face5 → Face adelante hasta0 cambia
a Skin15; mujer DK Skin0/Face6 → Face adelante hasta0 también llega a Skin15.
Después Skin recorre15,16,17,18…23. Cambiar a una cara DK exclusiva puede volver
a cambiar el color. No se promete independencia de todos los pares cara/piel.

## Aplicación servidor y cliente

SQL propio: `data/sql/custom/db_world/turtle_forest_troll_skins.sql`, registrado
en el manifiesto world. Para instalación general se usa `apply-db-world.sh`;
para desplegar solo esta unidad en DEV, con el servidor detenido:

```sh
mysql --login-path=azeroth-dev acore_world \
  < data/sql/custom/db_world/turtle_forest_troll_skins.sql
```

El esquema stock inspeccionado tenía `charsections_dbc` **MyISAM**. APPLY admite
MyISAM/InnoDB y convierte MyISAM a InnoDB antes de la transacción de filas.
Requiere ALTER y privilegios de rutina. **Esa DDL hace commit implícito y no
es parte del rollback transaccional**; puede persistir aunque después falle
una guarda. El rollback de la función no vuelve a MyISAM ni borra filas ajenas.

Las guardas comprueban ID y tupla semántica, comparan campos exactos y aceptan
repetición idéntica. No usar `mysql --force`. Un CALL fallido revierte filas,
pero puede dejar la rutina auxiliar; inspeccionar el conflicto y retirar solo
`azerothcore_setup_forest_troll_skins` (o su `_rollback`) antes de reintentar.
La tabla temporal desaparece al cerrar esa conexión. Reiniciar para recargar
el store SQL; no hace falta recompilar el core.

Cliente v1 archivado: copiar `client_patches/turtle_forest_troll/v1/Data/patch-S.MPQ` a
`Data/patch-S.MPQ`, con WoW cerrado, según el README principal. El MPQ contiene
solo CharSections, las162 texturas y su listfile. No sustituye los parches de
cripta T/Z/esES-Z; en los archivos auditados esos parches no aportan CharSections.
Otro mod que aporte esa tabla o modelos Troll requiere fusión/auditoría propia.
No instalar automáticamente sobre un patch-S ajeno ya existente.

SHA256 del MPQ:
`b97b993d317709578f4bc6af51d6bd7e04197b9ba6a0842ee5443a5c3c085a75`.
Comprobar `SHA256SUMS` desde `client_patches/turtle_forest_troll/v1/`.
Todos los clientes que vean esos personajes necesitan los datos.

## Rollback

Antes de retirar el parche, recustomizar cualquier Troll con Skin18–23 para
evitar dejar bytes que el cliente anterior no sepa representar. No se borran
personajes ni se migran sus apariencias automáticamente. Después, detener el
servidor y ejecutar el rollback específico, **fuera del manifiesto de aplicación**:

```sh
mysql --login-path=azeroth-dev acore_world \
  < data/sql/rollback/turtle_forest_troll_skins.sql
```

Solo elimina filas propias presentes e idénticas; ante cambios ajenos falla.
Mantiene InnoDB. Retirar/restaurar únicamente el patch-S propio con WoW cerrado,
con backups fuera de Data, y reiniciar el servidor. Una instalación futura del
manifiesto normal vuelve a aplicar la función mientras siga registrada.

## Validación y aceptación

- **PASS:**14 tests con integración de clientes fijados; dos builds separados
  idénticos, roundtrip de cada miembro MPQ,162 cabeceras/mips BLP2 válidos,
  conservación de8958 filas/cadenas originales, cero colisiones nuevas.
- **PASS:** SQL en MySQL8.4.11 privado:58 ejecuciones y70 comprobaciones, con y
  sin NO_BACKSLASH_ESCAPES. Cubre migración MyISAM, apply/reapply, rollback,
  casos ID/tupla/flags/case/espacios y preservación ajena. La prueba admite DDL
  fuente ya migrada, pero establece MyISAM solo en su instancia privada.
- **PASS:** en DEV se aplicó/reaplicó, revirtió dos veces a cero filas y volvió
  a aplicar/reaplicar; estado final90 filas e InnoDB. Reinicio completado con
  stores inicializados y worldserver ready. Esto no demuestra por sí solo cada
  lookup de su store en memoria ni la apariencia visible en un cliente.
- **PASS — aceptación práctica confirmada por el usuario:** «las pieles están
  correctamente implementadas». Es una confirmación del usuario, no una prueba
  de cliente ejecutada por el agente. Cierra la aceptación práctica del piloto,
  sin certificar individualmente una matriz de sexos, caras, clases o clientes.
- **NOT RUN por el agente / sin confirmación específica del usuario:** matriz
  exhaustiva de cycling/DK, render/UV/equipo, aleatorio, creación/relog/lista,
  recustomización, bots, otro cliente y variante HD. La confirmación general no
  acredita cada caso. Los snapshots originales no fueron modificados por el agente.

Checklist de regresión: trol hombre/mujer de clase normal, seis tonos nuevos y
todas sus caras, pelo/colores normales, ida/vuelta5↔18 y cierre del ciclo; DK con
el fallback Face descrito, sin entrar en colores NPC6–14; equipo, crear, relog,
lista de personajes y comprobación desde otro cliente parcheado. No extrapolar
la aceptación práctica a combinaciones o variantes no comprobadas expresamente.
