CREATE TABLE IF NOT EXISTS window (
  `id`       BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
  `team_id`  BIGINT(20)          NOT NULL,
  `pos_id`   VARCHAR(32)         NOT NULL,
  `pos_type` VARCHAR(32)         NOT NULL,
  `status`   TINYINT             NOT NULL,

# find
# id:1
# team_id:*
# pos_id:1

# update
# id:status
# team_id:status