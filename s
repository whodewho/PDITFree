CREATE TABLE IF NOT EXISTS pos_session (
  `id`          BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
  `session_id`  VARCHAR(40)         NOT NULL,
  `pos_id`      VARCHAR(32)         NOT NULL,
  `cashier_id`  VARCHAR(16)         NOT NULL,
  `merchant_id` VARCHAR(16)         NOT NULL,
  `create_time` TIMESTAMP           NOT NULL,
  `expire_time` TIMESTAMP           NOT NULL,
  `valid`       TINYINT             NOT NULL DEFAULT 1,

  # find
  # session_id:1
  # session_id,currentTime between create_time and expire_time:*
  # session_id,currentTime < expire_time:*

  # update
  # session_id:expire_time