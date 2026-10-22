# Exportación autónoma del piloto — formato alternativo

La ruta normal del proyecto es [aplicar los scripts existentes](deployment.md):
SQL/parches mediante sus manifiestos y cliente manual desde el repositorio.
Este documento conserva el formato autónomo de exportación y sus pruebas; no
es otro paso obligatorio ni debe encadenarse con el instalador SQL normal.
Su instalación inicial exige las diez filas SQL ausentes y mantiene su propio
estado, distinto del estado del instalador de archivos del proyecto.

## Qué garantiza y qué no

`tools/crypt_release.py` construye una **release portable del piloto Karazhan
Crypt**, verificable por SHA256. Se instala encima de AzerothCore/WotLK335
compatibles ya preparados, sin repetir conversiones, extracción ni navegación.
No necesita el checkout del proyecto, StormLib, los clientes fuente ni los
extractores modificados en la máquina de destino.

Esto **no es** un instalador de AzerothCore desde un sistema operativo vacío,
una restauración de todo el servidor privado, ni una reconstrucción completa
desde los clientes originales. Módulos, cuentas, personajes, configuración,
otras clases/quests/objetos y otras personalizaciones no forman parte de esta
unidad. Reconstruir el arte desde cero sigue necesitando el PNG manual y las
entradas de la [cadena de conversión](migration-guide.md#10-cadena-incremental-del-piloto-qué-reproduce-hoy).

Hay dos distribuciones de cliente diferentes:

- **r5 coordinada**, aceptada en juego: T + root Z + esES Z, para el snapshot
  custom exacto que se auditó. Sigue siendo la entrega para ese cliente.
- **Release limpia**, derivada de los recursos del piloto pero con DBC/TRS de
  una base stock declarada: un T nuevo, sin los Z. Tiene comprobación binaria
  y de instalación, **no una nueva aceptación visual en juego**.

No intercambiarlas. Los Z contienen otras personalizaciones. Incluso el T r5
incluye un WorldMapArea de referencia con 104 adiciones ajenas y una
modificación de Ruby Sanctum. La release limpia extrae únicamente las filas
propias; no copia esa tabla completa ni instala esas otras personalizaciones.

## Contenido de la unidad

- Seis `.map`, árbol VMap y seis tiles, parámetros MMap y los seis tiles finales,
  incluido el tile de navegación reparado.
- Cierre exacto de **405 modelos de colisión**, no todo el directorio de DEV.
  164 nombres físicos terminan en `.m2`: son binarios de colisión servidor, no
  modelos cliente. Los otros 241 terminan en `.vmo`.
- Deltas de cinco DBC servidor: Map800, Area5086, MapDifficulty756,
  WorldMapArea674 y AreaTrigger900800/900801. Se conservan las filas y las
  cadenas ajenas de la base de destino; AreaTrigger mantiene orden por MapID.
- **Diez filas SQL**: una instancia, dos triggers, dos teleports, dos plantillas
  GO, dos spawns y una regla de acceso. La unidad de acceso sola tiene nueve.
- Cliente: 64 recursos de arte/geografía intactos, seis DBC fusionadas contra
  la base declarada y 29 adiciones TRS, en un único `Data/patch-T.MPQ`.
- Código autónomo, SQL canónico fijado por hash, informe de cliente y manifiesto
  de los 439 archivos de la release. No hay credenciales dentro.

La diferencia servidor/cliente en Map800 campo57 es intencional: servidor0,
cliente511. LoadingScreens511 es de cliente; no se reemplaza LoadingScreens
del servidor. No hace falta un parche de gameplay del core para esta unidad.
Los parches de extractores solo son necesarios para regenerar datos.

## Construir la release — máquina de preparación

Python3.11+, CLI MPQ/StormLib y los artefactos propietarios son necesarios aquí,
no en destino. Todas las salidas deben ser nuevas.

```sh
# Leer únicamente los archivos stock declarados; no editar el snapshot.
python3 tools/crypt_release_client.py extract-baseline \
  --archive-root /ruta/snapshot-335 \
  --archives tools/crypt-release-stock-eses.json \
  --output work/base-stock-nueva

python3 tools/crypt_release_client.py build \
  --pilot work/client-overlay-r5/Data/patch-T.MPQ \
  --baseline work/base-stock-nueva \
  --output work/cliente-limpio-nuevo

python3 tools/crypt_release.py build \
  --server-data /ruta/datadir-del-piloto-validado \
  --client-release work/cliente-limpio-nuevo \
  --output work/release-nueva

python3 tools/crypt_release.py archive \
  --bundle work/release-nueva --output work/release-nueva.tar
```

El JSON stock es un orden **explícito, de menor a mayor prioridad**, de archivos
relativos a `Data`; no es un resolvedor automático de cualquier cliente custom.
El extractor puede leer ese subconjunto de un snapshot que contenga otros
parches, pero no lee sus Z/N ni certifica que el snapshot entero sea limpio.
Para otra distribución/locale, declarar y auditar su lista completa, incluidos
los archivos stock adicionales que tenga. El instalador exigirá exactamente
esos nombres y hashes. La autenticidad stock de las fuentes la establece el
operador, no el nombre del MPQ ni esta herramienta.

La construcción fija el hash del T r5 aceptado, el cierre de colisiones y el
SQL. Un cambio legítimo requiere revisar código/contrato y emitir otra release;
no sustituir hashes a ciegas. Construir dos veces con las mismas entradas y
código debe producir idénticos manifiestos y archivos `.tar`. El tar fija orden,
permisos, propietarios y fechas; los paths absolutos de preparación no aparecen
en el manifiesto de la release.

Guardar el `.tar` y su SHA256 en almacenamiento privado recuperable. `work/`
está excluido de Git y no recupera por sí mismo ese export. Los assets finales
se conservan también en el repositorio según la ruta normal del proyecto;
no confundir eso con recuperar clientes fuente o intermedios. El manifiesto
comprueba integridad, no aporta una firma de autenticidad. Esta herramienta no
ha realizado una copia externa de seguridad por sí sola.

## Instalar en destino

Requisitos:

- Linux/POSIX, Python3.11+ y cliente CLI `mysql` compatible con MySQL8.
- AzerothCore con esquema world compatible y datos nativos335 ya instalados.
  Cabeceras admitidas: MAPS9/build12340, VMAP_4.8, MMap20/Detour7.
  Se verifican muestras nativas de mapa0; eso no certifica cualquier revisión
  arbitraria del core. Las tablas propias deben ser InnoDB, sin triggers SQL.
- IDs, bindings y archivos del piloto libres. En la primera instalación se
  rechaza cualquier fila SQL propia existente, aunque parezca idéntica. Una
  instalación manual anterior no se adopta sin auditoría.
- DBC de servidor sin subdirectorios locale: los overrides locales necesitan
  otra migración explícita para no ocultar los deltas.
- Servidor y, si se instala cliente, WoW **detenidos**. Acceso exclusivo a sus
  archivos y BD durante instalación/reversión. `--offline` es una declaración
  del operador, no un detector ni una orden para parar servicios.

Comprobar el hash del tar recibido y extraerlo en una carpeta nueva. Después:

```sh
python3 /ruta/release/crypt_release.py verify --bundle /ruta/release

python3 /ruta/release/crypt_release.py install \
  --bundle /ruta/release \
  --data-dir /ruta/azerothcore/DataDir \
  --database acore_world \
  --login-path login-del-destino \
  --state /ruta/estado/crypt-release \
  --offline
```

`--data-dir` es el directorio efectivo que contiene `dbc`, `maps`, `vmaps` y
`mmaps`, no necesariamente el directorio del ejecutable. Configurar el login
MySQL del destino fuera del paquete. Alternativamente, usar
`--defaults-file /ruta/privada/mysql.cnf --login-path ''`. No hay `USE acore_world`
oculto: las sentencias derivadas del SQL canónico usan la BD elegida.

Si el cliente limpio está en esta máquina o accesible como directorio local,
añadir `--client /ruta/cliente-limpio`. Se verifican todos los archivos stock y
se rechazan MPQ adicionales, loose overrides y hashes distintos. El cliente
custom de juego actual **no es elegible** para esa opción; no quitarle los Z
para forzar el preflight. Instalar solo el servidor es válido y no toca clientes.
Para actualizar otro cliente, preparar su distribución aparte y comprobar el
contrato, en lugar de instalar a ciegas el T limpio sobre sus personalizaciones.

El preflight completo precede a los cambios en archivos/BD. Los modelos
compartidos existentes solo se reutilizan si coinciden byte a byte; un conflicto
no se sobrescribe. Los DBC se fusionan contra el destino, no se sustituyen por
las tablas completas de DEV. La transacción SQL propia contiene las diez filas
y no necesita crear procedimientos auxiliares ni privilegio `CREATE ROUTINE`.

Repetir **el mismo comando y `--state`** verifica la identidad del servidor
MySQL, bundle, BD, paths, archivos y filas y devuelve `already-installed` sin
reescribirlos. Conservar el bundle y el estado fuera del DataDir y del cliente.
Arrancar después y comprobar logs, acceso y funcionamiento en juego: la
instalación de archivos no sustituye esas pruebas.

## Reversión y fallos

Usar los mismos argumentos, cambiando `install` por `rollback`. Si se usó
`--client`, debe volver a indicarse. Se restauran los bytes/permisos guardados,
se eliminan solo los archivos que antes no existían y las diez filas añadidas,
y se conservan los datos ajenos. No se resetean contadores AUTO_INCREMENT.

Ante una interrupción, usar `recover` con esos argumentos: **revierte**, no
continúa la instalación. Distingue la transacción no confirmada, la confirmada
y los archivos instalados parcialmente. El diario se sincroniza antes del
COMMIT; los originales y la ausencia previa quedan registrados. Si otro
operador ha modificado archivos/filas propios, falla y requiere reconciliación;
no aplica un rollback destructivo por prefijos.

Una interrupción muy temprana, antes del primer diario, deja solo preparación
de backups, sin tocar archivos destino ni SQL. La herramienta lo diagnostica:
si se confirma que no se borró un diario instalado, retirar únicamente ese
estado incompleto o elegir otro `--state`. No borrar un diario instalado para
intentar tratarlo como preparación. Un estado revertido se conserva; una nueva
instalación usa otro directorio de estado.

## Validación y sus límites

Pruebas sintéticas y fixtures propietarios opt-in:

```sh
CRYPT_RELEASE_INTEGRATION="$PWD/work" \
  python3 -m unittest discover -s tools -p 'test_crypt_release*.py' -v

python3 tools/test_crypt_release_integration.py \
  --bundle work/release-nueva --baseline work/base-stock-nueva \
  --archive-root /ruta/snapshot-335 --output work/prueba-instalar-nueva
```

La segunda prueba arranca un MySQL privado, sin red, y lo cierra al terminar;
no necesita sudo. Copia de DEV **solo definiciones de tablas y una fila ajena
por tabla propia**, mediante lecturas, y usa DBC stock, muestras binarias
nativas y hardlinks de solo lectura a MPQ stock. No altera los originales.
Prueba instalación, reaplicación, rollback y recuperación ante fallos antes y
después del COMMIT y durante escritura de archivos, incluida la CLI autónoma.

Esto demuestra el instalador sobre una base aislada sin piloto; **no equivale
a arrancar un reino completo pristine** ni a lanzar el nuevo cliente. Esas
comprobaciones y la reconstrucción desde fuentes se reportan separadamente.
Los resultados concretos y hashes de entrega pertenecen a
[validation.md](validation.md), no a una promesa de compatibilidad universal.
