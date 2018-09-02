import aioredis
import logging
import asyncio
import time
import functools


class RateLimit(Exception):
    pass


class TokenBucketManager(object):
    """
    use second as unit
    """
    def __init__(self,
                 redis_pool=None,
                 default_rate=5,
                 default_burst=5):
        self.pool = redis_pool
        self._default_rate = default_rate
        self._default_burst = default_burst
        self._default_init_rate = default_rate - 1
        # use one token after init

    async def connect(self, redis_url):
        if self.pool:
            return

        host, _, port = redis_url.partition(':')
        if not port:
            port = 6379
        try:
            port = int(port)
        except ValueError:
            raise ValueError(port)
        self.pool = await aioredis.create_redis_pool(
            (host, port), minsize=10, maxsize=60)
        print("redis_pool", self.pool, id(self.pool))

    async def get_token(self, key, rate, burst, only_check_failed=False):
        with await self.pool as redis:
            tk = await redis.hget(key, "tk")
            if tk is None:
                tk = await self.create_bucket(
                    redis, key, rate, burst, only_check_failed)
            else:
                tk = int(tk)
            if tk < 1:
                tk = await self.check_and_refill(
                    redis, key, rate, burst, only_check_failed)
                if tk < 0:
                    return False
            else:
                if not only_check_failed:
                    await redis.hset(key, "tk", tk - 1)

        return True

    async def create_bucket(self, redis, key, rate=None, burst=None,
                            only_check_failed=False):
        logging.debug("create bucket")
        ts = time.time()
        if not burst:
            burst = self._default_burst
        if not rate:
            rate = self._default_rate
        if not only_check_failed:
            tk = min(rate, burst) - 1
        else:
            tk = min(rate, burst)

        pipe = redis.pipeline()
        fut1 = pipe.hset(key, "tk", tk)
        fut2 = pipe.hset(key, "ts", ts)
        fut3 = pipe.hset(key, "bst", burst)
        await pipe.execute()
        fut1_result, fut2_result, fut3_result = await\
            asyncio.gather(fut1, fut2, fut3)

        return tk

    async def check_and_refill(self, redis, key, rate=None, burst=None,
                               only_check_failed=False):
        logging.debug("check and refill")
        last_refill = float(await redis.hget(key, "ts"))
        n = int((time.time() - last_refill) / 1)
        if n > 0:
            bst = await redis.hget(key, "bst")
            if not bst:
                if burst:
                    bst = burst
                else:
                    bst = self._default_burst
                await redis.hset(key, "bst", burst)
            bst = int(bst)
            if not rate:
                rate = self._default_rate

            tk = min(rate * n, bst) - 1
            if not only_check_failed:
                pipe = redis.pipeline()
                fut1 = pipe.hset(key, "tk", tk)
                fut2 = pipe.hset(key, "ts", time.time())
                await pipe.execute()
                fut1_result, fut2_result = await asyncio.gather(fut1, fut2)
            return tk
        else:
            return -1


class rate_limit:
    def __init__(
            self, ttl=None, key=None, key_builder=None,
            redis_pool=None,
            noself=False, rate=None, burst=None,
            only_check_failed=False, check_failed=None,
            **kwargs
            ):
        self.ttl = ttl
        self.key = key
        self.key_builder = key_builder
        self.noself = noself
        self.cache = None
        self.rate = rate
        self.burst = burst
        self.redis_pool = redis_pool
        self._kwargs = kwargs
        self.only_check_failed = only_check_failed
        self.check_failed = check_failed

    def __call__(self, f):
        self.limit = TokenBucketManager(redis_pool=self.redis_pool)
        @functools.wraps(f)
        async def wrapper(*args, **kwargs):
            return await self.decorator(f, *args, **kwargs)

        wrapper.cache = self.cache
        return wrapper

    async def decorator(self, f, *args, **kwargs):
        print("id of limit ", id(self.limit))
        key = self.get_cache_key(f, args, kwargs)
        if self.redis_pool:
            pass
        else:
            await self.limit.connect("127.0.0.1:6379")

        access = await self.limit.get_token(
            key, self.rate, self.burst,
            only_check_failed=self.only_check_failed
        )
        if access is False:
            raise RateLimit()

        result = await f(*args, **kwargs)
        if self.only_check_failed:
            fail = self.check_failed(result)
            if fail:
                print("in rate_limit check failed ", fail)
                access = await self.limit.get_token(
                    key, self.rate, self.burst)  # make it normal
                if access is False:
                    raise RateLimit()

        return result

    def get_cache_key(self, f, args, kwargs):
        if self.key:
            return self.key
        if self.key_builder:
            return self.key_builder(*args, **kwargs)

        return self._key_from_args(f, args, kwargs)

    def _key_from_args(self, func, args, kwargs):
        ordered_kwargs = sorted(kwargs.items())
        return (func.__module__ or '') + func.__name__ + str(
            args[1:] if self.noself else args) + str(ordered_kwargs)




