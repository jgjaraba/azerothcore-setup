USE `acore_world`;

-- Turtle WoW maps port: minimal instance metadata for custom instance maps.
-- No creatures, scripts or playable systems are added here; this only makes the
-- map enterable by the server (see docs/turtle-wow/).
--
-- KarazhanCrypt (map 800) is entered from Deadwind Pass (map 0).

START TRANSACTION;

-- Preserve identical existing metadata; a conflicting map PK fails closed.
-- A single INSERT means no earlier row changes can survive its failure.
INSERT INTO `instance_template` (`map`, `parent`, `script`, `allowMount`)
SELECT 800, 0, '', 0
WHERE NOT EXISTS (
    SELECT 1 FROM `instance_template`
    WHERE `map` = 800 AND `parent` = 0
      AND BINARY `script` = BINARY '' AND `allowMount` = 0
);

COMMIT;
