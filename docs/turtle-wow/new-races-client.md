# Altos Elfos y Goblins — fase cliente aditiva 3.3.5a

> **Contrato histórico del candidato. Instalación vigente:** seguir
> [`client_patches/README.md`](../../client_patches/README.md) para la entrega
> consolidada regular/HD. No instalar este paquete ni los antiguos paquetes r5
> como capas adicionales. Las ediciones parciales están archivadas.

## Estado y alcance

**Previsualización aceptada con alcance acotado.** El usuario confirmó correctos
el Alto Elfo22 masculino y el Goblin23 femenino; el aviso posterior de fallo del
Goblin femenino fue un error de prueba del usuario, no una regresión confirmada.
La entrega consolidada **regular**, enUS y esES, se ejecutó en Linux con Wine10,
Direct3D9/WineD3D, Xvfb y Mesa llvmpipe: PASS de arranque/autenticación/selección,
doce opciones, diez razas originales con encabezados localizados, ambos modelos
nuevos muestreados y18 posiciones de cycling de piel/cara de Goblin femenino.
Son posiciones sucesivas observadas, no índices nativos consultados ni una matriz
exhaustiva. No es una ejecución en Windows nativo ni una prueba de gameplay o HD.
Evidencia: [`RESULTS.md`](../../work/consolidated-native-locale-ownership/RESULTS.md).

No se modifica el servidor, SQL, bases de datos, cuentas o runtime. **Crear,
guardar y jugar** personajes de las nuevas razas requiere una fase servidor
posterior. El servidor actual puede rechazar su creación; no es una activación
de gameplay ni una migración de zonas iniciales.

## Identidades y clases

| Nueva raza | ID | Equipo | Clases del snapshot Turtle |
|---|---:|---|---|
| Alto Elfo / TurtleHighElf |22|Alianza|Guerrero, Paladín, Cazador, Pícaro, Sacerdote, Mago|
| Goblin / TurtleGoblin |23|Horda|Guerrero, Cazador, Pícaro, Mago, Brujo|

La fuente real es CharBaseInfo de Turtle patch-9,59 registros de **dos bytes**.
No se infieren clases de los outfits: contienen combinaciones adicionales que
no son jugables en esa fuente. No se añaden DK, chamán o druida a las dos razas.

Se conservan **todas las filas nativas1–21**, incluido Goblin NPC9 y Elfo de
Sangre10, sus modelos, displays y assets. La tabla de clases mantiene las72
combinaciones del proyecto y añade11: **83**. No se sustituye otra raza jugable
ni se mueve una raza NPC para liberar su número.

Los vínculos nuevos de display/modelo son91000–91003; outfits90000–90021. Los
faction templates1/2 aseguran pertenencia cliente Alianza/Horda. Son un contrato
de preview: reputaciones, raciales, skills, stats y facciones propias se diseñan
en la fase servidor. La expansión requerida es0; cinematics0. Los prefijos de
equipo Be/Go se conservan, pero la adaptación de cascos no está validada.

## Paquete histórico y orden de carga

Candidato histórico bajo `client_patches/new-races/`; las rutas opcionales del
listado son relativas a ese directorio y ahora apuntan al archivo:

```text
Wow-new-races.exe
Wow-new-races.report.json
SHA256SUMS
primary/Data/patch-Z.mpq
primary/Data/esES/patch-esES-Z.MPQ
../archive/new-races/optional-extra-skins/Data/patch-Z.mpq
../archive/new-races/optional-extra-skins/Data/esES/patch-esES-Z.MPQ
assets-report.json
assets-validation.json
assets-SHA256SUMS
```

Cada pareja Z histórica era una **alternativa completa y coordinada**. Procede de las copias
Z aceptadas de la cripta, preservando sus otros miembros. Se repiten los nuevos
datos/recursos en root y locale para que ambos aporten el mismo contrato. Un
parche anterior a S no bastaría: S y Z contienen DBC completas y podrían ocultar
las nuevas filas. No se modifica ninguno de los paquetes S aceptados.

La edición `primary` conserva como base el S principal vigente; la
`optional-extra-skins` conserva el opcional. No mezclarlas: Z determina las DBC
ganadoras de las nuevas razas y la edición elegida de personalización previa.
Conservar **el S correspondiente**, el T de la cripta y los MPQ originales.
El paquete está auditado contra el snapshot/edición esES; otra cadena custom,
HD u otra locale necesita su propia revisión, no un overwrite indiscriminado.

### Procedimiento histórico del candidato, no instalación vigente

Los pasos siguientes describen exclusivamente el antiguo candidato esES. Para
instalar hoy, usar la guía consolidada enlazada arriba, sin reaplicar estos Z.

Para actualizar desde la primera entrega con el fallo de texturas, bastan los
dos Z nuevos de la edición elegida: **mantener el mismo EXE87ce…, S y T**. Cerrar
WoW completamente antes de sustituir los dos archivos; actualizar solo root Z
puede dejar la copia locale antigua ganando prioridad.

1. Verificar `sha256sum -c SHA256SUMS` desde `client_patches/new-races/`.
2. Cerrar WoW. Trabajar en una copia del cliente compatible; respaldar los Z
   que se reemplazarán **fuera de Data**, guardando también el estado anterior
   de los archivos que no existían. No dejar duplicados que solo cambien en caso.
3. Elegir **una** edición y copiar sus dos archivos a los mismos paths bajo el
   cliente: `Data/patch-Z.mpq` y `Data/esES/patch-esES-Z.MPQ`.
4. Copiar `Wow-new-races.exe` a la raíz de esa copia del cliente y **lanzar ese
   ejecutable**, no el original. No hace falta sobrescribir `Wow.exe` ni modificar
   el directorio de referencia. El derivado requiere los archivos/DLL nativos
   del cliente junto a él. El launcher habitual puede seguir lanzando el original.
5. Entrar hasta creación y comprobar las doce opciones. No interpretar un botón
   visible como soporte servidor: la creación22/23 no está integrada allí aún.

El ejecutable base compatible tiene SHA256
`bf644876709c591acc17c0da8cdf1814edcc9f1e6bc109a8c0d5c38c79dc953c`.
No aplicar offsets a otros ejecutables. El derivado combinado obligatorio es
`87ceca9ea08da2f0d9d312d833ae76751a3ab8f2b8a7d742bfd2356e55f291f3`.
La derivación solo-cache `cf11…` **no sirve** para cargar esta GlueXML modificada.

Reversión: con WoW cerrado restaurar la pareja Z previa y volver a lanzar el
ejecutable original. Retirar solo el derivado propio si se desea; S/T permanecen.
No hay un rollback SQL porque esta fase no escribe datos servidor.

## Límite nativo corregido e interfaz

El enumerador nativo recorre ChrRaces dinámicamente y excluye Flags&1; clases
proceden de CharBaseInfo. `GetAvailableRaces` devuelve triples nombre/file/enabled,
**no IDs**. `SetSelectedRace` usa ordinal del selector. Los nuevos ordinals
esperados son6 (Alto Elfo) y12 (Goblin), no22/23 como argumentos de esa API.

La restricción real encontrada es una caché de apariencia indexada por ID,
22 filas×2 sexos. Las posiciones22/23 invadían las variables de selección y
orientación vecinas. El derivado añade una sección PE real **RW no ejecutable**,
24 filas×2 punteros, redirige sus ocho referencias y ajusta init/cleanup y checksum.
No se alarga el array sobre memoria vecina ni se inventa un parche de máscara.

Se añaden dos botones XML reales, MAX_RACES12, seis posiciones por facción,
iconos y etiquetas, manteniendo diez botones de clase y filtros nativos. Las
escenas provisionales son BloodElf para Alto Elfo y Orc para Goblin; no son
zonas iniciales Turtle portadas. Las escenas de preview se observaron en la prueba
regular con Wine; la cámara/iluminación en gameplay no está validada.

La firma nativa de GlueXML cubre el contenido XML/Lua recursivo. El perfil
`--allow-custom-gluexml` acepta únicamente su **mismatch de contenido status2**
en el caller GlueXML. Mantiene firma TOC válida obligatoria, rechazo de firmas
ausentes/incorrectas y comparación del digest tras carga. No se cambia FrameXML,
autenticación, Warden, protecciones de red o licencias. Ver
[traza y alcance](../../tools/new-races-ui/GlueXML-integrity.md).

## Modelos originales convertidos

Se usan los BloodElf Turtle de patch-8 (no los archivos alternativos HighElf*)
y Goblin de patch-7. Cuatro M2 versión256 se convierten a264, con un SKIN externo
por modelo. Espacios aislados:

```text
Character\Custom\TurtleHighElf\Male|Female\...
Character\Custom\TurtleGoblin\Male|Female\...
```

No se usan Goblins NPC de1884/2123 vértices como sustituto: los modelos Turtle
tienen7419/11908. Altos Elfos tienen6435/6980. Vértices, pesos, bind bones y
clips originales se conservan, comprimiendo quaternions con error máximo1/32767.
Los timestamps se convierten a tiempo local y los fallbacks se materializan por
modelo, no alterando AnimationData global. Todas las animaciones son internas;
no se declaran `.anim` externos inexistentes.

El conversor usa M2Lib de Koward, pin
`18c085632b12e8a19da40df3459f1f4620a30972`, con patch GPL-2.0 explícito. Tres
pistas Goblin con almacenamiento legacy ambiguo se normalizan a lineal: huesos
80/126 masculinos y90 femenino. Son helpers fuera del árbol ponderado, pero sí
afectan attachments19/11: **no se llaman inútiles**. Los keyframes se conservan;
la curvatura/movimiento accesorio puede diferir. Por ello sus reports mantienen
`fullySupported=false` y requieren comprobación visual de equipo y transiciones.

## DBC, texturas y reparaciones declaradas

| Tabla | Base → total |
|---|---:|
| ChrRaces |21→23|
| CharBaseInfo |72→83|
| CharStartOutfit |200→222|
| CreatureDisplayInfo |24263→24267|
| CreatureModelData |1331→1335|
| CharSections principal/opcional |9302/9452→10490/10640|
| CharacterFacialHairStyles |233→270|
| CharHairGeosets |339→406|

Los nuevos grupos CharSections están ordenados por Race/Sex/Base/Variation/Color,
sin cambiar los IDs22000+ asignados ni el prefijo de registros/cadenas anterior.
Los flags de modelo donantes se conservan (2052 Altos Elfos,4 Goblins); no se
borran bits desconocidos bajo la suposición de que eran solo NPC. Los bounds
provienen del modelo convertido y la escala es1.

Se importan las opciones ordinarias de fuente, no todos los cuerpos NPC/tienda
flag1 que colisionan con sus colores. Se mantienen11 skins/10 caras por sexo
Alto Elfo,3 skins Goblin con4/6 caras. Pelo:16/20 estilos Alto Elfo×16 colores y
14/17 Goblin×5. Todas las320 filas femeninas Alto Elfo están presentes.

La fuente declara47 nombres inexistentes: overlays faciales legacy, scalps y
cinco torsos masculinos. Se probaron directamente todos los22 MPQ Turtle; la
declaración de scalps/overlays también coincide con nombres ausentes en los38
MPQ nativos. Para pelo femenino, las20 claves fuente/nativas de geoset coinciden
y **ShowScalp=0**: se limpian solo slots de overlay inactivos, conservando la
textura principal de pelo Turtle. No se sustituyen sus colores por arte nativo;
la comparación RGBA muestra que no son idénticos. Los torsos masculinos legacy
se normalizan a vacío, manteniendo cuerpo/pelvis. Estas reparaciones no acreditan
todos los detalles de su compositor en ejecución; están documentadas en report.

Los22 outfits son clones de clase/sexo nativos con ítems/displays válidos. No
representan exactamente cada conjunto de inicio Turtle: algunos IDs fuente no
existen o tienen otra apariencia en335. El inventario real requiere trabajo
servidor posterior. No se importa Item/Spell/Faction Turtle wholesale.

## Corrección de arrastre de texturas entre razas/sexos

El defecto inicial mostraba un rostro Orc sobre Alto Elfo masculino y aspecto
Scourge en Goblin femenino. La corrección de ambos modelos fue aceptada por el
usuario y después observada en el preview regular enUS/esES con Wine; un aviso
posterior sobre Goblin femenino fue aclarado como error de prueba.

El defecto concreto estaba en **44 BLP2 DXT1** usados por el compositor CPU:
23 de Alto Elfo masculino (21 caras,2 overlays de ropa) y21 de Goblin femenino
(3 cuerpos,18 caras). Los componentes equivalentes de los otros dos modelos
ya eran paletizados. No se encontraron diferencias de materiales, referencias
o flags que explicaran ese patrón.

En el EXE entregado, `0x004F2D40` devuelve paleta solo si encoding==1. El
compositor `0x004EC690` sale sin escribir si recibe NULL; otra ruta llama a
`0x004E82D0`, que rellena verde0xFF00FF00. Se ejecutaron esos bloques x86 en
Unicorn con los BLP publicados: los44 originales toman el camino NULL/stale;
los44 convertidos llegan a la entrada de procesamiento de píxeles. Esto sustenta
el mecanismo de reutilización del buffer anterior, pero no es una captura del
buffer del cliente del usuario ni una prueba completa de renderizado Windows.

La corrección de texturas del candidato cambió **solo esos44 miembros BLP**, en las cuatro copias
Z. Todas las DBC, M2, SKIN, Glue, clases, IDs y otros miembros son byte-idénticos.
Las599 texturas de roles CPU (cuerpo, cara, facial, scalp, ropa interior) pasan
la validación palette1; no se convierten indiscriminadamente pelo/ojos cargados
directamente por GPU, donde DXT sí es válido.

Se preservan cantidad/dimensiones de mips y alpha decodificado de todos ellos.
La reducción RGB a256 colores es **con pérdida**: MAE superior por archivo
0.064–2.299, P99 2–23 y error máximo aislado6–121 por canal0–255. Se registran
métricas, hashes fuente/finales y roles, sin afirmar identidad de píxeles.

**PASS de la corrección histórica:**13 tests unitarios, checks de imagen/modelos, dos builds idénticos,
comparación de todos los miembros de las cuatro copias y prueba nativa emulada
de las44 rutas. **Aceptación visual:** confirmación del usuario de22 masculino y23
femenino, más el muestreo regular enUS/esES con Wine descrito arriba.
EXE/S/T, servidor/BD y clientes originales no se modifican para este arreglo.

Prueba de regresión: Orc/Tauren/otras →Alto Elfo hombre; No-muerta/otras→Goblin
mujer, todos los colores/caras, especialmente Alto Elfo color04/Face05; cambiar
sexo, aleatorio, clase/ropa, salir/reentrar creación y volver a las razas previas.

### Propiedad de las tablas localizadas en la entrega consolidada

El Z raíz consolidado no contiene `ChrRaces`, `AreaTable`, `Map` ni
`MapDifficulty`: esas DBC pertenecen a los Z de cada locale. Retirar únicamente
esas cuatro tablas del root recuperó los diez encabezados españoles originales;
los27 miembros ordinarios restantes del root quedaron byte-idénticos y los otros
cinco archivos instalados no cambiaron. El preview regular enUS/esES confirmó
los encabezados originales y nuevos y conservó los modelos/cycling muestreados.
Esto valida esta cadena concreta; no establece prioridad universal para cualquier
cliente/mod ni acredita nombres de mapas en gameplay. No reintroducir las copias
localizadas antiguas del candidato en el root consolidado.

## Reproducibilidad y validación

La construcción de texturas usa un entorno aislado con las dependencias de
`tools/troll-customizations-requirements.txt` (Pillow13.0.0/NumPy2.2.6). Invocar el
builder con el Python de ese entorno; no sustituir el Python del sistema.

Para repetir la comparación del cambio limitado a texturas después de
publicar, conservar la entrega previa exacta y pasar
`--previous-publication /ruta/entrega-anterior` al modo `--integration` de
`tools/test_new_races_assets.py`. `--verify-existing` verifica dos builds ya
generados. El harness comprueba los cuatro hashes anteriores antes de construir
o escribir; no compara accidentalmente la entrega nueva consigo misma ni omite
la comparación cuando falta la anterior.

```sh
DOTNET=/ruta/dotnet8 scripts/build-new-races-model-converter.sh
DOTNET=/ruta/dotnet8 scripts/build-new-races-model-converter.sh --validate
DOTNET=/ruta/dotnet8 python3 tools/build_new_races_assets.py --output work/razas-nuevo
python3 tools/patch_new_races_client.py --allow-custom-gluexml \
  --output work/razas-exe-nuevo/Wow-new-races.exe
```

El builder consume fuentes fijadas por hash y herramientas versionadas, no los
informes de investigación de work/. El código/patch/licencia del conversor está
en [M2Lib integration](../../patches/third-party/m2lib/README.md). Los informes y
checksums publicados incluyen la evidencia de dos builds fuente idénticos.

- **PASS:**11 tests de ejecutable/interfaz, Lua5.1 con APIs nativas simuladas y
  ejecución Unicorn de los bloques x86 de decisión/digest;10 tests de assets.
- **PASS:** dos builds de los cuatro MPQ idénticos, modelos/animación/skins
  verificados independientemente,83 clases, cierre de texturas activas y ocho
  tablas con prefijos antiguos intactos. Preservados38 miembros root y25 locale
  ajenos de r5. Executable derivado regenerable con el SHA declarado.
- **PASS:** revisión independiente del conjunto publicado. Los MPQ originales,
  paquetes S, cliente de referencia, core/servidor/BD no se modificaron.
- **PASS observado:** preview de la entrega consolidada regular enUS/esES bajo
  Linux/Wine Direct3D9, con encabezados y18 posiciones de cycling Goblin femenino;
  no equivale a ejecutar todas las ediciones históricas.
- **NOT RUN:** Windows nativo, ejecución HD, creación/guardado/login/juego de22/23,
  tooltip Fireball y cobertura exhaustiva de animaciones, equipo, pelo y transiciones.

Checklist cliente: abrir con el derivado, confirmar12 razas y equipos, recorrer
las10 existentes sin regresión, ambas nuevas×ambos sexos×cada clase; cambiar
vieja→22→23→vieja repetidamente, random/cycling/rotación, salir/reentrar creación.
Comprobar el Goblin NPC y Elfo de Sangre existentes intactos. Registrar este
resultado de preview por separado de la futura creación/login/juego servidor.
