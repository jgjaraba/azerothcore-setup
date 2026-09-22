# Forsaken Paladin class quests — authoritative Phase 2.1 design

Status: implemented; human in-game QA accepted. This remains the sole
authoritative design for this task. Client patch-Z packaging/deployment remains
a separate human release responsibility.

## Design contract

- Both chains are Undead Paladin-only (`AllowableRaces=16`, `AllowableClasses=2`)
  normal Paladin-class quests (`QuestSortID=-141`), with no repeatability,
  reputation, honor, title, talent, mail, currency, or time limit.
- The level-12 Redemption chain is `91010`–`91016`; the independent level-20
  weapon chain is `91020`–`91024`. Reserved IDs are all used because each step
  changes location, objective, or consequence; none is filler.
- The Ashen Hand is only a quiet informal name for a few Forsaken practitioners,
  never an organization, rank, faction, or hidden history.
- No Ambermill, Ivar Patch, Springvale, custom fallen target, resurrection
  encounter, event/controller, SmartAI, Melrache/bodyguard/quest-372 change,
  Individual Progression change, Playerbots change, module, or core change.
- Custom items are project-owned, modest materials recovered from existing
  sources. Their significance comes from Lordaeron's surviving places, not from
  invented relic lore.

## Item allocation and deployment

| ID | Item enUS | Item esES | Role |
|---:|---|---|---|
| 92060 | Ravenclaw Counterweight | Contrapeso Corvozarpa | Fenris component |
| 92061 | Agamand Weapon Haft | Mango de arma Agamand | Agamand component |
| 92062 | Durnholde Forged Iron | Hierro forjado de Durnholde | Durnholde component |
| 92063 | Rot Hide Binding | Atadura Putrepellejo | Rot Hide component |
| 92064 | Lordaeron's Vigil | Vigilia de Lordaeron | final weapon |

`92060`–`92063` are normal-quality, non-equippable, non-sellable, stack-one
quest items cloned from `7309`, retaining its existing icon/display. `92064` is
a bind-on-pickup, rare two-handed mace cloned field-for-field for gameplay from
Verigan's Fist `6953`: damage 65–99, speed 3.20, +7 Stamina, +12 Spirit, +6
Intellect, and no new effect. It uses provisional existing DisplayID `13466`.
The display is a human visual choice, not a readiness blocker.

| DBC | Records | Server | Regular patch-Z | HD patch-Z | Reason |
|---|---|---|---|---|---|
| Item.dbc | 92060–92063 cloned from 7309; 92064 from 6953 | required | required | required | client/server item identity and display contract |
| Other DBCs | none | n/a | n/a | n/a | existing NPCs, objects, spells, and display are reused |

Phase 2.1 must add matching `item_template`/`item_template_locale` rows and
generate the five Item.dbc records for the server. The human manually packages
the same records into both client patch-Z archives. This packaging is expected,
not a blocker.

## Technical and group-loot contract

Each component is a project-owned additive loot row: `Chance=100`,
`QuestRequired=1`, `LootMode=1`, `GroupId=0`, `MinCount=MaxCount=1`. Canonical
rows are never deleted or changed. Each row has exactly one AND-grouped active
quest condition (`ElseGroup=0`, `ConditionTypeOrReference=9`, all unused values
zero): `(SourceType, SourceGroup, SourceEntry, quest)` is `(4, 4767, 92061,
91021)` for the rack; `(1, 1939, 92063, 91021)`, `(1, 1940, 92063, 91021)`,
`(1, 1942, 92063, 91021)`, and `(1, 1943, 92063, 91021)` for Rot Hides;
`(1, 1947, 92060, 91022)` for Thule; and `(1, 2261, 92062, 91023)` for the
Watchman. Phase 2.1 also adds `gameobject_questitem (105172, 92061)` and
`creature_questitem` registrations `(1939, 92063)`, `(1940, 92063)`, `(1942,
92063)`, `(1943, 92063)`, `(1947, 92060)`, and `(2261, 92062)`.

Core evaluates creature quest loot per eligible nearby group member; the
quest-loot-party hook makes normal-quality quest loot free-for-all. The Agamand
Weapon Rack has personal loot (`groupLootRules=0`), so each eligible player must
interact with it separately and wait for its ordinary respawn if necessary; one
opening does not award every group member. Playerbots may accompany humans as
ordinary group members; no bot AI or autonomous bot completion is required.
Human-plus-bot loot, including this rack behavior, is a Phase 2.1 live-validation
case.

| Component | Active quest | Source | Future loot ownership | IP reachability |
|---|---:|---|---|---|
| 92061 | 91021 | Agamand Weapon Rack `105172`, spawn `45165`, loot `4767` | additive personal GO loot; serial player interaction | SAFE |
| 92063 | 91021 | Rot Hides `1939`, `1940`, `1942`, `1943` | additive creature loot + active-quest condition | SAFE |
| 92060 | 91022 | Thule Ravenclaw `1947` | additive creature loot + active-quest condition | SAFE |
| 92062 | 91023 | Syndicate Watchman `2261` | additive creature loot + active-quest condition | SAFE |

SAFE means current DEV contains ordinary phase-1 spawns and tracked IP zone data
has no target-specific phasing rule. Phase 2.1 must still live-test the selected
ordinary IP state. If an effective source loot ID drifts, implementation stops
for review rather than silently changing a creature template.

## Redemption chain

All quests have `QuestLevel=-1`, `MinLevel=12`, no money or item reward, and
their direct predecessor as `PrevQuestID`. `91010` has no predecessor. The
ordinary XP difficulties are 4, 5, 4, 4, 5, 4, and 6 respectively. Every quest
uses ordinary quest relations and talk, delivery, or shared kill credit.

### 91010 — A Handful of Ash / Un puñado de ceniza

**Giver → receiver:** Pancratius Ward `90211`, Deathknell → Abraham West
`90210`, Brill. **Follow-up:** 91011. **Objective:** speak with Abraham.
**Items/reward/spell:** none. **World purpose:** Deathknell and Brill become a
practical route from instruction to service.

**enUS — Details:** You have learned to call upon the Light. That is not the
same as knowing why.

Abraham West keeps the old discipline in Brill. There are few who endure it, and
fewer who speak openly. Some call them the Ashen Hand, but do not mistake a
whispered name for an order.

Speak with Abraham. He will tell you what is required.

**Objectives:** Speak with Abraham West in Brill.

**Progress:** Pancratius sent you? Then he believes you are ready to be useful.

**Completion:** We have no church and no banner, $N. We are merely a handful of
the dead attempting an old discipline.

If you intend to remain, you will serve before you judge.

**esES — Descripción:** Has aprendido a invocar la Luz. Eso no significa que
sepas para qué.

Abraham West conserva la antigua disciplina en Rémol. Pocos soportan su peso, y
menos aún hablan de ella abiertamente. Algunos los llaman la Mano Cinérea, pero
no confundas un nombre susurrado con una orden.

Habla con Abraham. Él te dirá qué se espera de ti.

**Objetivos:** Habla con Abraham West en Rémol.

**Progreso:** ¿Te envía Pancratius? Entonces cree que ya puedes resultar útil.

**Finalización:** No tenemos iglesia ni estandarte, $N. Solo somos un puñado de
muertos que intenta seguir una antigua disciplina.

Si pretendes quedarte, servirás antes de juzgar.

### 91011 — A Kindness Without Witness / Bondad sin testigos

**Giver → receiver:** Abraham West → Caretaker Caice `2307`, Deathknell.
**Prerequisite/follow-up:** 91010 / 91012. **Objective:** deliver Linen Cloth
`2589` ×10, consumed on turn-in. **Reward/spell:** none. **World purpose:** the
newly risen and their care become the first real obligation, not a lecture.

**enUS — Details:** Caretaker Caice tends those who rise in Deathknell. Some
wake torn, some bewildered, and some do not wake at all.

Bring him ten pieces of linen for bindings and shrouds. A kindness does not
become righteous merely because someone witnesses it.

**Objectives:** Bring 10 Linen Cloth to Caretaker Caice in Deathknell.

**Progress:** The newly risen are not patient with old wrappings. Have you
brought the linen?

**Completion:** Good. This will serve for bandages and for shrouds.

The Light will not fold them for us.

**esES — Descripción:** El custodio Caice atiende a quienes se alzan en
Camposanto. Algunos despiertan maltrechos, otros confusos, y otros no llegan a
despertar.

Llévale diez paños de lino para vendajes y mortajas. Una bondad no se vuelve
justa porque alguien la presencie.

**Objetivos:** Lleva 10 paños de lino al custodio Caice en Camposanto.

**Progreso:** Los recién alzados no tratan con cuidado sus viejas vendas. ¿Has
traído el lino?

**Finalización:** Bien. Servirá para vendajes y para mortajas.

La Luz no va a doblarlos por nosotros.

### 91012 — What the Dead Still Need / Lo que aún necesitan los muertos

**Giver → receiver:** Caretaker Caice → Abraham West. **Prerequisite/follow-up:**
91011 / 91013. **Objective:** return to Abraham. **Items/reward/spell:** none.
**World purpose:** the return lets Caice's work, rather than an abstract lesson,
change Abraham's next instruction.

**enUS — Details:** Tell Abraham the work is done.

The dead still require hands, patience and someone willing to remain after
curiosity has passed.

**Objectives:** Return to Abraham West in Brill.

**Progress:** Did Caice find a use for you?

**Completion:** Compassion that depends upon gratitude is only trade.

You served people who could offer you nothing. Remember that.

**esES — Descripción:** Dile a Abraham que el trabajo está hecho.

Los muertos aún necesitan manos, paciencia y a alguien dispuesto a quedarse
cuando haya pasado la curiosidad.

**Objetivos:** Vuelve con Abraham West en Rémol.

**Progreso:** ¿Te encontró Caice alguna utilidad?

**Finalización:** La compasión que exige gratitud no es más que un trueque.

Has servido a quienes nada podían ofrecerte. Recuérdalo.

### 91013 — The Measure of Mercy / La medida de la compasión

**Giver → receiver:** Abraham West → Magistrate Sevren `1499`, Brill.
**Prerequisite/follow-up:** 91012 / 91014. **Objective:** speak with Sevren.
**Items/reward/spell:** none. **World purpose:** Brill's magistrate frames mercy
as civil protection rather than passivity.

**enUS — Details:** Mercy is not softness, $N, nor is it permission for murder.

Magistrate Sevren has work fit for someone learning the difference. Hear him
out, then act without relish.

**Objectives:** Speak with Magistrate Sevren in Brill.

**Progress:** Abraham sent you? Good. I require a steady hand, not a sermon.

**Completion:** Scarlet Warriors have been probing the road east of Brill. Their
zeal will not spare our people.

Thin their patrols before they grow bold enough to strike the town.

**esES — Descripción:** La compasión no es debilidad, $N, ni permiso para
asesinar.

El magistrado Sevren tiene una tarea adecuada para quien está aprendiendo la
diferencia. Escúchalo y actúa sin deleitarte en ello.

**Objetivos:** Habla con el magistrado Sevren en Rémol.

**Progreso:** ¿Te envía Abraham? Bien. Necesito una mano firme, no un sermón.

**Finalización:** Los Guerreros Escarlata están tanteando el camino al este de
Rémol. Su fanatismo no tendrá piedad de los nuestros.

Reduce sus patrullas antes de que se atrevan a atacar el pueblo.

### 91014 — The Light Without Pity / La Luz sin piedad

**Giver/receiver:** Magistrate Sevren. **Prerequisite/follow-up:** 91013 / 91015.
**Location/objective:** east of Brill; kill Scarlet Warrior `1535` ×8.
**Items/reward/spell:** none; standard shared kill credit. **World purpose:**
the existing Scarlet pressure on Brill makes restraint a concrete choice.

**enUS — Details:** The Scarlets offer no quarter to the Forsaken. Drive their
warriors back, but do not mistake necessity for virtue.

Kill eight Scarlet Warriors east of Brill, then report to me.

**Objectives:** Kill 8 Scarlet Warriors, then return to Magistrate Sevren in
Brill.

**Progress:** The Scarlets will mistake hesitation for weakness. Is the road
secure?

**Completion:** Eight fewer blades pointed at Brill. That is enough.

You did what was required and did not make a pageant of it. Abraham should hear
that.

**esES — Descripción:** Los Escarlata no conceden cuartel a los Renegados. Haz
retroceder a sus guerreros, pero no confundas la necesidad con la virtud.

Mata a ocho Guerreros Escarlata al este de Rémol y vuelve conmigo.

**Objetivos:** Mata a 8 Guerreros Escarlata y vuelve con el magistrado Sevren en
Rémol.

**Progreso:** Los Escarlata confundirán cualquier vacilación con debilidad. ¿Está
seguro el camino?

**Finalización:** Ocho hojas menos apuntan ahora hacia Rémol. Basta.

Hiciste lo necesario sin convertirlo en un espectáculo. Abraham debe saberlo.

### 91015 — A Report in Ash / Un informe en ceniza

**Giver → receiver:** Magistrate Sevren → Abraham West. **Prerequisite/follow-up:**
91014 / 91016. **Objective:** report to Abraham. **Items/reward/spell:** none.
**World purpose:** public security has an observable consequence before the
personal instruction concludes.

**enUS — Details:** Tell Abraham the patrol has been broken and the road is
secure.

He asked whether you could distinguish mercy from surrender. I believe he has
his answer.

**Objectives:** Report to Abraham West in Brill.

**Progress:** Sevren does not send praise lightly. What happened?

**Completion:** You tended the helpless and defended those still standing.
Neither deed made you pure, and neither required purity before it could be done.

There is one duty left to discuss.

**esES — Descripción:** Dile a Abraham que la patrulla ha sido deshecha y que el
camino está seguro.

Quería saber si sabrías distinguir la compasión de la rendición. Creo que ya
tiene su respuesta.

**Objetivos:** Informa a Abraham West en Rémol.

**Progreso:** Sevren no concede elogios con facilidad. ¿Qué ocurrió?

**Finalización:** Atendiste a los indefensos y defendiste a quienes aún seguían
en pie. Ningún acto te hizo puro, ni exigía pureza para llevarlo a cabo.

Queda un deber del que debemos hablar.

### 91016 — The Light Does Not Spare Us / La Luz no nos da tregua

**Giver/receiver:** Abraham West. **Prerequisite/follow-up:** 91015 / none.
**Objective:** complete instruction with Abraham. **Items:** none. **Reward:**
exact `1788` semantics: `RewardXPDifficulty=6`, `RewardDisplaySpell=7328`,
`RewardSpell=7329`, no money, items, choices, reputation, honor, mail, or other
reward. **Mechanism:** immediate same-NPC completion. **World purpose:** the
reward teaches Resurrection after care and defence, without inventing a target.

**enUS — Details:** The Light does not become gentle because it passes through
dead flesh. It burns, and still it answers.

A paladin’s duty is not merely to endure that pain. It is to call a fallen
companion back to service when battle takes them.

Attend, and I will show you how.

**Objectives:** Complete your instruction with Abraham West.

**Progress:** Stand ready. This lesson will not be comfortable.

**Completion:** The Light did not spare you, nor did it refuse you.

You now bear the power to return a fallen companion to life. Use it as a duty,
never as proof that we have mastered what passes through us.

**esES — Descripción:** La Luz no se vuelve amable por atravesar carne muerta.
Quema y, aun así, responde.

El deber de un paladín no consiste solo en soportar ese dolor. Debe llamar de
nuevo al servicio a un compañero caído cuando la batalla se lo arrebata.

Presta atención y te enseñaré cómo hacerlo.

**Objetivos:** Completa tu instrucción con Abraham West.

**Progreso:** Prepárate. Esta lección no será agradable.

**Finalización:** La Luz no te ha dado tregua, pero tampoco te ha rechazado.

Ahora posees el poder de devolver la vida a un compañero caído. Empléalo como un
deber, nunca como prueba de que dominamos aquello que nos atraviesa.

## Level-20 weapon chain

All quests have `QuestLevel=20`, `MinLevel=20`, ordinary quest relations, and
no money or spell reward. `91020` has no prerequisite; it must not require
`91016`. XP difficulties are 4, 5, 5, 5, and 6.

### 91020 — A Weapon of This Soil / Un arma de esta tierra

**Giver → receiver:** Abraham West, Brill → Basil Frye `4605`, War Quarter,
Undercity. **Follow-up:** 91021. **Objective:** speak with Basil.
**Items/reward:** none. **World purpose:** the ordinary Undercity forge begins a
journey to make rather than inherit a weapon.

**enUS — Details:** At your level, a borrowed weapon and a bought weapon teach
the same lesson: very little.

Basil Frye works a forge in the War Quarter. He is no celebrated master, which
may make him suitable. Ask whether he can fashion something from what Lordaeron
has left us.

**Objectives:** Speak with Basil Frye in the War Quarter of Undercity.

**Progress:** You want a weapon made here? That depends upon what you are
willing to bring me.

**Completion:** I can shape the metal, but I will not pretend the forge creates
substance from nothing.

We will begin with a sound haft and something fit to bind it.

**esES — Descripción:** A tu nivel, un arma prestada y otra comprada enseñan lo
mismo: muy poco.

Basil Frye trabaja en una forja del Barrio de la Guerra. No es un maestro
célebre, lo cual quizá lo haga adecuado. Pregúntale si puede fabricar algo con
lo que aún queda de Lordaeron.

**Objetivos:** Habla con Basil Frye en el Barrio de la Guerra de Entrañas.

**Progreso:** ¿Quieres un arma forjada aquí? Dependerá de lo que estés
$gdispuesto:dispuesta; a traerme.

**Finalización:** Puedo dar forma al metal, pero no fingiré que la forja crea
materia de la nada.

Empezaremos con un mango firme y algo adecuado para sujetarlo.

### 91021 — Wood and Sinew / Madera y tendón

**Giver/receiver:** Basil Frye. **Prerequisite/follow-up:** 91020 / 91022.
**Route/objectives:** Agamand Mills, obtain 92061 ×1 from Weapon Rack `105172`;
then Silverpine, obtain 92063 ×1 from Rot Hides 1939/1940/1942/1943. Both are
consumed at turn-in. **Reward/spell:** none. **World purpose:** an old estate's
useful wood and the region's everyday decay provide the weapon's structure.

**enUS — Details:** The Agamands kept racks for their weapons. Search the old
mill and take a haft that has not split with age.

For the binding, use no fresh leather. The Rot Hides cure their straps with
filth and grave-mould; unpleasant, but strong. Bring me one usable length.

**Objectives:** Bring an Agamand Weapon Haft and a Rot Hide Binding to Basil
Frye in Undercity.

**Progress:** A warped haft will ruin the balance, and rotten binding will part
on the first swing. Choose carefully.

**Completion:** The wood is old but straight, and this binding has survived
worse treatment than you will give it.

They are ugly materials. They will serve.

**esES — Descripción:** Los Agamand guardaban sus armas en expositores. Busca en
el viejo molino y toma un mango que no se haya agrietado con los años.

Para la atadura no emplearemos cuero nuevo. Los Putrepellejo curten sus correas
con inmundicia y moho de tumba; es desagradable, pero resistente. Tráeme un
trozo aprovechable.

**Objetivos:** Lleva un Mango de arma Agamand y una Atadura Putrepellejo a Basil
Frye en Entrañas.

**Progreso:** Un mango torcido arruinará el equilibrio, y una atadura podrida
cederá al primer golpe. Elige con cuidado.

**Finalización:** La madera es vieja, pero recta, y esta atadura ha soportado
peores tratos de los que tú le darás.

Son materiales feos. Servirán.

### 91022 — The Raven’s Weight / El peso del cuervo

**Giver/receiver:** Basil Frye. **Prerequisite/follow-up:** 91021 / 91023.
**Location/objective:** Fenris Isle; obtain Ravenclaw Counterweight `92060` ×1
from Thule Ravenclaw `1947`, then consume it at Basil. **Reward/spell:** none.
**World purpose:** Fenris becomes a dangerous place where useful material is
reclaimed from a necromancer, not a stage for a new legend.

**enUS — Details:** The head will need a counterweight. Thule Ravenclaw carries
a worked piece of iron heavy enough for the task.

He has made Fenris Isle a grave for others. Do not go there seeking a grand
victory. Take the iron, return alive and let the dead keep no more than they
already possess.

**Objectives:** Take the Ravenclaw Counterweight from Thule Ravenclaw on Fenris
Isle and bring it to Basil Frye.

**Progress:** Thule still has the iron, or you would have placed it on my bench.

**Completion:** Dense, well shaped and marked by no craft worth honoring.

Once it is in the weapon, it will serve a better purpose than its former bearer

**esES — Descripción:** La cabeza necesitará un contrapeso. Thule Corvozarpa
lleva una pieza de hierro trabajado con el peso adecuado.

Ha convertido la Isla de Fenris en la tumba de otros. No vayas allí en busca de
una gran victoria. Toma el hierro, regresa con vida y no permitas que los muertos
conserven más de lo que ya poseen.

**Objetivos:** Arrebata el Contrapeso Corvozarpa a Thule Corvozarpa en la Isla de
Fenris y llévaselo a Basil Frye.

**Progreso:** Thule aún conserva el hierro, o ya lo habrías dejado sobre mi
banco.

**Finalización:** Es denso, está bien formado y no lleva marca alguna de una
artesanía digna de honor.

Cuando forme parte del arma, servirá a un propósito mejor que su antiguo portador.

### 91023 — Iron in Captivity / Hierro cautivo

**Giver/receiver:** Basil Frye. **Prerequisite/follow-up:** 91022 / 91024.
**Location/objective:** Durnholde; obtain Durnholde Forged Iron `92062` ×1 from
Syndicate Watchman `2261`, then consume it at Basil. **Reward/spell:** none.
**World purpose:** Durnholde's ordinary stores outlast changing occupiers and
become useful again without changing canonical Durnholde content.

**enUS — Details:** For the striking face, I need iron that has already endured
a proper forge.

The Syndicate watchmen at Durnholde carry pieces cut and refitted from the
keep’s stores. Bring me one sound piece. We will remove their marks in the fire.

**Objectives:** Recover Durnholde Forged Iron from a Syndicate Watchman at
Durnholde and bring it to Basil Frye.

**Progress:** Any cracked or rust-eaten piece is useless to me. Have you found
sound iron?

**Completion:** This will take the hammer.

The keep changed hands, but its iron remained. Once reforged, it will owe
allegiance to no jailer or thief.

**esES — Descripción:** Para la cara de golpe necesito hierro que ya haya
resistido una forja adecuada.

Los Veladores de la Hermandad de Durnholde llevan piezas recortadas y adaptadas
de las reservas del castillo. Tráeme una que esté entera. Borraremos sus marcas
en el fuego.

**Objetivos:** Consigue Hierro forjado de Durnholde de un Velador de la
Hermandad en Durnholde y llévaselo a Basil Frye.

**Progreso:** Una pieza agrietada o comida por el óxido no me sirve. ¿Has
encontrado hierro en buen estado?

**Finalización:** Esto soportará el martillo.

El castillo cambió de manos, pero su hierro permaneció. Una vez reforjado, no
deberá lealtad a carcelero ni ladrón alguno.

### 91024 — Lordaeron’s Vigil / Vigilia de Lordaeron

**Giver/receiver:** Basil Frye. **Prerequisite/follow-up:** 91023 / none.
**Objective:** remain with Basil to complete the weapon. **Reward:** Lordaeron's
Vigil `92064` ×1 and ordinary XP difficulty 6; no money, spell, or alternative
item. **Mechanism:** immediate same-NPC completion, not an event. **World
purpose:** Basil's existing forge turns recovered practical materials into an
Undercity-made weapon.

**enUS — Details:** The pieces are ready. Stay while I fit them together.

This is forge work, not a rite. Hold the haft when I tell you, and do not pull
away when the hot iron meets the binding.

**Objectives:** Remain with Basil Frye while he finishes Lordaeron’s Vigil.

**Progress:** The forge is hot. We begin when you are ready.

**Completion:** There. No royal seal, no saint’s name and no promise that the
Light finds us worthy.

It was made from Lordaeron by hands that still serve Lordaeron. Keep watch.

**esES — Descripción:** Las piezas están listas. Quédate mientras las uno.

Esto es trabajo de forja, no un rito. Sujeta el mango cuando te lo indique y no
retrocedas cuando el hierro caliente toque la atadura.

**Objetivos:** Permanece con Basil Frye mientras termina la Vigilia de Lordaeron.

**Progreso:** La forja está caliente. Empezaremos cuando estés
$gpreparado:preparada;.

**Finalización:** Ya está. Sin sello real, sin nombre de santo y sin promesa de
que la Luz nos considere dignos.

Fue forjada con restos de Lordaeron por manos que aún sirven a Lordaeron. Mantén
la vigilia.

## Component provenance

| Item | Material and source | Why it belongs there and what it adds |
|---|---|---|
| 92061 | Straight spare weapon haft from Agamand Weapon Rack 105172 | A weapon rack naturally holds replaceable hafts. The ruined estate shows ordinary household arms surviving its owners; its sound wood makes the mace handle. |
| 92063 | Cured Rot Hide strap from ordinary Rot Hide gear | Gnoll straps are mundane equipment, made foul by the region rather than mystical. Silverpine's decay becomes a durable binding without being glorified. |
| 92060 | Worked iron counterweight carried by Thule Ravenclaw 1947 | A compact piece of equipment is plausible on Thule and adds balance to the mace head. Fenris shows the cost of death magic; the iron is recovered, not celebrated. |
| 92062 | Sound forged iron from Syndicate Watchman 2261 at Durnholde | Watchmen plausibly carry refitted keep iron. Durnholde shows an old institution reduced to occupation; the metal becomes the striking face after its marks are burned away. |

## Phase 2.1 implementation and validation boundaries

Use explicit-column, idempotent project SQL that owns only new quests, relations,
locales, item rows, custom loot rows, and their conditions. Verify every source
loot ID and every item/quest collision immediately before writing data. Validate
chain restrictions, predecessor/follow-up flow, 91016 reward parity, group kill
credit, per-player component loot, human-plus-Playerbot group behavior, source
reachability, 92064 field parity, both locales, Item.dbc parity, and rendering of
provisional display 13466.
