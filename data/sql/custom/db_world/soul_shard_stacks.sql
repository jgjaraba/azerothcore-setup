USE `acore_world`;

-- Make Soul Shards stackable in stacks of 10 and raise the inventory-wide
-- shard cap to 40 so it is a clean multiple of the new stack size.

UPDATE `item_template`
SET `stackable` = 10
WHERE `entry` = 6265
  AND `stackable` = 1;

UPDATE `item_template`
SET `maxcount` = 40
WHERE `entry` = 6265
  AND `maxcount` = 32;
