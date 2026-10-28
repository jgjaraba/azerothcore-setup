---
name: turtle-zone-import
description: "Importar o reparar zonas y mapas Turtle WoW en AzerothCore/WotLK 3.3.5a: terreno, agua, M2/WMO, DBC, minimapas, clic continental, MPQ y datos servidor; usar también ante Error132 o líquidos falsos de un port geográfico."
compatibility: "OpenCode en el proyecto privado azerothcore-setup, con snapshots Turtle/335 y AzerothCore DEV compatibles."
metadata:
  scope: "geographic-port"
  language: "es"
---

# Importar una zona Turtle a WotLK335

## Propósito y límites

Lleva una solicitud geográfica desde inspección hasta implementación validada.
Incluye terreno, dependencias visuales, líquidos, metadata, cartografía, cliente
y servidor. **No activa por sí sola razas nuevas ni importa NPC, quests, loot o
sistemas.** Si se piden, separa sus contratos; no los des por migrados.

Esta skill es un punto de entrada, **no otra fuente de verdad** ni un importador
universal. El procedimiento completo vive en la
[guía de migración](../../../docs/turtle-wow/migration-guide.md). Las políticas
y asignaciones de High Elf/cripta son ejemplos específicos, nunca defaults
automáticos de la próxima región.

## Lectura y reglas de arranque

1. Lee `AGENTS.md` del proyecto y
   [el índice de conocimiento](../../../docs/project/README.md).
2. Lee la guía y solo los documentos del índice relevantes a la petición. Antes
   de trabajo sustantivo en el core, lee sus AGENTS y los anidados aplicables.
3. Inspecciona estado real: ramas, cambios ajenos, inputs, herramientas, módulos,
   procesos y configuración efectiva cuando importe. No conviertas docs en
   inventario de deployment. No muestres credenciales.
4. No edites snapshots originales ni el cliente jugado. Conserva trabajo ajeno.
   **Nunca crees commits ni hagas push.** El cliente se instala manualmente;
   publicar el perfil local no es copiarlo al juego.
5. Resuelve ingeniería rutinaria con inspección/experimentos. No impongas gates
   de aprobación para operar DEV; pregunta solo por una decisión de producto
   realmente desconocida que bloquee el trabajo. Prefiere datos/configuración
   antes que módulo/core cuando sea correcto.

## 1. Delimita la operación y el contrato

Clasifica: port nuevo desde snapshots, rebuild desde archivo durable, actualización
de una región o diagnóstico de una regresión. No confundas esas cadenas.

- Identifica mapa/directorio/áreas, build, locales, snapshots y cliente efectivo.
- Resuelve archivos por prioridad real y sondeo directo; un listfile incompleto
  o T-last del extractor no demuestra qué carga el juego.
- Distingue mapa independiente, tiles nuevos y tiles comunes modificados.
- Audita IDs en DBC cliente/servidor, SQL overlays y código; incluye exploreFlags,
  claves WMO naturales y UID de placements de todo el mapa efectivo.
- Selecciona MCNK/halo explícitos si el continente es compartido. No uses el
  rectángulo WorldMapArea como permiso para sobrescribir tiles completos.

Usa la [plantilla de contrato](references/region-contract-template.md) para
registrar decisiones estables; evidencia de ejecución y planes temporales van
fuera del contrato. Delega investigación sustantiva a `ac-research`.

## 2. Implementa el delta geográfico

Sigue §§5–7 de la guía y [compatibilidad](../../../docs/turtle-wow/compatibility.md).

- Reconstruye tablas de nombres/indirectiones, placements y MCRF conservando
  identidades; ownership y remaps UID deben ser regionales/globales, no por tile.
- Valida framing y semántica del agua por separado. No limpies offsets MCLQ sin
  asegurar el recorrido físico cliente; conserva agua legítima y todas las capas
  MH2O de la celda elegida. No inventes un conversor MCLQ→MH2O inexistente.
- Cierra ADT→WMO/M2→grupos/materiales/texturas/skins/animaciones. Aísla path y
  basename donde corresponda. Existencia de un path o MVER17/18 no prueba fidelidad.
- Convierte M2 reales con soporte comprobado; no elimines partículas o efectos
  para declarar compatibilidad. Rechaza semánticas desconocidas.
- Comprueba líquidos WMO aun sin MLIQ. La adaptación de sentinel15 de High Elf
  está limitada por hashes a familias demostradas secas; no la apliques globalmente.
- Fusiona DBC sobre baselines independientes y conserva filas/strings ajenos.
  Verifica root/nameSet/group colocados, orden físico cuando proceda y propiedad
  root/locale para no ocultar traducciones ni contenido WotLK.

No cierres un bloqueo deshabilitando guards o cambiando expected hashes para
aceptar inputs desconocidos. Declara toda adaptación o pérdida de fidelidad.

## 3. Completa cartografía y acceso

Aplica §8 de la guía, no solo el empaquetado de imágenes.

- Mapas regionales, overlays, coordenadas del jugador y arte por idioma.
- TRS completo, nombres físicos compatibles con el buffer cliente, colisiones
  por contenido y conservación de mappings nativos/cripta fuera del delta.
- Lookup WMO real: prefijo, índice de grupo, grid y escala. No fabriques aliases
  entre interiores distintos; usa arte equivalente demostrado o planos de suelo
  reales, documentando simplificación y límites de pisos.
- Hover/clic continental: merge mínimo del `.zmp` con AreaTable IDs y controles
  vecinos; un highlight BLP no habilita por sí mismo el clic.
- Loading screen, puertas/portales/dificultad solo cuando sean parte del alcance;
  no importes FrameXML o continentes completos para sustituir datos faltantes.

## 4. Preserva, genera y despliega

Consulta §12 de la guía para interfaces y precondiciones; **adapta y prueba** los
wrappers que todavía codifican región, inventario o hashes High Elf/cripta.

1. Genera candidatos aislados, informes y deltas. Verifica inputs, formato y cierre.
2. Captura fuentes durables, baselines pre-región y resultados esperados. Conserva
   edición anterior; una captura activa no se sobrescribe ni se refreezea a ciegas.
3. Construye cliente dos veces y verifica readback/inventario/ownership. Publica
   solo el perfil compatible y documenta copia manual/rollback.
4. Usa un cliente de extracción coordinado, sin instalar DBC/WDT/Map recortados
   que solo servían al extractor. No trasplantes todas las DBC extraídas a DEV.
5. Ensambla VMap con el árbol completo y sus tiles/modelos coherentes; genera
   MMaps regionales y halo. Comprueba outputs reales, parámetros y dependencias.
6. Conserva datos mediante el manifiesto/instalador existente de
   [deployment.md](../../../docs/turtle-wow/deployment.md), con preimágenes
   reconocidas y rollback. Un manifiesto nuevo necesita estado nuevo.
7. Si hay cambio servidor, instala con parada/acceso exclusivo, reaplica y revisa
   arranque/logs. Si la reextracción es idéntica, demuestra el no-op en vez de
   reinstalar por suposición. SQL y archivos no son una sola transacción.

## 5. Valida, revisa y cierra

- Tests estáticos/sintéticos y fixtures reales, negativos y determinismo.
- Scanner nativo con EXE hash-compatible cuando aplique; extracción publicada,
  no solo staging. Ni el parser ni el generador son pruebas del renderizador.
- Lectores nativos de terreno/VMap/Detour: carga, altura, LoS y corredores con
  estados completos/parciales/ausentes separados.
- Cliente real aislado: carga, movimiento, suelo/aire, interior/exterior,
  agua legítima, minimapa/punto, hover/clic real y controles nativos pertinentes.
  Para regresiones, A/B en los puntos/alturas reales y control del comportamiento
  que el fix podría borrar. No ejecutes cleanup de un harness viejo sobre trabajo ajeno.
- Usa `ac-review` para revisión independiente, inspecciona tú también el diff,
  corrige hallazgos materiales y revalida.
- Actualiza el documento que posee cada contrato; evidencia y aceptación acotadas
  en [validation.md](../../../docs/turtle-wow/validation.md), sin diario de tarea.
- Reporta **PASS / FAIL / NOT RUN / NOT APPLICABLE / BLOCKED**, archivos/repos
  cambiados, instalación requerida, límites y estado DEV. No atribuyas ejecución
  ni aceptación del usuario que no haya ocurrido.

Para síntomas conocidos, usa §13 de la guía; para el cierre, §14. Un PASS de un
tile, una casa o una ruta no certifica todos los pisos, HD, addons ni gameplay.
