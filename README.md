# RedLock 分布式锁

基于 Redis 官方提出的设想 https://redis.io/topics/distlock/  实现；

参考 https://github.com/SPSCommerce/redlock-py 设计的代码实现；

具备以下优点

    - 互斥性 任一时刻有且只有一个客户端持有锁；
    - 无死锁 即使持有锁的客户端或者小部分服务器崩溃也能稳定运行；
    - 容错性 只要大多数服务器正常运转，就能够提供稳定的锁服务；

网络上有非常多关于分布式锁具体实现的文章和案例，其中基于 Redis 和 Python 的也不少；综合多方意见

我认为 Redis 官方提出的 Redlock 是一种很有意义的分布式锁实现方式，接着参考了 SPSCommerce 团队的实现

编写了你现在看到的这段代码；

在 Redlock 的 Python 范例的基础上，我做了一些小的改动，让它更贴近实际场景；



### 稳定性

RedLock 在理论上有 Redis Redlock 的支撑，同时参考了 SPSCommerce 的具体实现，我认为它是稳定的，完全可以用在生产环境当中；

### 使用方法

近段时间工作忙，还没来得及将它制作成为一个库，大家可以直接把代码复制到项目中使用，文件中有具体的调用方法；

假设你在本机启动了 3 个 Redis 服务，它们分别是 ` localhost 6379丨localhost 6389丨localhost 6399`，那么运行文件时你会在终端看到如下提示：

```
INFO 2020-10-31 18:46:36 Saturday main.py Line: 72 节点 Redis<ConnectionPool<Connection<host=localhost,port=6379,db=5>>> 连接结果为 [True];
INFO 2020-10-31 18:46:36 Saturday main.py Line: 72 节点 Redis<ConnectionPool<Connection<host=localhost,port=6389,db=5>>> 连接结果为 [True];
INFO 2020-10-31 18:46:36 Saturday main.py Line: 72 节点 Redis<ConnectionPool<Connection<host=localhost,port=6399,db=5>>> 连接结果为 [True];
INFO 2020-10-31 18:46:36 Saturday main.py Line: 78 创建一个拥有 3/3 个有效节点的 RedLock 实例；期望的节点为 [{'host': 'localhost', 'port': 6379, 'db': 5}, {'host': 'localhost', 'port': 6389, 'db': 5}, {'host': 'localhost', 'port': 6399, 'db': 5}]；有效节点为 [Redis<ConnectionPool<Connection<host=localhost,port=6379,db=5>>>, Redis<ConnectionPool<Connection<host=localhost,port=6389,db=5>>>, Redis<ConnectionPool<Connection<host=localhost,port=6399,db=5>>>]
INFO 2020-10-31 18:46:36 Saturday main.py Line: 84 服务器 [Redis<ConnectionPool<Connection<host=localhost,port=6379,db=5>>>] 上执行锁 [吾身如剑] 操作的结果为 [True]，此时锁值为 [91e29a16-6da0-490b-b273-47942eeee623-0b6c87d4-dded-47c8-a753-7f1ff45b186d]；
INFO 2020-10-31 18:46:36 Saturday main.py Line: 84 服务器 [Redis<ConnectionPool<Connection<host=localhost,port=6389,db=5>>>] 上执行锁 [吾身如剑] 操作的结果为 [True]，此时锁值为 [91e29a16-6da0-490b-b273-47942eeee623-0b6c87d4-dded-47c8-a753-7f1ff45b186d]；
INFO 2020-10-31 18:46:36 Saturday main.py Line: 84 服务器 [Redis<ConnectionPool<Connection<host=localhost,port=6399,db=5>>>] 上执行锁 [吾身如剑] 操作的结果为 [True]，此时锁值为 [91e29a16-6da0-490b-b273-47942eeee623-0b6c87d4-dded-47c8-a753-7f1ff45b186d]；
INFO 2020-10-31 18:46:36 Saturday main.py Line: 124 一帆风顺，现在将锁 [Lock(validity=98998, resource='吾身如剑', key='91e29a16-6da0-490b-b273-47942eeee623-0b6c87d4-dded-47c8-a753-7f1ff45b186d')] 交给客户端；
INFO 2020-10-31 18:46:36 Saturday main.py Line: 93 服务器 [Redis<ConnectionPool<Connection<host=localhost,port=6379,db=5>>>] 上执行锁 [吾身如剑] 释放的结果为 [1]，此时锁值为 [91e29a16-6da0-490b-b273-47942eeee623-0b6c87d4-dded-47c8-a753-7f1ff45b186d]；
INFO 2020-10-31 18:46:36 Saturday main.py Line: 93 服务器 [Redis<ConnectionPool<Connection<host=localhost,port=6389,db=5>>>] 上执行锁 [吾身如剑] 释放的结果为 [1]，此时锁值为 [91e29a16-6da0-490b-b273-47942eeee623-0b6c87d4-dded-47c8-a753-7f1ff45b186d]；
INFO 2020-10-31 18:46:36 Saturday main.py Line: 93 服务器 [Redis<ConnectionPool<Connection<host=localhost,port=6399,db=5>>>] 上执行锁 [吾身如剑] 释放的结果为 [1]，此时锁值为 [91e29a16-6da0-490b-b273-47942eeee623-0b6c87d4-dded-47c8-a753-7f1ff45b186d]；
```

从运行日志可以看出，本次创建了一个拥有 3 个有效节点的 RedLock 实例。如果你填写了 3 个 Redis 服务，但实际上只有 2 个有效，那么你将会看到这样的信息：

```
INFO 2020-10-31 18:50:48 Saturday main.py Line: 72 节点 Redis<ConnectionPool<Connection<host=localhost,port=6379,db=5>>> 连接结果为 [True];
ERROR 2020-10-31 18:50:48 Saturday main.py Line: 74 Error 61 connecting to localhost:6389. Connection refused.
INFO 2020-10-31 18:50:48 Saturday main.py Line: 72 节点 Redis<ConnectionPool<Connection<host=localhost,port=6399,db=5>>> 连接结果为 [True];
INFO 2020-10-31 18:50:48 Saturday main.py Line: 78 创建一个拥有 2/3 个有效节点的 RedLock 实例；期望的节点为 [{'host': 'localhost', 'port': 6379, 'db': 5}, {'host': 'localhost', 'port': 6389, 'db': 5}, {'host': 'localhost', 'port': 6399, 'db': 5}]；有效节点为 [Redis<ConnectionPool<Connection<host=localhost,port=6379,db=5>>>, Redis<ConnectionPool<Connection<host=localhost,port=6399,db=5>>>]
INFO 2020-10-31 18:50:48 Saturday main.py Line: 84 服务器 [Redis<ConnectionPool<Connection<host=localhost,port=6379,db=5>>>] 上执行锁 [吾身如剑] 操作的结果为 [True]，此时锁值为 [d515a37b-0e9c-4327-9d44-fb74f6525cd2-4aecade4-1162-49ea-b0a9-f7968878fffb]；
INFO 2020-10-31 18:50:48 Saturday main.py Line: 84 服务器 [Redis<ConnectionPool<Connection<host=localhost,port=6399,db=5>>>] 上执行锁 [吾身如剑] 操作的结果为 [True]，此时锁值为 [d515a37b-0e9c-4327-9d44-fb74f6525cd2-4aecade4-1162-49ea-b0a9-f7968878fffb]；
INFO 2020-10-31 18:50:48 Saturday main.py Line: 124 一帆风顺，现在将锁 [Lock(validity=98998, resource='吾身如剑', key='d515a37b-0e9c-4327-9d44-fb74f6525cd2-4aecade4-1162-49ea-b0a9-f7968878fffb')] 交给客户端；
INFO 2020-10-31 18:50:48 Saturday main.py Line: 93 服务器 [Redis<ConnectionPool<Connection<host=localhost,port=6379,db=5>>>] 上执行锁 [吾身如剑] 释放的结果为 [1]，此时锁值为 [d515a37b-0e9c-4327-9d44-fb74f6525cd2-4aecade4-1162-49ea-b0a9-f7968878fffb]；
INFO 2020-10-31 18:50:48 Saturday main.py Line: 93 服务器 [Redis<ConnectionPool<Connection<host=localhost,port=6399,db=5>>>] 上执行锁 [吾身如剑] 释放的结果为 [1]，此时锁值为 [d515a37b-0e9c-4327-9d44-fb74f6525cd2-4aecade4-1162-49ea-b0a9-f7968878fffb]；
```

3 个节点中只有 2 个有效，另外 1 个连接失败（可以想象是服务崩溃或者服务停止），这时候 RedLock 仍然能够正常工作，这是因为 Redis 服务列表中大多数服务是正常的；

我们来看一个反例，如果3 个节点中只有 1 个有效，另外 2 个连接失败，会发生什么：
```
INFO 2020-10-31 18:53:27 Saturday main.py Line: 72 节点 Redis<ConnectionPool<Connection<host=localhost,port=6379,db=5>>> 连接结果为 [True];
ERROR 2020-10-31 18:53:27 Saturday main.py Line: 74 Error 61 connecting to localhost:6389. Connection refused.
ERROR 2020-10-31 18:53:27 Saturday main.py Line: 74 Error 61 connecting to localhost:6399. Connection refused.
Traceback (most recent call last):
  File "/Users/vansen/Documents/GitHub/RedLock/main.py", line 155, in <module>
    rek = RedLock(redis_servers)
  File "/Users/vansen/Documents/GitHub/RedLock/main.py", line 77, in __init__
    raise ConditionException(ext)
__main__.ConditionException: 哦豁！仅能连接包括 [[Redis<ConnectionPool<Connection<host=localhost,port=6379,db=5>>>]] 的一小部分服务器，这种条件下无法保持锁的稳定性，请您检查;
```

运行日志中给出了明确的信息【一小部分服务器，这种条件下无法保持锁的稳定性】，于是它便不提供服务；

这是 RedLock 面对不同服务器场景的反应，阁下觉得如何？

### 当前版本号

```
v0.1
```

### 开发日志

```
[2020-10-31] [v0.1] 已经具备完整功能，可用于生产环境；
```


### 待办事项

- 单元测试
- 打包

