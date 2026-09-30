# SUPERSEDED — NOT AUTHORITATIVE

The authoritative final design is
`forsaken-paladin-class-quests.DESIGN.md`. This historical Phase 2.0b proposal
is retained only for traceability and must not be used for implementation.

## Binding structure

- Quest IDs (DEV-observed free in `quest_template`): Redemption `91010`–`91016`;
  weapon `91020`–`91024`. Those values are occupied items and must not be used
  for new items.
- `91020` has no Redemption predecessor. No controller, custom creature, GO,
  SmartAI, spell change, IP change, Playerbots change, quest-372 change, timed
  event, or Springvale component is proposed.
- Weapon: **Lordaeron's Vigil / Vigilia de Lordaeron**. Clone every
  gameplay-relevant field from Verigan's Fist `6953`; use an existing display
  only. Human selection remains open: `5226`, `8690`, `22133`, `8588`, `8585`,
  `5228`, or `13466`.

## Chains

| ID | enUS / esES | Giver → receiver | Objective |
|---:|---|---|---|
| 91010 | A Handful of Ash / Un puñado de ceniza | 90211 → 90210 | Speak. |
| 91011 | A Kindness Without Witness / Bondad sin testigos | 90210 → 2307 | 10 Linen Cloth 2589. |
| 91012 | What the Dead Still Need / Lo que aún necesitan los muertos | 2307 → 90210 | Return. |
| 91013 | The Measure of Mercy / La medida de la compasión | 90210 → 1499 | Speak. |
| 91014 | The Light Without Pity / La Luz sin piedad | 1499 → 1499 | Kill 8 Scarlet Warriors 1535. |
| 91015 | A Report in Ash / Un informe en ceniza | 1499 → 90210 | Return. |
| 91016 | The Light Does Not Spare Us / La Luz no nos da tregua | 90210 → 90210 | Conclude; clone quest 1788 reward semantics. |
| 91020 | The Watch at Ivar Patch / La guardia de los Dominios de Ivar | 90210 → 1951 | Speak. |
| 91021 | One Farm, Still Standing / Una granja aún en pie | 1951 → 1951 | Kill Ivar the Foul 1971. |
| 91022 | A Weapon of This Soil / Un arma de esta tierra | 1951 → 4605 | Speak. |
| 91023 | Remnants of Lordaeron / Vestigios de Lordaeron | 4605 → 4605 | Four components below. |
| 91024 | Lordaeron’s Vigil / Vigilia de Lordaeron | 4605 → 4605 | Turn in; one weapon reward. |

The early story teaches service and protection, then awards Resurrection without
claiming an unverified resurrection encounter. The weapon journey makes existing
ordinary Lordaeron objects meaningful: Ivar Patch, Agamand, Ambermill,
Durnholde, and Silverpine Rot Hides, with final forging at Basil's normal forge.

## Exact conditional component sources

- Agamand Weapon Haft: GO `105172`, spawn `45165`; additive quest loot only.
- Ambermill Refined Ingot: GO `103815`, spawn `35412`; additive quest loot only.
- Durnholde Smithing Hammer: Syndicate Watchman `2261`; additive creature loot.
- Rot Hide Binding: `1939`, `1940`, `1942`, `1943`; additive creature loot.

Do not consume canonical items `7569`/`7309`, modify their canonical quests, or
alter quest 372/Melrache `1665`/Bodyguard `1660`. All sources still require DEV
effective-spawn, loot, and legitimate-IP-state checks.

## Text direction

All retained text is concise Vanilla-style. Ashen Hand is an informal custom
label, never a recognized order. The level-12 text says: serve before judging;
care for newly risen Forsaken; mercy is neither softness nor permission for
murder; the Light hurts but gives a duty to raise fallen companions. The level-20
text says: Ivar Patch is one field worth keeping; kill Ivar without ceremony;
build from ordinary things surviving Lordaeron; no royal seal or saint's name is
needed. Full enUS/esES field text is the Stage 2 architecture report and must be
copied verbatim into the final implementation design before SQL authoring.

## Readiness gates

- **Resolved:** quest IDs; no hard chain gate; no unsafe events/actors; no quest
  372 interaction; no ember; exact base component candidates; DB-only additive
  shape; canonical 1788 and 6953 parity targets.
- **Still open:** `92020`–`92024` candidate item collisions; effective IP state
  availability for every actor/GO; display human choice/client validation;
  group-loot/credit runtime validation; exact full field copy and locale loading.
