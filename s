CREATE TABLE IF NOT EXISTS user_coupon (
  `id`          BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`     VARCHAR(16)         NOT NULL,
  `coupon_id`   BIGINT(20)          NOT NULL,
  `create_time` TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `start_time`  TIMESTAMP           NOT NULL,
  `expire_time` TIMESTAMP           NOT NULL,
  `usage_time`  TIMESTAMP           NOT NULL,
  `valid`       TINYINT             NOT NULL DEFAULT 1,

  PRIMARY KEY (`id`),
  KEY `idx_usercoupon_userid` (`user_id`)
