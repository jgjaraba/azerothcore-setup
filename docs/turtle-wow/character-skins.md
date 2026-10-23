# Pieles raciales de Turtle en la creación de personajes 3.3.5a

## Dictamen y alcance

**Viable como port selectivo de texturas y componentes**, usando el selector
nativo «Color de piel». Se conservan raza, modelo racial WotLK, animaciones,
equipo y almacenamiento normal de apariencia. No se propone un sistema de
morphs, auras, disfraces, display IDs alternativos ni nuevas razas.

La procedencia gratuita o de donación no determina la compatibilidad: una
apariencia comprada puede aportar una textura racial aprovechable. No se propone
portar el pago, el objeto de tienda ni su activación; las variantes adaptadas
deben ser elegibles desde creación. Esto **no demuestra que todas** puedan
portarse sin trabajo artístico ni que el snapshot contenga la tienda actual
completa. El catálogo general sigue en investigación; el
[piloto ForestTroll](forest-troll-skins.md) aceptado se conserva dentro de la
[ediciones Troll principal/opcional](troll-customizations.md). La principal
conserva Forest, pelo y rasgos; las pieles restantes y sus caras convertidas se
reservan a la opcional, cuya aceptación completa es separada.

## Evidencia local y reproducción

Se examinaron `/home/dev/wow-turtle` y `/home/dev/wow-335` sin modificarlos. El
segundo no se supone el cliente jugado. La auditoría inventaría22 MPQ Turtle y38
MPQ335 con hashes, candidatos DBC, referencias y recursos. La prioridad por
nombre es una **aproximación**, no una prueba del loader ejecutable, de overrides
loose o de carga simultánea de locales.

```sh
python3 tools/audit_turtle_skins.py --output work/skins-audit-nuevo
python3 -m unittest discover -s tools -p 'test_audit_turtle_skins.py' -v
```

Requiere los snapshots y `tools/mpq` preparado según la guía de migración. La
salida debe ser nueva, dentro de `work/`; se rechazan cachés reutilizadas para
no atribuir recursos antiguos a archivos actualizados. Informes generados:

- `archives.json`: procedencia, tamaños, fechas y SHA256 de los MPQ.
- `dbc-audit.json`: candidatos, filas y cadenas de siete tablas por cliente.
- `catalog.md`, `skin-deltas.json`, `extra-source-rows.md`: colores, flags,
  referencias y filas exactas, incluidos cuerpo/cara/ropa interior.
- `shop-baked-catalog.json`: cadena display → Extra → modelo racial → textura.
- `resources.json`, `model-uv-comparison.json`: recursos extraídos y cribado
  limitado de UV, no validación de renderizado.

En el snapshot auditado, los candidatos CharSections son Turtle `patch-8.mpq`
(6617 filas; SHA256 `40f020b68e087141f779c3eae91c7a9a602f73a5b2f7aad0cac68313fb403c48`)
y335 `patch-*-3` de locale (8958 filas; enUS/esES idénticos, SHA256
`18fc8d23f6e66598ab1681a74f90239ebdf84b76f300db0865cdad7d042b833f`).
Las tablas raciales/display Turtle candidatas vienen de `patch-9.mpq`.

## Qué existe realmente

Hay295 filas de cuerpo Turtle:196 con flag0 y99 con flag1. **No equivalen a295
skins extra ni a99 compras**. Muchas filas alternas comparten color con las
ordinarias; un flag Vanilla no acredita venta o selección gratuita.

| Raza destino | Cuerpos ordinarios Turtle H/M¹ | Cuerpos ordinarios335 H/M¹ | Hallazgos útiles |
|---|---:|---:|---|
| Humano |10/10|10/10|Alternos Necro/Wizard/Pirate; bakes de magos, nigromante y otros humanos |
| Orco |9/9|9/9|Trece cuerpos alternos entre sexos; Chaos explícito y variantes numeradas; siete bakes masculinos de tienda |
| Enano |14/14|9/9|Cuatro colores nuevos por sexo en Skin00_12–15; otro comparte nombre con DK335; bakes Wildhammer/Dark Iron/Earthen |
| Elfo de la noche |11/11|9/9|Colores9–10 coinciden en nombre con DK335; alternos DemonHunter/Druid y bakes prefijados |
| No-muerto |6/6|6/6|DeathKnight/BloodWidow; bakes deathknightundeadshop y wightundeadshop; caras color6 sin cuerpo ordinario equivalente |
| Tauren |20/12|19/11|Colores extra que coinciden con DK335, alternos GrimTotem y bake Spirit Walker |
| Gnomo |6/6|5/5|Color extra que coincide con DK335, alternos Leper/Necro y dos bakes masculinos |
| Trol |12/12|6/6|ForestTroll con cuerpo/cara/ropa interior; alternos numerados y bake Zombie Troll |
| Elfo de sangre |11/11²|10/10|Alto Elfo/BloodElf, Dark Ranger y otros alternos; adaptar a raza10 nativa |
| Draenei |—|nativo335|No se identificó una colección Turtle equivalente de personalización racial jugable |

¹ H/M = hombre/mujer; «ordinario» significa flag0 en Turtle y PLAYER sin DK en335,
no una equivalencia comercial o prueba visual. ² Es la raza **Alto Elfo** Turtle,
no una nueva raza que deba añadirse al destino.

### Candidato de menor riesgo: trol del bosque

Las filas cuerpo4762–4767 masculinas y5105–5110 femeninas usan colores6–11 y
texturas `Character\Troll\...\ForestTroll...`. Existen familias de cara inferior/
superior, pelvis y torso. **No hace falta convertirse en el modelo NPC
ForestTroll** para ensayar esas pieles. No acredita todavía UV, combinaciones o
selección efectiva en335.

### Tienda: recursos, no opciones listas

Se localizaron38 texturas `*shop*.blp`, presentes en los listados Turtle patch-6
y ausentes a esas rutas en los335. Están enlazadas mediante Extra15735–15749,
15751,15753–15774 y display20962–20999. **Todas esas cadenas concretas terminan
en modelos `Character\...` raciales**, no modelos `Creature\...`.

Ejemplos: wildhammershop1–4, darkironshop, earthenshop, lepershop,
necrognomeshop, spiritwalkertaurenshop, zombietrollshop, orcmaleshop1–7,
rangershop, bloodelfshop y los dos bakes no-muertos citados arriba. Es evidencia
favorable para estudiar un port de texturas, **no38 skins distintas garantizadas
ni una lista comercial completa**. Los99 alternos y estos38 bakes no se suman
como productos diferentes.

Un bake NPC puede incluir rostro, marcas o ropa fijados. Antes hay que determinar
qué componentes reutilizar, separar o reconstruir. No basta con añadir su display
a creación: debe resolver una familia coherente CharSections, incluso si se
decide conservar un rostro prefijado para una variante.

## Catálogo gratuito/donación: alcance de las fuentes

Las fuentes públicas sirven para nombres y adquisición histórica. Muchas
texturas numeradas siguen sin identidad comercial exacta acreditada.

- **Equipo Turtle, parche1.16.0:** nuevas opciones de creación para enanas
  Wildhammer y trolas del bosque; también cuernos tauren, que no son una piel [2].
- **Catálogo histórico de donación, expresamente desactualizado:** Blackrock,
  Chaos, Dreadskull y Mag’har orcos; Dark/Forest/Ice/Zombie/Sandfury trolls;
  Spirit Walker; Dark Iron/Earthen/Dwarf Death Knight; Leper y Scholomance
  Student; humanos Scholomance/Death Knight/Sally Whitemane; Blood Elf y Dark
  Ranger para Alto Elfo [3]. Hay restricciones por sexo [4].
- **Otras evidencias históricas:** Cultist humana y Demon Hunter elfo nocturno;
  no está probado que Cultist, Scholomance y Necromancer sean el mismo producto.
  Las verdes de creación y las antiguas Forest/Revantusk o Sand/Farraki de
  tienda no deben fusionarse por nombre [5].
- **No acreditado:** Highborne oficial comprable/creable, un conjunto Forsaken
  «elfo no-muerto», o esqueletos como pieles nativas. Peticiones/mods comunitarios
  y modelos NPC no prueban esas opciones.

El Lua `turtle_shopui.lua` recibe categoría, nombre, precio, ítem, modelo y sexo
**del servidor**. Los MPQ no certifican todas las ventas actuales ni exclusividad
de donación; algunas apariencias también se obtienen jugando.

## Contrato técnico

### Cliente: componentes y flags, no copiar tablas enteras

Ambos CharSections tienen10 campos, pero **en diferente orden** [1]:

```text
Vanilla/Turtle: ID Race Sex Base Variation Color Texture1 Texture2 Texture3 Flags
WotLK335:      ID Race Sex Base Texture1 Texture2 Texture3 Flags Variation Color
```

Base0 es cuerpo; Base1 usa Face como Variation y **Skin como Color**; Base4 usa
el mismo Skin para ropa interior. Bases2/3 usan HairColor para barba/pelo.
No existe un byte FaceColor independiente en creación.

Importar familias coherentes por raza/sexo/color: cuerpo, superficies extra,
caras permitidas y ropa interior. Mantener peinados/geosets WotLK salvo necesidad
específica. Hay11 filas de ropa interior con alguna referencia no resuelta en
listados Turtle (5090–5092,5410–5412,6151–6155): investigar antes de incluirlas,
sin confundir ausencia en listfile con fallo de carga demostrado.

En335 se observan cuerpos normales0x11, DK0x05 y NPC0x08; el core define PLAYER
0x01 y DK0x04. No trasplantar flags Vanilla ni habilitar todos los NPC. Preservar
IDs y colores existentes, incluidos DK, y comprobar colisiones de tupla e ID.

`CharacterCreate.lua` tiene cinco controles y llama a `CycleCharCustomization`;
el primero es Skin Color. No hace falta un sexto control para más colores.
Los nombres «Mag’har», «Wildhammer», etc. no forman parte de esta DBC: un selector
con nombres exigiría UI adicional. El cycling está en el ejecutable; la posterior
inspección estática del [piloto ForestTroll](forest-troll-skins.md) establece
max+1, salto de huecos y fallback cara/color para el binario de referencia.
Su aceptación en juego sigue pendiente.

Los M2 Turtle observados son versión256 y los335 son264. El cribado de vértices/
UV compartidos encuentra coincidencias parciales, no equivalencia completa.
Preservar modelos WotLK y comprobar/reproyectar las texturas individualmente.
Dimensiones BLP o nombres iguales no prueban compatibilidad. HD no validado.

### Servidor: persistencia nativa y overlay SQL

El handler y CharacterCreateInfo reciben Skin, Face, HairStyle, HairColor y
FacialHair como bytes. Player los empaqueta en PLAYER_BYTES/PLAYER_BYTES_2;
save/login y enumeración usan `characters.skin`, `face`, `hairStyle`, `hairColor`,
`facialStyle`. Rango0–255: **256 valores**, no garantía de256 opciones de UI.
El display sigue dependiendo de raza/sexo, no del nuevo color.

En este checkout `Player::Create` **no valida apariencia contra CharSections**:
lo deja como TODO. No atribuirle Player::ValidateAppearance de TrinityCore ni
declarar obligatorio un parche core para aceptar cada nueva piel.

Existe `charsections_dbc`, cargado después del binario con formato `diiixxxiii`.
Puede contener el delta servidor con columnas explícitas
`Id,Race,Gender,GenType,TexturePath1–3,Flags,Type,Color`, sin sustituir la DBC
servidor. Los paths se ignoran en el formato del core. Mantener coherencia por
filas/tuplas, no igualdad de hashes completos. El SQL **no se envía al cliente**
y el store se refresca al arrancar.

Fuentes locales: CharacterHandler.cpp/WorldSession.h, Player.cpp (Create,
InitDisplayIds, BuildEnumData, SaveToDB), PlayerStorage.cpp, DBCStructure.h,
DBCfmt.h, DBCStores.cpp y DBCDatabaseLoader.cpp del checkout AzerothCore.
No se hizo una prueba real de creación/save/relog para estas variantes.

### Módulos y límites de raza

Playerbots sí consume CharSections para cara/color, sin filtrar flags DK/clase
en el factory inspeccionado; ampliar caras puede cambiar sus elecciones.
Character Services usa recustomización nativa: las variantes podrían aparecer
allí también. «Desde creación» no se interpreta como «exclusivo de creación».
La barbería tiene otro contrato, no queda garantizada por estas filas.

Turtle9 es Goblin jugable;3359 es NPC. Turtle10 es Alto Elfo;33510 es Elfo de
sangre. No copiar ChrRaces ni añadir esas razas nuevas en este trabajo. No hay
colección racial jugable Turtle Draenei equivalente. Skeleton/FelOrc y las
ilusiones Worgen u otras criaturas no se habilitan como supuestas pieles;
raza33512 es FelOrc NPC, no Worgen.

## Implementación recomendada y aceptación pendiente

1. Manifiesto por apariencia: nombre/procedencia, recursos, raza/sexo, componentes
   y compatibilidad. No asignar nombres comerciales a `_100` por conjetura.
2. Pilotar **un color ForestTroll**, con familia completa y modelo Troll WotLK
   intacto. Verificar ambos sexos y no pisar DK.
3. MPQ aditivo que preserve las DBC/overrides del proyecto. Delta servidor en
   SQL/manifiesto world del flujo existente; cliente conservado en el repositorio
   con copia manual e instrucciones README.
4. Extender a las demás familias gratuitas y a materiales de tienda, sin portar
   sus mecanismos de pago o morph.
5. Probar preview, cycling bidireccional, aleatorio, cambio de raza/clase, caras/
   pelo, desnudo/con equipo, creación, lista de personajes, relog y visión desde
   otro cliente parcheado. Preservar normales/DK, personajes existentes,
   recustomización y generación de bots; HD por separado.

**PASS:** auditoría local reproducida en salida nueva, esquemas y referencias
examinados, cuatro tests sintéticos y contrato servidor verificado en fuente.
**NOT RUN:** renderizado, selección real de nuevos colores, creación/relog,
aceptación regular/HD y catálogo comercial actual exhaustivo. El estudio inicial
no desplegó cambios; el contrato y despliegue del primer piloto se registran
separadamente en [ForestTroll](forest-troll-skins.md).

## Referencias públicas

[1] [WoWDev: CharSections, esquemas por versión y componentes](https://wowdev.wiki/DB/CharSections).

[2] [Equipo Turtle: parche1.16.0, opciones añadidas a creación](https://web.archive.org/web/20260429093730/https://forum.turtlecraft.gg/viewtopic.php?f=2&t=2253).

[3] [Token Shop Skins — catálogo histórico que advierte estar desactualizado](https://web.archive.org/web/20260507081411/https://forum.turtlecraft.gg/viewtopic.php?p=18203).

[4] [Equipo Turtle: restricciones por sexo y preview de tienda](https://web.archive.org/web/20260421195826/https://forum.turtlecraft.gg/viewtopic.php?t=18419).

[5] [Discusión sobre cambios Dark/Forest/Farraki y tonos de creación](https://web.archive.org/web/20260422114628/https://forum.turtlecraft.gg/viewtopic.php?t=23389).

[6] [Galería oficial de personalización — snapshot2026-10-14, no catálogo comercial](https://web.archive.org/web/20261014115428/https://turtlecraft.gg/character-customizations).
