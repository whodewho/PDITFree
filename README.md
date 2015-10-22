# PDITFree

如果你受够了Spring框架下无休止的POJO+DAO+IMPL+TEST代码，跑下这个脚本，PDIT Free

先写一个预处理文件s

第一部分是SQL，是的，只拷贝这么多

第二部分是find
> * session_id:1，指用id查询返回1个结果
> * session_id,currentTime between create_time and expire_time:*，where里有两个约束，非列变量用驼峰
> * Equal单写，运算符要写全，逗号分割；返回1个用'1'，多个用'*'；前后':'分割

第三部分是update
> * 前后':'分割，前面是key，后面是要变更的value

第四部分，没有第四部分，save会自动生成

s文件例子如下
```python
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
  # session_id,pos_id:*

  # update
  # session_id:expire_time
  # session_id,pos_id:valid,expire_time
```

当一个动作不停的重复的时候，它就是垃圾动作，一定要自动化砍掉这80%

觉得文档难写，是因为你废话太多

边用边改，边做边爱