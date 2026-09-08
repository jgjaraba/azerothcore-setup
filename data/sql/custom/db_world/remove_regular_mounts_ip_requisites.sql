START TRANSACTION;

-- ============================================================
-- Individual Progression - Mount vendor progression cleanup
--
-- 1. Later-expansion racial mounts remain permanently available.
--    They are cosmetic / low-level content, not catch-up content.
--
-- 2. Original pre-1.4 epic racial mounts remain limited-time,
--    but are retired after Molten Core (when BWL becomes available)
--    instead of after Onyxia.
-- ============================================================


-- ------------------------------------------------------------
-- Remove WotLK progression gates from ordinary racial mounts
-- ------------------------------------------------------------

DELETE FROM `conditions`
WHERE `SourceTypeOrReferenceId` = 23
  AND `ConditionTypeOrReference` = 8
  AND (
    (`SourceGroup` = 3362 AND `SourceEntry` = 46099) -- Horn of the Black Wolf
        OR (`SourceGroup` = 3685 AND `SourceEntry` = 46100) -- White Kodo
        OR (`SourceGroup` = 4731 AND `SourceEntry` = 46308) -- Black Skeletal Horse
        OR (`SourceGroup` = 4731 AND `SourceEntry` = 47101) -- Ochre Skeletal Warhorse
    );

COMMIT;