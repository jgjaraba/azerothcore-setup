# Tauren — personalización nativa y ediciones acumulativas

## Entrega vigente

Se parte de las ediciones Troll terminadas, con sus recursos y registros
conservados. No vuelven los colores masculinos Troll33–35 retirados. Las nuevas
rutas canónicas para esta y futuras razas son:

- **Principal:** `client_patches/Data/patch-S.MPQ`.
- **Opcional completa:** `client_patches/optional-extra-skins/Data/patch-S.MPQ`.

Copiar solo una como `Data/patch-S.MPQ`, con WoW cerrado y backup fuera de Data.
No instalar ambas, renombrar una como otro parche o copiar carpetas históricas.
Mantener T/Z/locale-Z. Los paquetes de `turtle_forest_troll/` son bases congeladas
de reconstrucción, no capas adicionales de la entrega actual. La política
permanente está en [ADR-0007](../project/decisions/ADR-0007-native-customization-editions.md).

## Qué se clasifica como completo

Para tauren, el banco ordinario es **cinco rostros masculinos y cuatro femeninos**.
La principal contiene una nueva piel por sexo con todos esos pares de texturas
distintos y expresamente referenciados por Turtle. No se clona una cara fija
para aparentar cobertura. Las caras exclusivas DK se preservan, no se inventan
versiones inexistentes; el acoplamiento Face/Skin del cliente sigue vigente.
La clasificación acredita cierre de datos, **no aceptación gráfica ya realizada**.

| Edición | Color tauren | Fuente | Caras |
|---|---|---|---|
| Principal hombre |25|cuerpo Turtle20 con marcas, Extra18 y banco facial18|0–4, cinco pares diferentes |
| Principal mujer |17|cuerpo Turtle11 con marcas, Extra10 y banco facial10|0–3, cuatro pares diferentes |
| Opcional hombre |26|alternativa azul Skin19|solo0 |
| Opcional hombre |27|Skin21GrimTotem|solo0 |
| Opcional hombre |28|spiritwalkertaurenshop identificado|solo0 |
| Opcional mujer |18|alternativa azul Skin19|solo0 |
| Opcional mujer |19|Skin20GrimTotem|solo0 |

Los cuerpos ordinarios pintados proceden de filas Turtle3856 y4107, con familias
Base0/1/4 completas. Sus nombres también existen entre recursos DK de Wrath,
pero no se sobreescriben esos índices:25/17 son nuevos. Las alternativas no
tienen un banco fuente completo; se deriva una cara del mismo atlas y se
expone **solo Face0**, sin aliases que simulen caras diferentes. Al cambiar Face,
el cliente puede cambiar de piel buscando otra combinación válida. Para elegir
las parciales, seleccionar primero Face0.

El bake de tienda masculino carece de una familia Extra independiente: usa un
alias explícito de Extra azul19. No se afirma fidelidad comercial completa ni
se importan objetos/precios/auras de tienda. Se conserva como opción parcial.

## Pelo, colores y adornos

- Todos los estilos de cuernos/pelo Turtle0–12 hombre y0–11 mujer ya tienen
  correspondencia nativa en CharHairGeosets. Se habilitan **cinco estilos por
  sexo**,30 filas con PLAYER añadido0x12→0x13, conservando barbería.
- Se añaden **seis colores de cuernos**: fuente3–8 → destino4–9, en todos los
  estilos. Se preservan0–2 y el índice NPC3 oculto, sin reutilizarlo.
- El modelo tauren usa texturas tipo1/8/2, no el tipo6 de pelo. Para esos colores
  se aporta la capa ScalpLower real. Los placeholders Texture1/3 que faltan ya
  en los datos legacy no se copian como referencias falsas en las filas nuevas.
- Nuevos adornos faciales: **dos por sexo**, claves masculinas7/8 y femeninas5/6.
  No se asignan nombres de formas no comprobados visualmente.

### Geometría adicional, no sustitución completa del modelo

Las cuatro opciones usan piezas ausentes en Wrath: geosets110/111 masculinos y
206/207 femeninos. Se agregan a los M2 nativos versión264 y sus tres perfiles
SKIN; no se copia el modelo Vanilla256 entero. Son126 vértices nuevos masculinos
y179 femeninos; femenino206 contiene dos secciones.

Se verifican los huesos usados y todos sus padres: ID, flags, parentesco y pivot
de reposo coinciden con el modelo nativo. Los pesos y vértices fuente se conservan,
con remapeo explícito de paletas de huesos en cada LOD. Esqueleto, animaciones,
attachments, ojos DK, vértices y materiales anteriores permanecen intactos; solo
cambian los headers de los arrays ampliados y se añaden datos al final. Las
piezas quedan dentro de los bounds nativos y no cambian combate/alcance/cápsula.

Esto requiere validación visual de animación, cascos y equipo. No es compatible
por afirmación con modelos HD o con otro mod que reemplace los M2 tauren.

## Recursos y componentes

Namespace nuevo: `Character\Custom\TurtleTauren\...`. Las texturas de familias
completas se conservan de fuente. Las caras generadas opcionales usan BLP2
paletizado con plano alpha correcto, evitando la representación BGRA que falló
en las caras Troll. Los cuerpos originales no se repintan.

La ropa interior de variantes parciales se compone sobre el propio atlas con
una prenda nativa recuperada de seis pares cuerpo/ropa. Es aproximada: MAE RGB
2.454 pelvis masculina,3.269 pelvis femenina,5.192 torso femenino; P99 15/21/34.
No es reconstrucción artística exacta ni se eliminan prendas ya pintadas en los
bakes. La principal utiliza los componentes fuente completos, no este ajuste.

## Identificadores y servidor

| Unidad | Datos |
|---|---|
| Nuevas filas principales |163 IDs21000–21162:13 de piel completa y150 de colores de cuernos |
| Overlays nativos |30 IDs existentes, solo PLAYER añadido a flags |
| Principal SQL |193 filas en `turtle_tauren_customizations.sql` |
| Opcional SQL |15 IDs21200–21214, fuera del manifiesto normal |
| Estilos faciales |cuatro nuevas claves Race6/Sex/Variation, sin ID |

El donor servidor contiene ahora once filas: siete Troll +cuatro Tauren. El
helper admite la familia antigua7 o completa11, rechaza mezclas incompletas y
fusiona claves naturales sin reemplazar la tabla. En una base estándar resultan
233 estilos. El orden físico puede depender del estado previo; comprobar por
clave/campos, no exigir hashes binarios idénticos en todo destino.

Perfil principal: Troll298 +Tauren193 =**491 overlays**. Perfil opcional completo:
lo anterior +Troll135 +Tauren15 =**641**. CharSections efectiva tiene9302 filas en
principal y9452 en opcional; los147 overlays nativos sustituyen IDs, no añaden
filas lógicas. La DBC binaria servidor CharSections no se reemplaza.

Los SQL están en los manifiestos existentes, tauren después de Troll:

```sh
scripts/apply-db-world.sh --validate --with-server-data
# Servidor detenido, DataDir real y estado nuevo para este manifiesto:
scripts/apply-db-world.sh --with-server-data --data-dir /ruta/DataDir \
  --state-dir /ruta/fuera-de-DataDir/estado-nuevo --offline

# Opt-in completo, solo después de la principal y con servidor detenido:
SQL_DIR="$PWD/data/sql/optional/db_world" scripts/apply-db-world.sh
```

Reiniciar para recargar stores. SQL y archivos no son una transacción única;
mantener backup/estado y no usar --force. No modificar apariencias guardadas al
cambiar de perfil: todos los clientes que vean personajes opcionales necesitan
sus recursos. El core inspeccionado no valida completamente esas tuplas; retirar
SQL no remapea personajes ni constituye un control de desbloqueos.

## Reproducción y conservación

`tools/tauren-customizations.json` fija archivos fuente y sus hashes, decisiones,
colores e IDs. El builder normal no depende de informes de auditoría de work/:

```sh
python3 tools/build_tauren_customizations.py --output work/tauren-build-nuevo
TAUREN_INTEGRATION=1 python3 -m unittest discover -s tools \
  -p 'test_tauren_customizations.py' -v
```

Usar el entorno de `tools/troll-customizations-requirements.txt`. `--publish`
verifica destinos, SQL, donor y manifiesto antes de preparar/reemplazar archivos;
no instala en clientes ni toca BD. Conserva los paquetes Troll base byte-idénticos.
La auditoría inicial puede reproducirse con `audit_tauren_customizations.py` y
salida nueva. [Troll](troll-customizations.md) conserva su contrato específico;
sus rutas anteriores son ahora fuente congelada, no entrega acumulativa actual.

SHA256:

| Edición | MPQ |
|---|---|
| Principal |`54b56931376604df4122c5551f3bfccd937a32b32974e35906ba73139bd885d3`|
| Opcional |`5e0a1954da86d71d9fa9bf1ce408b535d03f86941956be754a9f976cfd7accf2`|

## Rollback acotado

Retirar primero tauren opcional con `data/sql/rollback/turtle_tauren_extra_skins.sql`
(solo15) y recustomizar colores parciales26–28 hombre/18–19 mujer antes de usar
un cliente sin ellos. Para volver totalmente a Troll, retirar después tauren
principal con `data/sql/rollback/turtle_tauren_customizations.sql` (solo193) y
restaurar los siete estilos de donor Troll/tabla previa229, sin tocar los Troll.
Antes de ese downgrade también recustomizar tauren25 hombre/17 mujer, colores
de cuernos4–9 y adornos faciales7–8 hombre/5–6 mujer que el cliente viejo no admite.

El rollback del helper es **de todos los archivos que posee su estado**, no un
desinstalador selectivo. Solo usarlo para downgrade tauren si el estado incremental
se tomó sobre Troll ya instalado y el resto de archivos no cambió. No usar un
estado de instalación limpia para retirar solo una raza: puede poseer la cripta.
Conservar fuente/manifiesto/estado y usar otro estado después de revertir.

## Validación y límites

- **PASS — aceptación práctica del usuario:** «funciona perfectamente». Se
  registra como confirmación del usuario, no como cliente ejecutado por el agente
  ni prueba individual de cada sexo, estilo, equipo o clase.
- **Limitación confirmada por el usuario:** un personaje con piel opcional se
  representa con errores al cambiar al principal. La edición principal actual
  no aporta sus tuplas/recursos; esta aceptación no resuelve clientes mezclados.
- **PASS:**15 tests, dos builds fuente idénticos y176 ejecuciones SQL en MySQL
  privado sin red, con dos modos de escape; conflictos/prerrequisitos/rollback y
  preservación. Verificadores independientes cubren M2/SKIN, huesos, geometría,
  alpha, componentes, bancos de caras y todo el contenido Troll anterior.
- **PASS:**27 pruebas del helper, incluido donor combinado y preservación de
  claves/bytes. Publicación y manifiestos validados; solo cambia su entrada donor.
- **PASS:** en DEV principal491, opt-in641, retirada hasta Troll298 y nueva
  principal491, con reaplicación/rollback. Apariencias guardadas de Troll y Tauren
  comparadas antes/después y conservadas. No se escriben sus bytes de personaje.
- **PASS:**491 overlays finales comparados campo a campo,233 estilos servidor
  coincidentes con el cliente y binario CharSections original intacto. Logs
  observados hasta worldserver ready y authserver activo tras el reinicio.
- **NOT RUN por el agente / sin confirmación específica:** matriz exhaustiva de
  renderizado/selección, animaciones, cascos/equipo, combinaciones/DK, creación/
  relog y HD. La aceptación general del usuario no acredita cada caso. Los
  snapshots originales no se modificaron.

### Representación entre ediciones: investigación, sin cambio aplicado

El ejecutable de referencia separa elegibilidad de creación de representación.
Lookup CharSections `0x004F3BA0` no filtra flags; el predicado de selección
`0x004F39A0` exige PLAYER. El camino de actualización de jugadores `0x006DA870`
lee el byte Skin y llama al setter `0x004EA6B0` sin ese predicado; la recarga local
también lo usa. Esto favorece aportar tuplas de render ocultas en principal,
con PLAYER borrado (`0x11→0x10`), conservando sus índices.

No usar NPC0x08 para ocultarlas: los setters `0x004EA735`/`0x004EA4C4` prueban
ese bit y alteran carga de ropa/cara. Los flags no son irrelevantes globalmente.
La evidencia es estática en el binario de referencia, **no una prueba en juego
de filas ocultas**, que sigue pendiente.

Hay dos contratos posibles: principal con fallbacks nativos ocultos (muestra
un sustituto válido, sin recursos opcionales) o principal con los recursos reales
ocultos a creación (muestra la apariencia exacta, pero cambia la separación de
assets de ADR-0007). Ninguno se ha implementado ni se modifica la política sin
decidir qué representación debe ver el usuario del principal. El servidor no
envía texturas ni negocia esta capacidad nativamente por observador.

Checklist: ambos sexos, principal con sus cinco/cuatro caras realmente distintas,
trece/doce estilos y nueve colores elegibles de cuernos (0–2,4–9), adornos nuevos,
movimiento y cascos; opcional con Face0 y cambio de piel al recorrer caras; crear,
relog y comprobación desde otro cliente con la edición adecuada.

Formatos de referencia: [M2/SKIN](https://wowdev.wiki/M2/.skin) y
[BLP](https://wowdev.wiki/BLP). La compatibilidad visual no se infiere solo de
que un parser propio pueda leer esos formatos.
