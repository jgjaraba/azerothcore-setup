# Validación de los vendedores de mazmorras

1. Importa `dungeon_gear_vendor_npc.sql` y `dungeon_gear_item.sql` y reinicia **worldserver**. El modelo 90100 debe estar instalado en servidor y cliente; las compras requieren también las monedas y los registros `ItemExtendedCost` del catálogo.
2. Entra con una cuenta GM. Ejecuta `.gm on` para revisar las posiciones sin que los enemigos interfieran.
3. Usa los comandos siguientes en el **chat del juego**, uno cada vez. `.go creature` recibe el **GUID de aparición**, no el ID de plantilla.
4. Comprueba que cada NPC pisa el suelo, se ve completo, queda accesible, permite hablar/comerciar y no tapa una puerta ni activa el portal al acercarte. Prueba también el acceso normal con `.gm off` cuando hayas comprobado que la zona es segura.

Las posiciones se han contrastado con coordenadas y volúmenes de acceso del servidor, pero no se han probado visualmente dentro del juego. No se dispone de los mapas de colisión VMAP para certificar suelo, muros o visibilidad. Si hay que ajustar un punto, envíame el ID del NPC y la salida de `.gps` desde la posición deseada.

| Mazmorra / ala | NPC | Ir al vendedor |
|---|---:|---|
| Sima Ígnea | 90300 | `.go creature 900010` |
| Cuevas de los Lamentos | 90301 | `.go creature 900011` |
| Minas de la Muerte | 90302 | `.go creature 900012` |
| Castillo de Colmillo Oscuro | 90303 | `.go creature 900013` |
| Cavernas de Brazanegra | 90304 | `.go creature 900014` |
| Mazmorras de Ventormenta | 90305 | `.go creature 900015` |
| Gnomeregan | 90306 | `.go creature 900016` |
| Horado Rajacieno | 90307 | `.go creature 900017` |
| Cementerio Escarlata | 90308 | `.go creature 900018` |
| Biblioteca Escarlata | 90309 | `.go creature 900019` |
| Armería Escarlata | 90310 | `.go creature 900020` |
| Catedral Escarlata | 90311 | `.go creature 900021` |
| Zahúrda Rajacieno | 90312 | `.go creature 900022` |
| Uldaman | 90313 | `.go creature 900023` |
| Zul'Farrak | 90314 | `.go creature 900024` |
| Maraudon | 90315 | `.go creature 900025` |
| Templo Sumergido | 90316 | `.go creature 900026` |
| Profundidades de Roca Negra | 90317 | `.go creature 900027` |
| Cumbre de Roca Negra inferior | 90318 | `.go creature 900028` |
| Cumbre de Roca Negra superior | 90319 | `.go creature 900029` |
| La Masacre Este | 90320 | `.go creature 900030` |
| La Masacre Oeste | 90321 | `.go creature 900031` |
| La Masacre Norte | 90322 | `.go creature 900032` |
| Scholomance | 90323 | `.go creature 900033` |
| Stratholme: sector vivo | 90324 | `.go creature 900034` |
| Stratholme: sector no muerto | 90325 | `.go creature 900035` |

Los dos vendedores de Cumbre de Roca Negra están junto al acceso exterior compartido. Maraudon utiliza la entrada naranja. Uldaman y Gnomeregan utilizan la entrada principal. La Masacre Este utiliza su acceso occidental desde el patio. Los dos vendedores de Stratholme están en entradas distintas.

## Coordenadas directas

Si todavía no se han cargado los spawns, estos comandos permiten inspeccionar las ubicaciones propuestas. Sintaxis: `.go xyz X Y Z mapa orientación`.

| Mazmorra / ala | Comando |
|---|---|
| Sima Ígnea | `.go xyz 1811.78 -4410.5 -18.4704 1 1.78` |
| Cuevas de los Lamentos | `.go xyz -731.607 -2218.39 17.0281 1 5.68` |
| Minas de la Muerte | `.go xyz -11208.7 1673.52 24.6361 0 4.55217` |
| Castillo de Colmillo Oscuro | `.go xyz -235.0 1564.5 76.8909 0 4.398` |
| Cavernas de Brazanegra | `.go xyz 4249.99 740.102 -25.671 1 4.5828` |
| Mazmorras de Ventormenta | `.go xyz -8779.9 834.349 94.6801 0 3.77934` |
| Gnomeregan | `.go xyz -5163.54 925.423 257.181 0 4.71239` |
| Horado Rajacieno | `.go xyz -4470.28 -1677.77 81.3925 1 4.28827` |
| Cementerio Escarlata | `.go xyz 2911.0 -800.0 160.333 0 3.50405` |
| Biblioteca Escarlata | `.go xyz 2873.0 -822.0 160.333 0 0.387856` |
| Armería Escarlata | `.go xyz 2882.0 -819.0 160.333 0 1.95268` |
| Catedral Escarlata | `.go xyz 2906.0 -817.0 160.333 0 3.50405` |
| Zahúrda Rajacieno | `.go xyz -4657.3 -2519.35 81.0529 1 1.25978` |
| Uldaman | `.go xyz -6071.37 -2955.16 209.782 0 3.20443` |
| Zul'Farrak | `.go xyz -6801.19 -2893.02 9.00388 1 3.30496` |
| Maraudon | `.go xyz -1464.14 2615.21 76.7172 1 0.0` |
| Templo Sumergido | `.go xyz -10177.9 -3994.9 -111.239 0 2.95938` |
| Profundidades de Roca Negra | `.go xyz -7179.34 -921.212 165.821 0 1.84097` |
| Cumbre de Roca Negra inferior | `.go xyz -7531.0 -1213.0 285.44 0 3.8` |
| Cumbre de Roca Negra superior | `.go xyz -7536.0 -1217.0 285.44 0 3.8` |
| La Masacre Este | `.go xyz -3741.48 934.975 160.973 1 3.13864` |
| La Masacre Oeste | `.go xyz -3828.01 1250.22 160.226 1 0.0` |
| La Masacre Norte | `.go xyz -3521.29 1085.2 161.097 1 1.5009` |
| Scholomance | `.go xyz 1269.64 -2556.21 93.6088 0 3.6631` |
| Stratholme: sector vivo | `.go xyz 3352.92 -3379.03 144.782 0 3.11819` |
| Stratholme: sector no muerto | `.go xyz 3235.46 -4047.6 108.45 0 1.93522` |
