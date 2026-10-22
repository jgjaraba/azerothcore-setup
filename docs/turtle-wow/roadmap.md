# Hoja de ruta hacia todo el contenido custom de Turtle

## Objetivo y límites

El destino es un servidor **WotLK335 ampliado**, no reemplazado por Vanilla.
El objetivo global incluye geografía y, progresivamente, el contenido jugable
custom de Turtle. Esta es una hoja de ruta, no un inventario exhaustivo ni una
afirmación de que cada sistema1.12 se pueda copiar directamente a335.

Las funcionalidades nativas y propias, así como los módulos instalados, tienen
prioridad frente a sustituciones silenciosas. Los conflictos de diseño reales
se deciden explícitamente; los problemas técnicos normales se investigan.
No acceder a producción ni publicar automáticamente recursos de terceros.

## Situación de partida

- Karazhan Crypt: **piloto geográfico práctico aceptado** por el usuario,
  con presentación, acceso y pruebas básicas. Excepciones de fidelidad y
  navegación siguen explícitas; no hace falta reabrir ese cierre para avanzar.
- El inventario geográfico es **preliminar**. Hay57 Map records y175 paths
  continentales source-only analizados; faltan modificaciones comunes y
  cierres de dependencias/perímetros. Eso no es toda la geografía custom.
- Hay herramientas y construcciones incrementales probadas, pero no un
  bootstrap genérico desde cero. El agua ADT no tiene aún un conversor validado;
  hay un defecto MHDR conocido que debe corregirse antes de mapas húmedos.
- Un cliente no aporta la BD completa de spawns, quests, loot o scripts del
  servidor. Para el contenido jugable harán falta fuentes servidor autorizadas,
  compatibles y de procedencia/versionado comprobables, o reconstrucción
  validada cuando sea viable. El SQL público Tortoise es orientación, no prueba
  de equivalencia con la versión actual del servidor oficial.

## Próximo hito recomendado: Tel'Abim, viabilidad de un delta continental húmedo

**Por qué ahora:** amplía lo aprendido sin duplicar solo otra mazmorra. Obliga
a probar incorporación sobre Kalimdor, agua y recursos específicos, que son
requisitos para casi todas las siguientes regiones.

Evidencia acotada:14 ADT locales con áreas5121–5129 y MCLQ, inicialmente
source-only bajo la comparación disponible. Las referencias directas incluyen
una familia no resuelta en el índice335: `utari_house_03.wmo`, presente como
root/grupo en listings Turtle patch3. El resto de existencias por path **no**
certifica fidelidad. No se ha cerrado el perímetro completo ni el halo costero.

Orden del trabajo:

1. Corregir y probar parser/serializador MHDR con fixtures reales335/Vanilla,
   sin alterar los artefactos del piloto aceptado.
2. Delimitar isla+halo y construir un manifiesto efectivo de nuevos/comunes/
   modificados; comparar WDT y costuras con Kalimdor335. No copiar el continente.
3. Investigar/probar el tratamiento de agua: tipo, alturas, cobertura, alfa y
   render/extracción. No asumir que soporteMCLQ del extractor certifica el cliente.
4. Auditar la familia WMO faltante y dependencias transitivas. Reutilizar solo
   cuando la geometría/colisión lo justifique; aislar cambios por namespace.
5. Construir un candidato geográfico regenerable con inputs declarados,
   IDs/referencias y cartografía aditivas, sin NPC/quests/loot todavía.
6. Extraer datos y validar costa, agua, alturas, colisiones, navegación y una
   pequeña regresión del continente. Aceptación en juego con alcance explícito.

**Salida del hito:** una segunda región y un procedimiento de merge húmedo
continental demostrado, o un informe preciso de qué categoría bloquea su
integración y qué subconjunto es seguro. No prometer importación completa
solo porque14 tiles ya estén extraídos.

## Fases posteriores

| Fase | Trabajo | Criterio para avanzar |
|---|---|---|
| 1. Infraestructura de importación | Bootstrap desde snapshots/hashes, registro de IDs, resolver de prioridad/locale, manifests de recursos y pruebas de preservación | Rebuild verificable sin depender de informes temporales perdidos; conflictos fallan explícitamente |
| 2. Mundo físico | Nuevos mapas, islas y deltas continentales; WMO/M2/agua/luz/cartografía y accesos | Inventario trazable, datos cliente/servidor coherentes, excepciones explícitas y regiones aceptadas |
| 3. Entorno estático servidor | GameObjects, transportes y puertas necesarios para el escenario | Spawns/destinos/colisiones sin importar prematuramente mecánicas de combate |
| 4. NPC y criaturas custom | Templates/spawns, modelos, facciones, movimiento, servicios y textos | Equivalencia semántica con335 y módulos; sin sobrescribir originales ni duplicar NPC existentes |
| 5. Misiones y progresión | Quests/cadenas, condiciones, objetos de misión, reputación y recompensas dependientes | Dependencias/IDs/locale completos, principio-fin jugable y economía/regresiones comprobadas |
| 6. Objetos y loot | Templates/DBC, costes, vendedores y tablas de loot; ligadas a las fases que las necesiten | No romper item/talento/hechizo propio; economía y referencias validadas |
| 7. Mazmorras/raids jugables | IA, jefes, puertas, resets, grupos y dificultad | Compatibilidad con progresión individual, bots y demás módulos; pruebas de cada encuentro |
| 8. Sistemas custom | Hechizos/talentos, profesiones, razas/clases, eventos y otras mecánicas | Decisión de diseño/compatibilidad por sistema, con adaptaciones mínimas mantenibles |

Las fases expresan dependencias, no bloques rígidos: una quest puede exigir su
objeto antes, y una puerta puede depender de un encuentro. Importar unidades
verticales pequeñas con sus dependencias y pruebas; no volcar todo un esquema
Vanilla en el esquema335 ni ejecutar una base pública sin auditoría.

## Organización por paquetes y aceptación

Para cada región o feature jugable registrar:

- Fuente/build/procedencia y contenido custom frente a contenido ya nativo335.
- Conjunto de archivos/filas, dependencias y correspondencias estables de IDs.
- Contrato de comportamiento e interacción con módulos/proyecto.
- Fidelidad: idéntico, adaptación verificada, aproximación declarada o pendiente.
- Estado separado de inventario, conversión, integración y validación real.
- Construcción, instalación y rollback del conjunto coordinado.
- Evidencia ejecutada y una lista de pruebas manuales concreta y razonable.

Un contenido invisible o una referencia SQL ausente no se completa con un
marcador de error, y una excepción no debe desaparecer del inventario. “TODO”
solo se podrá declarar migrado cuando la cobertura total esté inventariada y
cada elemento tenga implementación aceptada o una excepción expresamente
acordada. Actualmente ese criterio global **no se cumple**.

Reglas operativas y recetas vigentes: [guía de migración](migration-guide.md).
Estado por región: [inventario](maps-inventory.md). Evidencia del piloto:
[validación](validation.md).
