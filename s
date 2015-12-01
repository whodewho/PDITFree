CREATE TABLE IF NOT EXISTS refund_order (
  `refund_id`           VARCHAR(32)  NOT NULL
  COMMENT '唯一退款订单号',
  `order_id`            VARCHAR(32)  NOT NULL
  COMMENT '唯一订单号',
  `user_id`             VARCHAR(16)  NOT NULL
  COMMENT '',
  `cashier_id`          VARCHAR(16)  NOT NULL
  COMMENT '发起退款的收银员ID',
  `create_time`         TIMESTAMP    NOT NULL
  COMMENT '订单创建时间',
  `apply_refund_amount` INT(11)      NOT NULL
  COMMENT '申请退款金额,单位分',
  `refund_reason`       VARCHAR(128) NOT NULL
  COMMENT '申请退款原因',
  `refund_amount`       INT(11)      NOT NULL DEFAULT '0'
  COMMENT '实际退款金额,单位分',
  `refund_trade_id`     CHAR(32)              DEFAULT NULL
  COMMENT '支付中心唯一退款交易号',
  `refund_status`       TINYINT      NOT NULL DEFAULT '11'
  COMMENT '退款状态,11为申请退款,12为退款成功,13为退款失败',
  `refund_time`         TIMESTAMP    NOT NULL DEFAULT '1970-01-02 00:00:00'
  COMMENT '退款时间',
  `refund_desc`         VARCHAR(128)          DEFAULT NULL
  COMMENT '退款结果描述',
  `modify_time`         TIMESTAMP    NOT NULL
  COMMENT '更新时间',
  `modify_ip`           VARCHAR(32)           DEFAULT NULL
  COMMENT '请求hostIP',
  `refund_try_count`    TINYINT      NOT NULL DEFAULT 0
  COMMENT '重试退款的次数',

# find
# refund_id:1
# order_id,user_id:1
# user_id,refund_status,refund_time between start_time and end_time:*

# update
# refund_id:refund_time,refund_status,modify_time