# Plantilla de contrato geográfico Turtle →335

Copiar/adaptar solo cuando otra región justifique su documento de feature bajo
`docs/turtle-wow/`, enlazado desde los índices existentes. No rellenar casillas
por suposición ni guardar progreso, estado Git, secretos o transcripciones.
Procedimiento owner: [guía de migración](../../../../docs/turtle-wow/migration-guide.md).

## Objetivo y alcance

- Región de origen, mapa/directorio y áreas; independiente o continente compartido.
- Contenido geográfico incluido y exclusiones (quests, NPC, loot, razas, sistemas).
- Criterio de preservación WotLK y del contenido propio ya aceptado.

## Fuentes y reconstrucción

- Builds/locales y fuente de cada contrato; dónde se fijan archivos/hashes.
- Resolución root/locale/custom y loose files; distinción snapshot/cliente jugado.
- Configuraciones, herramientas y dependencias versionadas o fijadas.
- Tres cadenas separadas: desde snapshots, rebuild de archivo cliente, build e
  instalación servidor. Inputs manuales/no regenerables que deben preservarse.
- Qué pasos siguen siendo específicos de esta región, no un bootstrap universal.

## Selección geográfica y conflictos

- Perímetro de tiles/MCNK, halo, vecinos y motivo de la selección.
- Costuras/agua/agujeros y contenido nativo que se conserva o adapta.
- Ownership de objetos; auditoría UID global y remaps con guards.
- Comparaciones semánticas que permiten omitir salidas nativas equivalentes.

## Identificadores y metadata

- Map/Area/WorldMapArea/Overlay/LoadingScreen/Trigger u otros namespaces usados.
- ExploreFlags, claves root/nameSet/group y remaps fuente→destino.
- Baselines cliente por locale y servidor independientes; overlays SQL revisados.
- Documento registro de IDs enlazado; no reservar por `max+1` sin auditoría.

## Conversión y dependencias

- Contratos ADT/WDT/MCNK, alpha, framing y líquidos MCLQ/MH2O.
- Política por WMO/M2: reutilización, aislamiento, conversión o adaptación.
- Familias/grupos, materiales, texturas, SKIN/animación/partículas y cierre.
- Adaptaciones acotadas por identidad/hash; controles negativos que evitan
  retirar agua/efectos/geometría legítimos y límites de soporte.

## Cartografía, idioma y acceso

- WorldMapArea, artwork/overlays, marcador del jugador y locale/fallback.
- TRS, nombres físicos, prefijos WMO, grupos/grid/escala/pisos e interiores sin arte.
- Máscara continental `.zmp`, highlights, celdas fronterizas y preservación nativa.
- WDL/Light/ambiente/loading y portales: importado, reutilizado o excluido, con motivo.
- Simplificaciones artísticas declaradas; no afirmar fidelidad total por presencia.

## Entrega y servidor

- Propiedad por parche root/locale, perfiles incluidos y excluidos; source locks.
- Captura/migración de fuentes y preservación de baselines/resultados previos.
- Maps, árbol/tiles VMap coordinados, cierre de modelos y MMaps/halo/parámetros.
- Contrato del manifiesto, preimágenes aceptadas y dependencias del generador.
- Instalación/reaplicación/rollback/recovery mediante el flujo existente; cliente
  manual, estado nuevo por manifiesto nuevo y separación SQL/archivos.
- Puntos de entrada para verificar/reconstruir, sin depender de nombres de scratch
  antiguos como si fueran fuentes durables ni mezclar recortes de extracción con entrega.

## Validación y límites

- Enlaces a tests, fixtures/oráculos independientes y evidencia ejecutada.
- Alcance de consultas nativas y de cliente real: qué posiciones/pisos/agua/clics
  se comprobaron y qué no; controles de regresión y artefactos finales probados.
- Aceptación del usuario solo si existe, sin convertir una confirmación puntual
  en cobertura completa. Estado de comprobaciones en el documento de validación.
- Riesgos durables y trigger para abordarlos; no tareas temporales ni diarios.
