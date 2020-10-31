#coding:utf8
import time
import uuid
import logging
from collections import namedtuple

import redis


LockTuple = namedtuple("Lock", ("validity", "resource", "key"))
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s %(asctime)s %(filename)s Line: %(lineno)d %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S %A',
)


class ConditionException(Exception):
    def __init__(self, reason, *args, **kwargs):
        super(ConditionException, self).__init__(*args, **kwargs)
        if not isinstance(reason, str):
            reason = str(reason)
        self.reason = reason

    def __str__(self):
        return self.reason

    def __repr__(self):
        return self.__str__()


class LockException(Exception):
    def __init__(self, errors, *args, **kwargs):
        super(LockException, self).__init__(*args, **kwargs)
        self.errors = errors

    def __str__(self):
        return "::".join([str(ext) for ext in self.errors])

    def __repr__(self):
        return self.__str__()


class RedLock:
    """ 分布式锁
    基于 https://redis.io/topics/distlock/ 提出的设想实现；
    参考 https://github.com/SPSCommerce/redlock-py 设计的代码实现；
    具备以下优点
        - 互斥性 任一时刻有且只有一个客户端持有锁；
        - 无死锁 即使持有锁的客户端或者小部分服务器崩溃也能稳定运行；
        - 容错性 只要大多数服务器正常运转，就能够提供稳定的锁服务；
    """
    def __init__(self, servers, retry=3, delay=0.2):
        self.release_script = """
        if redis.call("get",KEYS[1]) == ARGV[1] then
            return redis.call("del",KEYS[1])
        else
            return 0
        end"""

        self.retry = retry
        self.delay = delay
        self.clock_drift_factor = 0.01
        self.quorum = len(servers) // 2 + 1
        self.redis_servers = []
        for ser in servers:
            server = redis.Redis(**ser)
            try:
                result = server.set(str(uuid.uuid4()), 1, ex=1)
                if result:
                    self.redis_servers.append(server)
                logging.info("节点 {} 连接结果为 [{}];".format(server, result))
            except Exception as ext:
                logging.error(ext)
        if self.quorum > len(self.redis_servers):
            ext = "哦豁！仅能连接包括 [{}] 的一小部分服务器，这种条件下无法保持锁的稳定性，请您检查;".format(self.redis_servers)
            raise ConditionException(ext)
        logging.info("创建一个拥有 {}/{} 个有效节点的 RedLock 实例；期望的节点为 {}；有效节点为 {}".format(len(self.redis_servers), len(servers), servers, self.redis_servers))

    @staticmethod
    def _lockout(server, resource, value, ttl):
        try:
            result = server.set(resource, value, nx=True, px=ttl)
            logging.info("服务器 [{}] 上执行锁 [{}] 操作的结果为 [{}]，此时锁值为 [{}]；".format(server, resource, result, value))
            return result
        except Exception as ext:
            ext = "哦豁！在服务器 [{}] 上执行锁 [{}] 操作时失败，异常信息为 [{}]，请您检查；".format(server, resource, str(ext))
            raise LockException([ext])

    def _release(self, server, resource, value):
        try:
            result = server.eval(self.release_script, 1, resource, value)
            logging.info("服务器 [{}] 上执行锁 [{}] 释放的结果为 [{}]，此时锁值为 [{}]；".format(server, resource, result, value))
        except Exception as ext:
            ext = "哦豁！在服务器 [{}] 上执行锁 [{}] 释放时失败，异常信息为 [{}]，请您检查；".format(server, resource, str(ext))
            raise LockException([ext])

    @staticmethod
    def _generator_unique_identifier():
        identifier = "{}-{}".format(str(uuid.uuid4()), str(uuid.uuid4()))
        return identifier

    def locking(self, resource, ttl):
        retry = 0
        identifier = self._generator_unique_identifier()
        drift = int(ttl * self.clock_drift_factor) + 2
        errors = []
        while retry < self.retry:
            success_lock_times = 0
            start = int(time.time() * 1e3)
            del errors[:]
            for server in self.redis_servers:
                try:
                    if self._lockout(server, resource, identifier, ttl):
                        success_lock_times += 1
                except Exception as ext:
                    errors.append(str(ext))
            elapsed = int(time.time() * 1e3) - start
            validity = int(ttl - elapsed - drift)
            if validity > 0 and success_lock_times >= self.quorum:
                if errors:
                    raise LockException(errors)
                information = LockTuple(validity, resource, identifier)
                logging.info("一帆风顺，现在将锁 [{}] 交给客户端；".format(information))
                return information, True
            else:
                for server in self.redis_servers:
                    try:
                        self._release(server, resource, identifier)
                    except Exception as ext:
                        logging.error(ext)
                retry += 1
                logging.info("故事曲折，即将开始第 {} 轮尝试；".format(retry + 1))
                time.sleep(self.delay)
        logging.info("很遗憾，本次未能获得锁 [{}]；".format(resource))
        return LockTuple(0, resource, identifier), False

    def release(self, lock):
        errors = []
        for server in self.redis_servers:
            try:
                self._release(server, lock.resource, lock.key)
            except Exception as ext:
                errors.append(ext)
        if errors:
            raise LockException(errors)


if __name__ == "__main__":
    redis_servers = [
        {"host": "localhost", "port": 6379, "db": 5},
        {"host": "localhost", "port": 6389, "db": 5},
        {"host": "localhost", "port": 6399, "db": 5},
    ]
    rek = RedLock(redis_servers)
    instance, result = rek.locking("吾身如剑", 100000)
    if result:
        rek.release(instance)
