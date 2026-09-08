# Catálogo de esencias y fuentes de obtención — MorphSummon

Documento de referencia del sistema de desbloqueo de apariencias de `mod-morphsummon` para AzerothCore.

> [!IMPORTANT]
> Esta lista se genera a partir del **loot real configurado** en `creature_loot_template`, no únicamente de la fuente declarada en el catálogo. Si varios NPC comparten un mismo `lootid`, todos aparecen como fuentes reales de la esencia.

## Estado de validación

- **Esencias desbloqueables:** 79 / 79.
- **Asociaciones reales esencia → NPC:** 285.
- **Esencias sin ninguna fuente de loot:** 0.
- **Esencias sin ninguna ubicación resoluble:** 0.
- **Fuentes cuya ubicación se resolvió mediante `difficulty_entry_*`:** 49.
- **NPC únicos sin spawn estático resoluble:** 21 (37 asociaciones repartidas entre 17 esencias).

Las fuentes sin ubicación estática se conservan en el documento porque siguen siendo fuentes de loot válidas; suelen corresponder a criaturas invocadas, encuentros, eventos, quests o templates especiales. Tras el rebalanceo, **ninguna esencia depende exclusivamente de una fuente de este tipo**.

## Resumen por familia

| Familia | Esencias |
|---|---:|
| Diablillo | 7 |
| Abisario | 16 |
| Súcubo | 3 |
| Manáfago | 9 |
| Guardia vil | 4 |
| Necrófago | 23 |
| Elemental de agua | 3 |
| Armas del guardia vil | 14 |
| **Total** | **79** |

## Leyenda

- **Esencia ID**: ID del objeto custom (`91001–91079`).
- **Apariencia ID**: `CreatureDisplayID` de la apariencia; para las armas del guardia vil corresponde al ItemID visual del arma.
- **NPC ID**: `creature_template.entry` de la criatura que puede soltar la esencia.
- **Nv.**: nivel o rango de niveles del NPC.
- **Drop**: probabilidad configurada de obtener la esencia.
- **`vía difficulty_entry_*`**: el NPC de dificultad no tiene spawn propio; su ubicación se ha heredado correctamente del template base.
- **⚠ Ubicación no resuelta**: el NPC no dispone de un spawn estático resoluble mediante `creature` ni mediante `difficulty_entry_1/2/3`.

> [!NOTE]
> Los nombres de zona se conservan tal como los devuelve el conjunto de DBC usado para la consulta. Por eso algunas zonas o instancias aparecen en inglés.

## Índice

- [Diablillo](#diablillo)
- [Abisario](#abisario)
- [Súcubo](#sucubo)
- [Manáfago](#manafago)
- [Guardia vil](#guardia-vil)
- [Necrófago](#necrofago)
- [Elemental de agua](#elemental-de-agua)
- [Armas del guardia vil](#armas-del-guardia-vil)

## Fuentes reforzadas

Las siguientes esencias conservan su fuente especial temática, pero disponen también de una fuente repetible para evitar depender de encuentros ligados a quests:

| Esencia | Apariencia | Fuente repetible | Fuente especial |
|---:|---|---|---|
| `91017` | Señor del Vacío azul con armadura roja | Ánima del vacío inestable `[18869]` — Netherstorm | Barón del vacío Galaxis `[16939]` |
| `91018` | Señor del Vacío púrpura con armadura roja | Terror de El Nexo `[19307]` — Auchindoun: Mana-Tombs | Barón del vacío Galaxis `[16939]` |
| `91077` | Hacha 2 | Legionario guardia vil `[17152]` — Nagrand / Zangarmarsh | Guardián del portal de demonios `[11937]` |
| `91078` | Hacha 3 | Guardia apocalíptico Hoja Vil `[19853]` — Netherstorm | Guardián del portal de demonios `[11937]` |

## Diablillo

<details>
<summary><code>91001</code> — <strong>Esencia: Familiar vil</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `1185`
- **Zona(s) resuelta(s):** `Durotar`
- **Fuentes (1):**
  - Familiar vil [`3101`] — Nv. 3-4 — **Durotar**

</details>

<details>
<summary><code>91002</code> — <strong>Esencia: Diablillo jade</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `7552`
- **Zona(s) resuelta(s):** `Dire Maul`
- **Fuentes (1):**
  - Pusillín [`14354`] — Nv. 57 — **Dire Maul**

</details>

<details>
<summary><code>91003</code> — <strong>Esencia: Diablillo rojo</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `10811`
- **Zona(s) resuelta(s):** `Dire Maul`
- **Fuentes (1):**
  - Pusillín [`14354`] — Nv. 57 — **Dire Maul**

</details>

<details>
<summary><code>91004</code> — <strong>Esencia: Diablillo de Terrallende rojo</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `16888`
- **Zona(s) resuelta(s):** `Hellfire Citadel: Ramparts`, `Hellfire Citadel: The Blood Furnace`, `The Blood Furnace`
- **Fuentes (52):**
  - Avizor Fuego Infernal [`17517`] — Nv. 57-58 — ⚠ **Ubicación no resuelta**
  - Can de guerra Mano Destrozada [`17280`] — Nv. 59 — **Hellfire Citadel: Ramparts**
  - Vigía Fuego Infernal [`17309`] — Nv. 59 — **Hellfire Citadel: Ramparts**
  - Hambriento Mascahuesos [`17259`] — Nv. 60-61 — **Hellfire Citadel: Ramparts**
  - Cuervoso Mascahuesos [`17264`] — Nv. 60-61 — **Hellfire Citadel: Ramparts**
  - Taumaturgo oscuro Foso Sangrante [`17269`] — Nv. 60-61 — **Hellfire Citadel: Ramparts**
  - Arquero Foso Sangrante [`17270`] — Nv. 60-61 — **Hellfire Citadel: Ramparts**
  - Destructor Mascahuesos [`17271`] — Nv. 60-61 — **Hellfire Citadel: Ramparts**
  - Maestro de bestias Mascahuesos [`17455`] — Nv. 60 — **Hellfire Citadel: Ramparts**
  - Arúspice Foso Sangrante [`17478`] — Nv. 60-61 — **Hellfire Citadel: Ramparts**
  - Desgarrador Mascahuesos [`17281`] — Nv. 61 — **Hellfire Citadel: Ramparts**
  - Déspota Riecráneos [`17370`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Brujo Sombraluna [`17371`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Invocador Sombraluna [`17395`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Adepto Sombraluna [`17397`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Orco vil naciente [`17398`] — Nv. 61-62 — **Hellfire Citadel: The Blood Furnace**
  - Seductora [`17399`] — Nv. 61 — ⚠ **Ubicación no resuelta**
  - Técnico Sombraluna [`17414`] — Nv. 61-62 — **Hellfire Citadel: The Blood Furnace**
  - Diablillo Fuego Infernal [`17477`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Pícaro Riecráneos [`17491`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Legionario Riecráneos [`17626`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Tosco guardia vil [`18894`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Familiar Fuego Infernal [`19016`] — Nv. 61 — ⚠ **Ubicación no resuelta**
  - Neófito orco vil [`17429`] — Nv. 62 — ⚠ **Ubicación no resuelta**
  - Celador Riecráneos [`17624`] — Nv. 62 — **Hellfire Citadel: The Blood Furnace**
  - Canalizador Sombraluna [`17653`] — Nv. 62 — **The Blood Furnace**
  - Hellfire Watcher (1) [`18058`] — Nv. 69 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17309`)_
  - Shattered Hand Warhound (1) [`18059`] — Nv. 69 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17280`)_
  - Shadowmoon Adept (1) [`18615`] — Nv. 69-70 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17397`)_
  - Shadowmoon Summoner (1) [`18617`] — Nv. 69-70 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17395`)_
  - Felguard Brute (1) [`21645`] — Nv. 69-70 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `18894`)_
  - Bleeding Hollow Archer (1) [`18048`] — Nv. 70-71 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17270`)_
  - Bonechewer Beastmaster (1) [`18051`] — Nv. 70 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17455`)_
  - Bonechewer Destroyer (1) [`18052`] — Nv. 70-71 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17271`)_
  - Hellfire Sentry (1) [`18057`] — Nv. 70 — ⚠ **Ubicación no resuelta**
  - Hellfire Imp (1) [`18606`] — Nv. 70 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17477`)_
  - Laughing Skull Enforcer (1) [`18608`] — Nv. 70 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17370`)_
  - Laughing Skull Legionnaire (1) [`18609`] — Nv. 70 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17626`)_
  - Laughing Skull Rogue (1) [`18610`] — Nv. 70 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17491`)_
  - Shadowmoon Technician (1) [`18618`] — Nv. 70 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17414`)_
  - Shadowmoon Warlock (1) [`18619`] — Nv. 70 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17371`)_
  - Hellfire Familiar (1) [`21646`] — Nv. 70 — ⚠ **Ubicación no resuelta**
  - Bleeding Hollow Darkcaster (1) [`18049`] — Nv. 71 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17269`)_
  - Bleeding Hollow Scryer (1) [`18050`] — Nv. 71 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17478`)_
  - Bonechewer Hungerer (1) [`18053`] — Nv. 71 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17259`)_
  - Bonechewer Ravener (1) [`18054`] — Nv. 71 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17264`)_
  - Bonechewer Ripper (1) [`18055`] — Nv. 71 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17281`)_
  - Fel Orc Neophyte (1) [`18603`] — Nv. 71 — ⚠ **Ubicación no resuelta**
  - Laughing Skull Warden (1) [`18611`] — Nv. 71 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17624`)_
  - Nascent Fel Orc (1) [`18612`] — Nv. 71 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17398`)_
  - Seductress (1) [`18614`] — Nv. 71 — ⚠ **Ubicación no resuelta**
  - Shadowmoon Channeler (1) [`18620`] — Nv. 71 — **The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17653`)_

</details>

<details>
<summary><code>91005</code> — <strong>Esencia: Diablillo de Terrallende púrpura</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `16889`
- **Zona(s) resuelta(s):** `Shadowmoon Valley`
- **Fuentes (1):**
  - Diablillo Forja Muerta [`20887`] — Nv. 67 — **Shadowmoon Valley**

</details>

<details>
<summary><code>91006</code> — <strong>Esencia: Diablillo de Terrallende amarillo</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `16890`
- **Zona(s) resuelta(s):** `Blade's Edge Mountains`
- **Fuentes (1):**
  - Diablillo agostador [`21021`] — Nv. 67-68 — **Blade's Edge Mountains**

</details>

<details>
<summary><code>91007</code> — <strong>Esencia: Diablillo de Terrallende blanco</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `16891`
- **Zona(s) resuelta(s):** `Hellfire Citadel: Ramparts`, `Hellfire Citadel: The Blood Furnace`, `The Blood Furnace`
- **Fuentes (52):**
  - Avizor Fuego Infernal [`17517`] — Nv. 57-58 — ⚠ **Ubicación no resuelta**
  - Can de guerra Mano Destrozada [`17280`] — Nv. 59 — **Hellfire Citadel: Ramparts**
  - Vigía Fuego Infernal [`17309`] — Nv. 59 — **Hellfire Citadel: Ramparts**
  - Hambriento Mascahuesos [`17259`] — Nv. 60-61 — **Hellfire Citadel: Ramparts**
  - Cuervoso Mascahuesos [`17264`] — Nv. 60-61 — **Hellfire Citadel: Ramparts**
  - Taumaturgo oscuro Foso Sangrante [`17269`] — Nv. 60-61 — **Hellfire Citadel: Ramparts**
  - Arquero Foso Sangrante [`17270`] — Nv. 60-61 — **Hellfire Citadel: Ramparts**
  - Destructor Mascahuesos [`17271`] — Nv. 60-61 — **Hellfire Citadel: Ramparts**
  - Maestro de bestias Mascahuesos [`17455`] — Nv. 60 — **Hellfire Citadel: Ramparts**
  - Arúspice Foso Sangrante [`17478`] — Nv. 60-61 — **Hellfire Citadel: Ramparts**
  - Desgarrador Mascahuesos [`17281`] — Nv. 61 — **Hellfire Citadel: Ramparts**
  - Déspota Riecráneos [`17370`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Brujo Sombraluna [`17371`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Invocador Sombraluna [`17395`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Adepto Sombraluna [`17397`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Orco vil naciente [`17398`] — Nv. 61-62 — **Hellfire Citadel: The Blood Furnace**
  - Seductora [`17399`] — Nv. 61 — ⚠ **Ubicación no resuelta**
  - Técnico Sombraluna [`17414`] — Nv. 61-62 — **Hellfire Citadel: The Blood Furnace**
  - Diablillo Fuego Infernal [`17477`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Pícaro Riecráneos [`17491`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Legionario Riecráneos [`17626`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Tosco guardia vil [`18894`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Familiar Fuego Infernal [`19016`] — Nv. 61 — ⚠ **Ubicación no resuelta**
  - Neófito orco vil [`17429`] — Nv. 62 — ⚠ **Ubicación no resuelta**
  - Celador Riecráneos [`17624`] — Nv. 62 — **Hellfire Citadel: The Blood Furnace**
  - Canalizador Sombraluna [`17653`] — Nv. 62 — **The Blood Furnace**
  - Hellfire Watcher (1) [`18058`] — Nv. 69 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17309`)_
  - Shattered Hand Warhound (1) [`18059`] — Nv. 69 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17280`)_
  - Shadowmoon Adept (1) [`18615`] — Nv. 69-70 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17397`)_
  - Shadowmoon Summoner (1) [`18617`] — Nv. 69-70 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17395`)_
  - Felguard Brute (1) [`21645`] — Nv. 69-70 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `18894`)_
  - Bleeding Hollow Archer (1) [`18048`] — Nv. 70-71 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17270`)_
  - Bonechewer Beastmaster (1) [`18051`] — Nv. 70 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17455`)_
  - Bonechewer Destroyer (1) [`18052`] — Nv. 70-71 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17271`)_
  - Hellfire Sentry (1) [`18057`] — Nv. 70 — ⚠ **Ubicación no resuelta**
  - Hellfire Imp (1) [`18606`] — Nv. 70 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17477`)_
  - Laughing Skull Enforcer (1) [`18608`] — Nv. 70 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17370`)_
  - Laughing Skull Legionnaire (1) [`18609`] — Nv. 70 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17626`)_
  - Laughing Skull Rogue (1) [`18610`] — Nv. 70 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17491`)_
  - Shadowmoon Technician (1) [`18618`] — Nv. 70 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17414`)_
  - Shadowmoon Warlock (1) [`18619`] — Nv. 70 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17371`)_
  - Hellfire Familiar (1) [`21646`] — Nv. 70 — ⚠ **Ubicación no resuelta**
  - Bleeding Hollow Darkcaster (1) [`18049`] — Nv. 71 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17269`)_
  - Bleeding Hollow Scryer (1) [`18050`] — Nv. 71 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17478`)_
  - Bonechewer Hungerer (1) [`18053`] — Nv. 71 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17259`)_
  - Bonechewer Ravener (1) [`18054`] — Nv. 71 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17264`)_
  - Bonechewer Ripper (1) [`18055`] — Nv. 71 — **Hellfire Citadel: Ramparts** _(vía `difficulty_entry_1` del NPC base `17281`)_
  - Fel Orc Neophyte (1) [`18603`] — Nv. 71 — ⚠ **Ubicación no resuelta**
  - Laughing Skull Warden (1) [`18611`] — Nv. 71 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17624`)_
  - Nascent Fel Orc (1) [`18612`] — Nv. 71 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17398`)_
  - Seductress (1) [`18614`] — Nv. 71 — ⚠ **Ubicación no resuelta**
  - Shadowmoon Channeler (1) [`18620`] — Nv. 71 — **The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17653`)_

</details>

## Abisario

<details>
<summary><code>91008</code> — <strong>Esencia: Abisario de Terrallende azul con armadura verde</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `16634`
- **Zona(s) resuelta(s):** `Hellfire Peninsula`
- **Fuentes (2):**
  - Abisario sin control [`16975`] — Nv. 60-61 — **Hellfire Peninsula**
  - Abisario inestable [`20145`] — Nv. 60 — ⚠ **Ubicación no resuelta**

</details>

<details>
<summary><code>91009</code> — <strong>Esencia: Abisario de Terrallende azul con armadura púrpura</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `17081`
- **Zona(s) resuelta(s):** `Bloodmyst Isle`, `Hellfire Peninsula`
- **Fuentes (2):**
  - Anomalía del vacío [`17550`] — Nv. 15-16 — **Bloodmyst Isle**
  - Abisario pícaro [`16974`] — Nv. 60-61 — **Hellfire Peninsula**

</details>

<details>
<summary><code>91010</code> — <strong>Esencia: Abisario de Terrallende azul con armadura azul</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `17298`
- **Zona(s) resuelta(s):** `Hellfire Peninsula`
- **Fuentes (1):**
  - Abisario sin control [`16975`] — Nv. 60-61 — **Hellfire Peninsula**

</details>

<details>
<summary><code>91011</code> — <strong>Esencia: Abisario de Terrallende azul con armadura roja</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `18366`
- **Zona(s) resuelta(s):** `Nagrand`
- **Fuentes (1):**
  - Engendro del vacío [`17981`] — Nv. 65-66 — **Nagrand**

</details>

<details>
<summary><code>91012</code> — <strong>Esencia: Abisario de Terrallende púrpura con armadura azul</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `18953`
- **Zona(s) resuelta(s):** `Hellfire Peninsula`
- **Fuentes (1):**
  - Abisario en colapso [`17014`] — Nv. 61-62 — **Hellfire Peninsula**

</details>

<details>
<summary><code>91013</code> — <strong>Esencia: Invocador del Vacío azul</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `17704`
- **Zona(s) resuelta(s):** `Bloodmyst Isle`
- **Fuentes (1):**
  - Anomalía del vacío [`17550`] — Nv. 15-16 — **Bloodmyst Isle**

</details>

<details>
<summary><code>91014</code> — <strong>Esencia: Invocador del Vacío púrpura</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `17746`
- **Zona(s) resuelta(s):** `Hellfire Peninsula`
- **Fuentes (1):**
  - Abisario en colapso [`17014`] — Nv. 61-62 — **Hellfire Peninsula**

</details>

<details>
<summary><code>91015</code> — <strong>Esencia: Invocador del Vacío rojo</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `19884`
- **Zona(s) resuelta(s):** `Nagrand`
- **Fuentes (1):**
  - Engendro del vacío [`17981`] — Nv. 65-66 — **Nagrand**

</details>

<details>
<summary><code>91016</code> — <strong>Esencia: Señor del Vacío púrpura con armadura púrpura</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `16635`
- **Zona(s) resuelta(s):** `Netherstorm`
- **Fuentes (1):**
  - Ánima del vacío inestable [`18869`] — Nv. 68-69 — **Netherstorm**

</details>

<details>
<summary><code>91017</code> — <strong>Esencia: Señor del Vacío azul con armadura roja</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `18170`
- **Zona(s) resuelta(s):** `Netherstorm`
- **Fuentes (2):**
  - Barón del vacío Galaxis [`16939`] — Nv. 63 — ⚠ **Ubicación no resuelta**
  - Ánima del vacío inestable [`18869`] — Nv. 68-69 — **Netherstorm**

</details>

<details>
<summary><code>91018</code> — <strong>Esencia: Señor del Vacío púrpura con armadura roja</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `18958`
- **Zona(s) resuelta(s):** `Auchindoun: Mana-Tombs`
- **Fuentes (2):**
  - Barón del vacío Galaxis [`16939`] — Nv. 63 — ⚠ **Ubicación no resuelta**
  - Terror de El Nexo [`19307`] — Nv. 64 — **Auchindoun: Mana-Tombs**

</details>

<details>
<summary><code>91019</code> — <strong>Esencia: Señor del Vacío púrpura con armadura azul</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `19883`
- **Zona(s) resuelta(s):** `Auchindoun: Mana-Tombs`
- **Fuentes (1):**
  - Terror de El Nexo [`19307`] — Nv. 64 — **Auchindoun: Mana-Tombs**

</details>

<details>
<summary><code>91020</code> — <strong>Esencia: Señor del Vacío rojo con armadura azul</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `26214`
- **Zona(s) resuelta(s):** `Auchindoun: Mana-Tombs`
- **Fuentes (1):**
  - Terror de El Nexo [`19307`] — Nv. 64 — **Auchindoun: Mana-Tombs**

</details>

<details>
<summary><code>91021</code> — <strong>Esencia: Espectro del Vacío púrpura</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `18050`
- **Zona(s) resuelta(s):** `Auchindoun: Mana-Tombs`, `Netherstorm`
- **Fuentes (3):**
  - Terror de El Nexo [`19307`] — Nv. 64 — **Auchindoun: Mana-Tombs**
  - Ánima del vacío inestable [`18869`] — Nv. 68-69 — **Netherstorm**
  - Nexus Terror (1) [`20265`] — Nv. 70 — **Auchindoun: Mana-Tombs** _(vía `difficulty_entry_1` del NPC base `19307`)_

</details>

<details>
<summary><code>91022</code> — <strong>Esencia: Espectro del Vacío azul</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `18069`
- **Zona(s) resuelta(s):** `Netherstorm`
- **Fuentes (1):**
  - Ánima del vacío inestable [`18869`] — Nv. 68-69 — **Netherstorm**

</details>

<details>
<summary><code>91023</code> — <strong>Esencia: Espectro del Vacío rojo</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `18919`
- **Zona(s) resuelta(s):** `Auchindoun: Mana-Tombs`
- **Fuentes (1):**
  - Terror de El Nexo [`19307`] — Nv. 64 — **Auchindoun: Mana-Tombs**

</details>

## Súcubo

<details>
<summary><code>91024</code> — <strong>Esencia: Súcubo magenta</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `159`
- **Zona(s) resuelta(s):** `Desolace`
- **Fuentes (3):**
  - Doncella abisal [`4679`] — Nv. 37-38 — **Desolace**
  - Doncella de Disciplina [`18663`] — Nv. 70 — ⚠ **Ubicación no resuelta**
  - Maiden of Discipline (1) [`20655`] — Nv. 70 — ⚠ **Ubicación no resuelta**

</details>

<details>
<summary><code>91025</code> — <strong>Esencia: Súcubo azul</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `2737`
- **Zona(s) resuelta(s):** `Desolace`
- **Fuentes (1):**
  - Hechicera abisal [`4684`] — Nv. 39-40 — **Desolace**

</details>

<details>
<summary><code>91026</code> — <strong>Esencia: Súcubo rojo</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `10925`
- **Zona(s) resuelta(s):** `Azshara`, `Scholomance`
- **Fuentes (3):**
  - Simone la Seductora [`14533`] — Nv. 60 — ⚠ **Ubicación no resuelta**
  - Lady Hederine [`10201`] — Nv. 61 — **Azshara**
  - Administrador de sangre de Kirtonos [`14861`] — Nv. 61 — **Scholomance**

</details>

## Manáfago

<details>
<summary><code>91027</code> — <strong>Esencia: Cazamagos azul</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `24906`
- **Zona(s) resuelta(s):** `Borean Tundra`, `Dragonblight`, `The Nexus`
- **Fuentes (5):**
  - Can de Berilo [`25355`] — Nv. 69-70 — **Borean Tundra**
  - Asesino de magos de Gelidar [`25718`] — Nv. 69 — **Borean Tundra**
  - Acechador Reposo Lunar [`26281`] — Nv. 71-72 — **Dragonblight**
  - Asesino de magos [`26730`] — Nv. 71 — **The Nexus**
  - Mage Slayer (1) [`30473`] — Nv. 80 — **The Nexus** _(vía `difficulty_entry_1` del NPC base `26730`)_

</details>

<details>
<summary><code>91028</code> — <strong>Esencia: Cazamagos verde</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `24907`
- **Zona(s) resuelta(s):** `Borean Tundra`
- **Fuentes (1):**
  - Asesino de magos de Gelidar [`25718`] — Nv. 69 — **Borean Tundra**

</details>

<details>
<summary><code>91029</code> — <strong>Esencia: Cazamagos rojo</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `24908`
- **Zona(s) resuelta(s):** `Icecrown`
- **Fuentes (1):**
  - Can de peste hambriento [`30952`] — Nv. 80 — **Icecrown**

</details>

<details>
<summary><code>91030</code> — <strong>Esencia: Can azul</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `3916`
- **Zona(s) resuelta(s):** `Western Plaguelands`, `Redridge Mountains`
- **Fuentes (2):**
  - Can oscuro voraz [`1549`] — Nv. 9-10 — **Western Plaguelands**
  - Sirviente de Ilgalar [`819`] — Nv. 24-25 — **Redridge Mountains**

</details>

<details>
<summary><code>91031</code> — <strong>Esencia: Can gris</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `6195`
- **Zona(s) resuelta(s):** `Nagrand`
- **Fuentes (1):**
  - Can Sombra de Muerte [`22394`] — Nv. 70-71 — **Nagrand**

</details>

<details>
<summary><code>91032</code> — <strong>Esencia: Can púrpura</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `7890`
- **Zona(s) resuelta(s):** `Eastern Plaguelands`
- **Fuentes (1):**
  - Cachorro de can de peste [`8596`] — Nv. 53-54 — **Eastern Plaguelands**

</details>

<details>
<summary><code>91033</code> — <strong>Esencia: Can rojo</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `8180`
- **Zona(s) resuelta(s):** `Blackrock Depths`
- **Fuentes (1):**
  - Can de sangre [`8921`] — Nv. 49-50 — **Blackrock Depths**

</details>

<details>
<summary><code>91034</code> — <strong>Esencia: Can blanco</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `14312`
- **Zona(s) resuelta(s):** `Nagrand`
- **Fuentes (1):**
  - Can Sombra de Muerte [`22394`] — Nv. 70-71 — **Nagrand**

</details>

<details>
<summary><code>91035</code> — <strong>Esencia: Zergling</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `10993`
- **Zona(s) resuelta(s):** `Teldrassil`
- **Fuentes (1):**
  - Grell sañoso [`2005`] — Nv. 7 — **Teldrassil**

</details>

## Guardia vil

<details>
<summary><code>91036</code> — <strong>Esencia: Guardia vil azul</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `5048`
- **Zona(s) resuelta(s):** `Ashenvale`, `Durotar`
- **Fuentes (2):**
  - Guardia vil vagabundo [`6115`] — Nv. 29-30 — **Ashenvale**
  - Guardia vil vagabundo [`6115`] — Nv. 29-30 — **Durotar**

</details>

<details>
<summary><code>91037</code> — <strong>Esencia: Guardia vil amarillo</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `5049`
- **Zona(s) resuelta(s):** `Stonetalon Mountains`, `Desolace`
- **Fuentes (2):**
  - Guardia vil inferior [`3772`] — Nv. 23-24 — **Stonetalon Mountains**
  - Guardiavil [`4677`] — Nv. 37-38 — **Desolace**

</details>

<details>
<summary><code>91038</code> — <strong>Esencia: Guardia vil rojo</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `18342`
- **Zona(s) resuelta(s):** `Blackrock Spire`
- **Fuentes (1):**
  - Guardia vil ardiente [`10263`] — Nv. 56-57 — **Blackrock Spire**

</details>

<details>
<summary><code>91039</code> — <strong>Esencia: Guardia vil blanco</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `19901`
- **Zona(s) resuelta(s):** `Nagrand`, `Zangarmarsh`
- **Fuentes (2):**
  - Legionario guardia vil [`17152`] — Nv. 67-68 — **Nagrand**
  - Legionario guardia vil [`17152`] — Nv. 67-68 — **Zangarmarsh**

</details>

## Necrófago

<details>
<summary><code>91040</code> — <strong>Esencia: Necrófago gris</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `137`
- **Zona(s) resuelta(s):** `Eversong Woods`, `Ghostlands`, `Duskwood`, `Alterac Mountains`, `Western Plaguelands`, `Dragonblight`
- **Fuentes (7):**
  - Merodeador pataputrefacta [`15658`] — Nv. 8-9 — **Eversong Woods**
  - Merodeador pataputrefacta [`15658`] — Nv. 8-9 — **Ghostlands**
  - Caníbal ganglioso [`16309`] — Nv. 12-13 — **Ghostlands**
  - Podrido [`948`] — Nv. 25-26 — **Duskwood**
  - Necrófago en podredumbre [`1793`] — Nv. 54-55 — **Alterac Mountains**
  - Necrófago en podredumbre [`1793`] — Nv. 54-55 — **Western Plaguelands**
  - Cavador de baldío [`26492`] — Nv. 72-73 — **Dragonblight**

</details>

<details>
<summary><code>91041</code> — <strong>Esencia: Necrófago rojo</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `414`
- **Zona(s) resuelta(s):** `Alterac Mountains`, `Western Plaguelands`, `Stratholme`, `Icecrown`
- **Fuentes (5):**
  - Necrófago abrasador [`1795`] — Nv. 55-56 — **Alterac Mountains**
  - Necrófago abrasador [`1795`] — Nv. 55-56 — **Western Plaguelands**
  - Necrófago andrajoso [`10497`] — Nv. 58 — ⚠ **Ubicación no resuelta**
  - Necrófago desgarracarne [`10407`] — Nv. 59-60 — **Stratholme**
  - Necrófago descompuesto [`31812`] — Nv. 79-80 — **Icecrown**

</details>

<details>
<summary><code>91042</code> — <strong>Esencia: Necrófago blanco</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `519`
- **Zona(s) resuelta(s):** `Duskwood`, `Western Plaguelands`, `Scholomance`, `The Culling of Stratholme`
- **Fuentes (5):**
  - Propagador de peste [`604`] — Nv. 27-28 — **Duskwood**
  - Crinatroz [`1847`] — Nv. 52 — **Western Plaguelands**
  - Necrófago malsano [`10495`] — Nv. 58-59 — **Scholomance**
  - Necrófago iracundo [`27729`] — Nv. 80 — **The Culling of Stratholme**
  - Enraging Ghoul (1) [`31178`] — Nv. 80 — **The Culling of Stratholme** _(vía `difficulty_entry_1` del NPC base `27729`)_

</details>

<details>
<summary><code>91043</code> — <strong>Esencia: Necrófago azul</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `547`
- **Zona(s) resuelta(s):** `Duskwood`
- **Fuentes (1):**
  - Podrido [`948`] — Nv. 25-26 — **Duskwood**

</details>

<details>
<summary><code>91044</code> — <strong>Esencia: Zombi negro (manco)</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `1196`
- **Zona(s) resuelta(s):** `Tirisfal Glades`, `Scarlet Monastery`, `Dustwallow Marsh`
- **Fuentes (4):**
  - Anciano en podredumbre [`1530`] — Nv. 10-11 — **Tirisfal Glades**
  - Thurman Agamand [`1656`] — Nv. 10 — **Tirisfal Glades**
  - Muerto angustioso [`6426`] — Nv. 31-33 — **Scarlet Monastery**
  - Raquítico resucitado [`23555`] — Nv. 35-36 — **Dustwallow Marsh**

</details>

<details>
<summary><code>91045</code> — <strong>Esencia: Zombi verde (manco)</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `1197`
- **Zona(s) resuelta(s):** `Western Plaguelands`, `Ghostlands`
- **Fuentes (3):**
  - Horror desgarbado [`1528`] — Nv. 8-9 — **Western Plaguelands**
  - Hambriento resucitado [`16301`] — Nv. 13-14 — **Ghostlands**
  - [PH] Dragonblight Carrion Field Zombie [`26490`] — Nv. 72 — ⚠ **Ubicación no resuelta**

</details>

<details>
<summary><code>91046</code> — <strong>Esencia: Zombi verde mar (manco)</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `1198`
- **Zona(s) resuelta(s):** `Western Plaguelands`
- **Fuentes (1):**
  - Horror sangrante [`1529`] — Nv. 9-10 — **Western Plaguelands**

</details>

<details>
<summary><code>91047</code> — <strong>Esencia: Zombi negro (con flechas)</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `1200`
- **Zona(s) resuelta(s):** `Tirisfal Glades`, `Ghostlands`
- **Fuentes (2):**
  - Muerto en podredumbre [`1525`] — Nv. 5-6 — **Tirisfal Glades**
  - Trepador resucitado [`16300`] — Nv. 9-10 — **Ghostlands**

</details>

<details>
<summary><code>91048</code> — <strong>Esencia: Zombi verde (con flechas)</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `1201`
- **Zona(s) resuelta(s):** `Tirisfal Glades`, `Ghostlands`
- **Fuentes (3):**
  - Cuerpo devastado [`1526`] — Nv. 6-7 — **Tirisfal Glades**
  - Hambriento resucitado [`16301`] — Nv. 13-14 — **Ghostlands**
  - [PH] Dragonblight Carrion Field Zombie [`26490`] — Nv. 72 — ⚠ **Ubicación no resuelta**

</details>

<details>
<summary><code>91049</code> — <strong>Esencia: Zombi verde mar (con flechas)</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `1202`
- **Zona(s) resuelta(s):** `Western Plaguelands`, `Dragonblight`
- **Fuentes (2):**
  - Muerte hambrienta [`1527`] — Nv. 7-8 — **Western Plaguelands**
  - Noble reanimado [`27552`] — Nv. 71-72 — **Dragonblight**

</details>

<details>
<summary><code>91050</code> — <strong>Esencia: Zombi verde mar (con espada)</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `24707`
- **Zona(s) resuelta(s):** `Dragonblight`
- **Fuentes (1):**
  - Noble reanimado [`27552`] — Nv. 71-72 — **Dragonblight**

</details>

<details>
<summary><code>91051</code> — <strong>Esencia: Esqueleto (con casco)</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `158`
- **Zona(s) resuelta(s):** `Ghostlands`
- **Fuentes (1):**
  - Esqueleto Huesobravo [`16303`] — Nv. 10-11 — **Ghostlands**

</details>

<details>
<summary><code>91052</code> — <strong>Esencia: Esqueleto verde (con casco)</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `201`
- **Zona(s) resuelta(s):** `Stratholme`
- **Fuentes (1):**
  - Guardián esquelético [`10390`] — Nv. 55-56 — **Stratholme**

</details>

<details>
<summary><code>91053</code> — <strong>Esencia: Esqueleto verde azulado oscuro (con casco)</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `535`
- **Zona(s) resuelta(s):** `Tirisfal Glades`
- **Fuentes (1):**
  - Soldado testapartida [`1523`] — Nv. 8-9 — **Tirisfal Glades**

</details>

<details>
<summary><code>91054</code> — <strong>Esencia: Esqueleto blanco</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `7550`
- **Zona(s) resuelta(s):** `Western Plaguelands`, `Scholomance`, `Karazhan`
- **Fuentes (5):**
  - Lacayo resucitado [`10482`] — Nv. 1 — ⚠ **Ubicación no resuelta**
  - Maligno esquelético [`531`] — Nv. 24-25 — ⚠ **Ubicación no resuelta**
  - Esqueleto deambulante [`10816`] — Nv. 55 — **Western Plaguelands**
  - Aberración resucitada [`10485`] — Nv. 57-58 — **Scholomance**
  - Camarero esquelético [`16415`] — Nv. 71 — **Karazhan**

</details>

<details>
<summary><code>91055</code> — <strong>Esencia: Esqueleto amarillo</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `7555`
- **Zona(s) resuelta(s):** `Duskwood`, `Stratholme`
- **Fuentes (3):**
  - Sanador esquelético [`787`] — Nv. 26-27 — **Duskwood**
  - Golpeflama [`16383`] — Nv. 53-55 — ⚠ **Ubicación no resuelta**
  - Guardián esquelético [`10390`] — Nv. 55-56 — **Stratholme**

</details>

<details>
<summary><code>91056</code> — <strong>Esencia: Esqueleto azul</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `9783`
- **Zona(s) resuelta(s):** `Deadwind Pass`, `Razorfen Downs`
- **Fuentes (2):**
  - Mago esquelético [`203`] — Nv. 22-23 — **Deadwind Pass**
  - Tejescarcha esquelético [`7341`] — Nv. 37-38 — **Razorfen Downs**

</details>

<details>
<summary><code>91057</code> — <strong>Esencia: Esqueleto rojo</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `9784`
- **Zona(s) resuelta(s):** `Stratholme`
- **Fuentes (1):**
  - Rabioso esquelético [`10391`] — Nv. 56-57 — **Stratholme**

</details>

<details>
<summary><code>91058</code> — <strong>Esencia: Esqueleto verde</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `9785`
- **Zona(s) resuelta(s):** `Eversong Woods`, `Stratholme`
- **Fuentes (2):**
  - Saqueador huesopeste [`15654`] — Nv. 5-6 — **Eversong Woods**
  - Guardián esquelético [`10390`] — Nv. 55-56 — **Stratholme**

</details>

<details>
<summary><code>91059</code> — <strong>Esencia: Esqueleto negro</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `9786`
- **Zona(s) resuelta(s):** `Deadwind Pass`, `Duskwood`, `Stratholme`, `Scholomance`, `Dragonblight`, `Wintergrasp`
- **Fuentes (8):**
  - Lacayo resucitado [`10482`] — Nv. 1 — ⚠ **Ubicación no resuelta**
  - Horror esquelético [`202`] — Nv. 23-24 — **Deadwind Pass**
  - Horror esquelético [`202`] — Nv. 23-24 — **Duskwood**
  - Taumaturgo umbrío esquelético [`7340`] — Nv. 36 — ⚠ **Ubicación no resuelta**
  - Rabioso esquelético [`10391`] — Nv. 56-57 — **Stratholme**
  - Aberración resucitada [`10485`] — Nv. 57-58 — **Scholomance**
  - Esqueleto en llamas [`27360`] — Nv. 73-74 — **Dragonblight**
  - Esqueleto en llamas [`27360`] — Nv. 73-74 — **Wintergrasp**

</details>

<details>
<summary><code>91060</code> — <strong>Esencia: Esqueleto (sin casco)</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `27355`
- **Zona(s) resuelta(s):** `Dragonblight`, `Wintergrasp`
- **Fuentes (2):**
  - Esqueleto en llamas [`27360`] — Nv. 73-74 — **Dragonblight**
  - Esqueleto en llamas [`27360`] — Nv. 73-74 — **Wintergrasp**

</details>

<details>
<summary><code>91061</code> — <strong>Esencia: Esqueleto verde azulado oscuro (sin casco)</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `27356`
- **Zona(s) resuelta(s):** `Ghostlands`
- **Fuentes (1):**
  - Esqueleto Huesobravo [`16303`] — Nv. 10-11 — **Ghostlands**

</details>

<details>
<summary><code>91062</code> — <strong>Esencia: Esqueleto verde (sin casco)</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `27357`
- **Zona(s) resuelta(s):** `Eversong Woods`
- **Fuentes (1):**
  - Saqueador huesopeste [`15654`] — Nv. 5-6 — **Eversong Woods**

</details>

## Elemental de agua

<details>
<summary><code>91063</code> — <strong>Esencia: Elemental de agua verde</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `4907`
- **Zona(s) resuelta(s):** `Gnomeregan`, `Nagrand`, `Zangarmarsh`
- **Fuentes (3):**
  - Horror irradiado [`6220`] — Nv. 28-29 — **Gnomeregan**
  - Engendro de lodo [`17154`] — Nv. 64-66 — **Nagrand**
  - Engendro de lodo [`17154`] — Nv. 64-66 — **Zangarmarsh**

</details>

<details>
<summary><code>91064</code> — <strong>Esencia: Elemental de agua rojo</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `17045`
- **Zona(s) resuelta(s):** `Bloodmyst Isle`
- **Fuentes (1):**
  - Espíritu de agua podrido [`17358`] — Nv. 18-19 — **Bloodmyst Isle**

</details>

<details>
<summary><code>91065</code> — <strong>Esencia: Elemental de agua púrpura</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `27029`
- **Zona(s) resuelta(s):** `Gundrak`
- **Fuentes (2):**
  - Mojo viviente [`29830`] — Nv. 76 — **Gundrak**
  - Living Mojo (1) [`30938`] — Nv. 80-81 — **Gundrak** _(vía `difficulty_entry_1` del NPC base `29830`)_

</details>

## Armas del guardia vil

<details>
<summary><code>91066</code> — <strong>Esencia: Espada 1</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `1899`
- **Zona(s) resuelta(s):** `Blasted Lands`
- **Fuentes (1):**
  - Élite guarda vil [`8717`] — Nv. 61 — **Blasted Lands**

</details>

<details>
<summary><code>91067</code> — <strong>Esencia: Espada 2</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `10613`
- **Zona(s) resuelta(s):** `Hellfire Peninsula`, `Blade's Edge Mountains`
- **Fuentes (2):**
  - Guardia de Cólera [`18975`] — Nv. 58-59 — **Hellfire Peninsula**
  - Sobrestante Azarad [`20685`] — Nv. 70 — **Blade's Edge Mountains**

</details>

<details>
<summary><code>91068</code> — <strong>Esencia: Espada 3</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `10614`
- **Zona(s) resuelta(s):** `Blackrock Spire`
- **Fuentes (1):**
  - Guardia vil ardiente [`10263`] — Nv. 56-57 — **Blackrock Spire**

</details>

<details>
<summary><code>91069</code> — <strong>Esencia: Espada 4</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `12889`
- **Zona(s) resuelta(s):** `Netherstorm`
- **Fuentes (1):**
  - Guardia apocalíptico Hoja Vil [`19853`] — Nv. 67-68 — **Netherstorm**

</details>

<details>
<summary><code>91070</code> — <strong>Esencia: Espada 5</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `12902`
- **Zona(s) resuelta(s):** `Hellfire Peninsula`, `Nagrand`, `Zangarmarsh`
- **Fuentes (4):**
  - Legionario del Campamento Forja [`16954`] — Nv. 60-61 — **Hellfire Peninsula**
  - Destructor guardia vil [`18977`] — Nv. 60 — **Hellfire Peninsula**
  - Legionario guardia vil [`17152`] — Nv. 67-68 — **Nagrand**
  - Legionario guardia vil [`17152`] — Nv. 67-68 — **Zangarmarsh**

</details>

<details>
<summary><code>91071</code> — <strong>Esencia: Espada 6</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `13504`
- **Zona(s) resuelta(s):** `Bloodmyst Isle`, `Stonetalon Mountains`, `Desolace`, `Blade's Edge Mountains`
- **Fuentes (5):**
  - Sironas [`17678`] — Nv. 20 — **Bloodmyst Isle**
  - Guardia vil inferior [`3772`] — Nv. 23-24 — **Stonetalon Mountains**
  - Akkrilus [`3773`] — Nv. 26 — **Stonetalon Mountains**
  - Lord Azrethoc [`5760`] — Nv. 40 — **Desolace**
  - Maligno de cólera [`22291`] — Nv. 70-72 — **Blade's Edge Mountains**

</details>

<details>
<summary><code>91072</code> — <strong>Esencia: Maza 1</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `2809`
- **Zona(s) resuelta(s):** `Teldrassil`, `Ashenvale`, `Durotar`
- **Fuentes (5):**
  - Grell sañoso [`2005`] — Nv. 7 — **Teldrassil**
  - Guardia vil vagabundo [`6115`] — Nv. 29-30 — **Ashenvale**
  - Guardia vil vagabundo [`6115`] — Nv. 29-30 — **Durotar**
  - Azotadora Mannoroc [`11697`] — Nv. 29-30 — **Ashenvale**
  - Azotadora Mannoroc [`11697`] — Nv. 29-30 — **Durotar**

</details>

<details>
<summary><code>91073</code> — <strong>Esencia: Maza 2</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `5491`
- **Zona(s) resuelta(s):** `Blasted Lands`, `Hellfire Citadel: Ramparts`, `Hellfire Citadel: The Blood Furnace`, `The Blood Furnace`
- **Fuentes (29):**
  - Avizor guardia vil [`6011`] — Nv. 54-55 — **Blasted Lands**
  - Avizor Fuego Infernal [`17517`] — Nv. 57-58 — ⚠ **Ubicación no resuelta**
  - Can de guerra Mano Destrozada [`17280`] — Nv. 59 — **Hellfire Citadel: Ramparts**
  - Vigía Fuego Infernal [`17309`] — Nv. 59 — **Hellfire Citadel: Ramparts**
  - Hambriento Mascahuesos [`17259`] — Nv. 60-61 — **Hellfire Citadel: Ramparts**
  - Cuervoso Mascahuesos [`17264`] — Nv. 60-61 — **Hellfire Citadel: Ramparts**
  - Taumaturgo oscuro Foso Sangrante [`17269`] — Nv. 60-61 — **Hellfire Citadel: Ramparts**
  - Arquero Foso Sangrante [`17270`] — Nv. 60-61 — **Hellfire Citadel: Ramparts**
  - Destructor Mascahuesos [`17271`] — Nv. 60-61 — **Hellfire Citadel: Ramparts**
  - Maestro de bestias Mascahuesos [`17455`] — Nv. 60 — **Hellfire Citadel: Ramparts**
  - Arúspice Foso Sangrante [`17478`] — Nv. 60-61 — **Hellfire Citadel: Ramparts**
  - Desgarrador Mascahuesos [`17281`] — Nv. 61 — **Hellfire Citadel: Ramparts**
  - Déspota Riecráneos [`17370`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Brujo Sombraluna [`17371`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Invocador Sombraluna [`17395`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Adepto Sombraluna [`17397`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Orco vil naciente [`17398`] — Nv. 61-62 — **Hellfire Citadel: The Blood Furnace**
  - Seductora [`17399`] — Nv. 61 — ⚠ **Ubicación no resuelta**
  - Técnico Sombraluna [`17414`] — Nv. 61-62 — **Hellfire Citadel: The Blood Furnace**
  - Diablillo Fuego Infernal [`17477`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Pícaro Riecráneos [`17491`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Legionario Riecráneos [`17626`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Tosco guardia vil [`18894`] — Nv. 61 — **Hellfire Citadel: The Blood Furnace**
  - Familiar Fuego Infernal [`19016`] — Nv. 61 — ⚠ **Ubicación no resuelta**
  - Aniquilador guardia vil [`17400`] — Nv. 62 — **Hellfire Citadel: The Blood Furnace**
  - Neófito orco vil [`17429`] — Nv. 62 — ⚠ **Ubicación no resuelta**
  - Celador Riecráneos [`17624`] — Nv. 62 — **Hellfire Citadel: The Blood Furnace**
  - Canalizador Sombraluna [`17653`] — Nv. 62 — **The Blood Furnace**
  - Felguard Annihilator (1) [`18604`] — Nv. 71 — **Hellfire Citadel: The Blood Furnace** _(vía `difficulty_entry_1` del NPC base `17400`)_

</details>

<details>
<summary><code>91074</code> — <strong>Esencia: Maza 3</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `12950`
- **Zona(s) resuelta(s):** `Blackrock Spire`
- **Fuentes (1):**
  - Guardia vil ardiente [`10263`] — Nv. 56-57 — **Blackrock Spire**

</details>

<details>
<summary><code>91075</code> — <strong>Esencia: Maza 4</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `30670`
- **Zona(s) resuelta(s):** `Blade's Edge Mountains`
- **Fuentes (1):**
  - Sobrestante Azarad [`20685`] — Nv. 70 — **Blade's Edge Mountains**

</details>

<details>
<summary><code>91076</code> — <strong>Esencia: Hacha 1</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `5287`
- **Zona(s) resuelta(s):** `Terokkar Forest`
- **Fuentes (1):**
  - Soldado de choque Illidari [`19802`] — Nv. 68-69 — **Terokkar Forest**

</details>

<details>
<summary><code>91077</code> — <strong>Esencia: Hacha 2</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `14643`
- **Zona(s) resuelta(s):** `Nagrand`, `Zangarmarsh`
- **Fuentes (3):**
  - Guardián del portal de demonios [`11937`] — Nv. 38 — ⚠ **Ubicación no resuelta**
  - Legionario guardia vil [`17152`] — Nv. 67-68 — **Nagrand**
  - Legionario guardia vil [`17152`] — Nv. 67-68 — **Zangarmarsh**

</details>

<details>
<summary><code>91078</code> — <strong>Esencia: Hacha 3</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `14870`
- **Zona(s) resuelta(s):** `Netherstorm`
- **Fuentes (2):**
  - Guardián del portal de demonios [`11937`] — Nv. 38 — ⚠ **Ubicación no resuelta**
  - Guardia apocalíptico Hoja Vil [`19853`] — Nv. 67-68 — **Netherstorm**

</details>

<details>
<summary><code>91079</code> — <strong>Esencia: Arma de asta 1</strong> — Drop 2.5%</summary>

- **Apariencia ID:** `28365`
- **Zona(s) resuelta(s):** `Magtheridon's Lair`
- **Fuentes (2):**
  - Trelopades [`22828`] — Nv. 70 — ⚠ **Ubicación no resuelta**
  - Magtheridon [`17257`] — Nv. 73 — **Magtheridon's Lair**

</details>

## Notas técnicas

- La consulta de referencia resuelve primero spawns directos y, cuando no existen, busca el NPC como `difficulty_entry_1`, `difficulty_entry_2` o `difficulty_entry_3` de otro `creature_template`.
- Las zonas de mundo se obtienen cruzando las coordenadas del spawn con los límites de `WorldMapArea.dbc`; para instancias se utiliza el nombre de `Map.dbc` como fallback.
- Las fuentes marcadas como no resueltas no se han eliminado del loot. Su ausencia de coordenadas SQL no implica por sí sola que sean inaccesibles.
- Los templates `[PH]`, criaturas invocadas y NPC ligados a scripts/eventos deben tratarse como fuentes secundarias; la colección no debe depender exclusivamente de ellos.
