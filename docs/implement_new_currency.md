## Implement new currency

### 1. Create temporary table

```sql
DROP TEMPORARY TABLE IF EXISTS `tmp_currency_token`;
CREATE TEMPORARY TABLE `tmp_currency_token` LIKE `item_template`;
```

### 2. Copy currency base (for example Mark of Transmogrification, ID 90001 )

```sql
INSERT INTO `tmp_currency_token`
SELECT *
FROM `item_template`
WHERE `entry` = 90001;
```

### 3. Update currency values in temporary table

````sql
UPDATE `tmp_currency_token`
SET
    `entry`          = 90005, #CHECK UNUSED ID
    `class`          = 15,
    `subclass`       = 0,
    `name`           = 'Naxxramas Curio', #SET NAME
    `Quality`        = 4, #SET QUALITY 4 EPIC, 3 RARE, 2 UNCOMMON, 1 COMMON, 0 POOR
    `area`           = 0,
    `Map`            = 0,
    `Flags`          = 2048,
    `FlagsExtra`     = 0,
    `BuyCount`       = 1,
    `BuyPrice`       = 0,
    `BagFamily`      = 0,
    `SellPrice`      = 0,
    `InventoryType`  = 0,
    `displayid`      = 35350, #SET DISPLAYID
    `AllowableClass` = -1,
    `AllowableRace`  = -1,
    `ItemLevel`      = 1,
    `RequiredLevel`  = 1,
    `maxcount`       = 0,
    `stackable`      = 200,
    `bonding`        = 1,
    `description`    = 'A desecrated relic recovered from the necropolis. It remains deathly cold no matter how long it is held. A collector of rare artifacts might find value in it.', #SET DESCRIPTION
    `VerifiedBuild`  = 0;
````

### 4. Insert into final table and drop temporary one

```sql
INSERT INTO `item_template`
SELECT *
FROM `tmp_currency_token`;

DROP TEMPORARY TABLE `tmp_currency_token`;
```

### 5. (Optional) Add translations

````sql
DELETE FROM `item_template_locale`
WHERE `ID` = 90005
  AND `locale` = 'esES';

INSERT INTO `item_template_locale`
(
    `ID`,
    `locale`,
    `Name`,
    `Description`,
    `VerifiedBuild`
)
VALUES
(
    90005,
    'esES',
    'Curiosidad de Naxxramas',
    'UUna reliquia profanada recuperada de la necrópolis. Permanece gélida al tacto sin importar cuánto tiempo se sostenga. Un coleccionista de artefactos extraños podría encontrarle valor.',
    0
);
````