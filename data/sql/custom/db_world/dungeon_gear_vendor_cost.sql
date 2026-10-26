-- Server ItemExtendedCost SQL overlay; no binary DBC replacement is required.
-- Exact numeric records from tracked dbc/ItemExtendedCost.dbc, SHA256:
-- 24bc323061283e6c4c94a411318496720230ec83fe7315c1798ba8c0e280c4be
-- Requires dungeon_gear_vendor.sql currencies and matching client DBC records.
-- Owns only 97010..97035, 98010..98035, 99010..99035 (prices 2, 5, 10).
-- Execute without --force. A failed CALL rolls back all row changes and leaves
-- the procedure as a fail-safe: inspect the error/state, then explicitly DROP
-- PROCEDURE `azerothcore_setup_dungeon_vendor_costs` before retrying.
USE `acore_world`;
DELIMITER $$
CREATE PROCEDURE `azerothcore_setup_dungeon_vendor_costs`()
BEGIN
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    DROP TEMPORARY TABLE IF EXISTS `dungeon_vendor_costs_expected`;
    RESIGNAL;
  END;

  IF NOT EXISTS (SELECT 1 FROM information_schema.TABLES
                 WHERE TABLE_SCHEMA = DATABASE()
                   AND TABLE_NAME = 'itemextendedcost_dbc' AND ENGINE = 'InnoDB') THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Dungeon vendor costs: itemextendedcost_dbc must be InnoDB';
  END IF;

  CREATE TEMPORARY TABLE `dungeon_vendor_costs_expected` (
    `ID` INT NOT NULL PRIMARY KEY,
    `HonorPoints` INT NOT NULL, `ArenaPoints` INT NOT NULL, `ArenaBracket` INT NOT NULL,
    `ItemID_1` INT NOT NULL, `ItemID_2` INT NOT NULL, `ItemID_3` INT NOT NULL,
    `ItemID_4` INT NOT NULL, `ItemID_5` INT NOT NULL,
    `ItemCount_1` INT NOT NULL, `ItemCount_2` INT NOT NULL, `ItemCount_3` INT NOT NULL,
    `ItemCount_4` INT NOT NULL, `ItemCount_5` INT NOT NULL,
    `RequiredArenaRating` INT NOT NULL, `ItemPurchaseGroup` INT NOT NULL
  ) ENGINE=InnoDB;
  INSERT INTO `dungeon_vendor_costs_expected`
    (`ID`, `HonorPoints`, `ArenaPoints`, `ArenaBracket`,
     `ItemID_1`, `ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`,
     `ItemCount_1`, `ItemCount_2`, `ItemCount_3`, `ItemCount_4`, `ItemCount_5`,
     `RequiredArenaRating`, `ItemPurchaseGroup`) VALUES
    (97010, 0, 0, 0, 90010, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97011, 0, 0, 0, 90011, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97012, 0, 0, 0, 90012, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97013, 0, 0, 0, 90013, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97014, 0, 0, 0, 90014, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97015, 0, 0, 0, 90015, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97016, 0, 0, 0, 90016, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97017, 0, 0, 0, 90017, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97018, 0, 0, 0, 90018, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97019, 0, 0, 0, 90019, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97020, 0, 0, 0, 90020, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97021, 0, 0, 0, 90021, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97022, 0, 0, 0, 90022, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97023, 0, 0, 0, 90023, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97024, 0, 0, 0, 90024, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97025, 0, 0, 0, 90025, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97026, 0, 0, 0, 90026, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97027, 0, 0, 0, 90027, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97028, 0, 0, 0, 90028, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97029, 0, 0, 0, 90029, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97030, 0, 0, 0, 90030, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97031, 0, 0, 0, 90031, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97032, 0, 0, 0, 90032, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97033, 0, 0, 0, 90033, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97034, 0, 0, 0, 90034, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (97035, 0, 0, 0, 90035, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0),
    (98010, 0, 0, 0, 90010, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98011, 0, 0, 0, 90011, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98012, 0, 0, 0, 90012, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98013, 0, 0, 0, 90013, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98014, 0, 0, 0, 90014, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98015, 0, 0, 0, 90015, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98016, 0, 0, 0, 90016, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98017, 0, 0, 0, 90017, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98018, 0, 0, 0, 90018, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98019, 0, 0, 0, 90019, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98020, 0, 0, 0, 90020, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98021, 0, 0, 0, 90021, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98022, 0, 0, 0, 90022, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98023, 0, 0, 0, 90023, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98024, 0, 0, 0, 90024, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98025, 0, 0, 0, 90025, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98026, 0, 0, 0, 90026, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98027, 0, 0, 0, 90027, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98028, 0, 0, 0, 90028, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98029, 0, 0, 0, 90029, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98030, 0, 0, 0, 90030, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98031, 0, 0, 0, 90031, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98032, 0, 0, 0, 90032, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98033, 0, 0, 0, 90033, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98034, 0, 0, 0, 90034, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (98035, 0, 0, 0, 90035, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0),
    (99010, 0, 0, 0, 90010, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99011, 0, 0, 0, 90011, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99012, 0, 0, 0, 90012, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99013, 0, 0, 0, 90013, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99014, 0, 0, 0, 90014, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99015, 0, 0, 0, 90015, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99016, 0, 0, 0, 90016, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99017, 0, 0, 0, 90017, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99018, 0, 0, 0, 90018, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99019, 0, 0, 0, 90019, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99020, 0, 0, 0, 90020, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99021, 0, 0, 0, 90021, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99022, 0, 0, 0, 90022, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99023, 0, 0, 0, 90023, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99024, 0, 0, 0, 90024, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99025, 0, 0, 0, 90025, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99026, 0, 0, 0, 90026, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99027, 0, 0, 0, 90027, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99028, 0, 0, 0, 90028, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99029, 0, 0, 0, 90029, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99030, 0, 0, 0, 90030, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99031, 0, 0, 0, 90031, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99032, 0, 0, 0, 90032, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99033, 0, 0, 0, 90033, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99034, 0, 0, 0, 90034, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
    (99035, 0, 0, 0, 90035, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0);

  START TRANSACTION;
  -- Validate every owned ID before inserting any missing record. Exact existing
  -- records and every foreign ID are retained without UPDATE/REPLACE/DELETE.
  IF EXISTS (
    SELECT 1 FROM `itemextendedcost_dbc` a
    JOIN `dungeon_vendor_costs_expected` e ON a.`ID` = e.`ID`
    WHERE NOT (a.`HonorPoints` <=> e.`HonorPoints`
      AND a.`ArenaPoints` <=> e.`ArenaPoints` AND a.`ArenaBracket` <=> e.`ArenaBracket`
      AND a.`ItemID_1` <=> e.`ItemID_1` AND a.`ItemID_2` <=> e.`ItemID_2`
      AND a.`ItemID_3` <=> e.`ItemID_3` AND a.`ItemID_4` <=> e.`ItemID_4`
      AND a.`ItemID_5` <=> e.`ItemID_5`
      AND a.`ItemCount_1` <=> e.`ItemCount_1` AND a.`ItemCount_2` <=> e.`ItemCount_2`
      AND a.`ItemCount_3` <=> e.`ItemCount_3` AND a.`ItemCount_4` <=> e.`ItemCount_4`
      AND a.`ItemCount_5` <=> e.`ItemCount_5`
      AND a.`RequiredArenaRating` <=> e.`RequiredArenaRating`
      AND a.`ItemPurchaseGroup` <=> e.`ItemPurchaseGroup`)
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Dungeon vendor costs: owned ID has different fields; no overlay rows changed';
  END IF;

  INSERT INTO `itemextendedcost_dbc`
    (`ID`, `HonorPoints`, `ArenaPoints`, `ArenaBracket`,
     `ItemID_1`, `ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`,
     `ItemCount_1`, `ItemCount_2`, `ItemCount_3`, `ItemCount_4`, `ItemCount_5`,
     `RequiredArenaRating`, `ItemPurchaseGroup`)
  SELECT e.`ID`, e.`HonorPoints`, e.`ArenaPoints`, e.`ArenaBracket`,
    e.`ItemID_1`, e.`ItemID_2`, e.`ItemID_3`, e.`ItemID_4`, e.`ItemID_5`,
    e.`ItemCount_1`, e.`ItemCount_2`, e.`ItemCount_3`, e.`ItemCount_4`, e.`ItemCount_5`,
    e.`RequiredArenaRating`, e.`ItemPurchaseGroup`
  FROM `dungeon_vendor_costs_expected` e
  LEFT JOIN `itemextendedcost_dbc` a ON a.`ID` = e.`ID`
  WHERE a.`ID` IS NULL;
  DROP TEMPORARY TABLE `dungeon_vendor_costs_expected`;
  COMMIT;
END$$
DELIMITER ;
CALL `azerothcore_setup_dungeon_vendor_costs`();
DROP PROCEDURE `azerothcore_setup_dungeon_vendor_costs`;
