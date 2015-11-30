CREATE TABLE IF NOT EXISTS merchant_pos (
  `id`            BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
  `merchant_id`   VARCHAR(16)         NOT NULL,
  `merchant_name` VARCHAR(32)         NOT NULL,
  `pos_id`        VARCHAR(32)         NOT NULL,
  `create_time`   TIMESTAMP           NOT NULL,
  `status`        TINYINT             NOT NULL,

# find
# id:1
# merchant_id,pos_id,status:1

# update
# pos_id:status
# merchant_id:status