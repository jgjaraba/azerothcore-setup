USE `acore_world`;

-- VERDES x5
UPDATE `reference_loot_template`
SET `Chance` = LEAST(`Chance` * 5.0, 100)
WHERE `Reference` <> 0
  AND `Comment` REGEXP '^(Vanilla|TBC|WotLK) Greens ';

-- AZULES x5
UPDATE `reference_loot_template`
SET `Chance` = LEAST(`Chance` * 5.0, 100)
WHERE `Reference` <> 0
  AND `Comment` REGEXP '^(Vanilla|TBC|WotLK) Blues ';

-- ÉPICOS x5
UPDATE `reference_loot_template`
SET `Chance` = LEAST(`Chance` * 5.0, 100)
WHERE `Reference` <> 0
  AND `Comment` REGEXP '^(Vanilla|TBC|WotLK) Purples ';

-- COMPROBACIÓN
SELECT
    `Entry`,
    `Item`,
    `Reference`,
    `Chance`,
    `Comment`
FROM `reference_loot_template`
WHERE `Reference` <> 0
  AND `Chance` <> 0
  AND `Comment` REGEXP '^(Vanilla|TBC|WotLK) (Purples) '
ORDER BY `Entry`, `Item`;