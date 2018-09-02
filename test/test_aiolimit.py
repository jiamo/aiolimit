import asyncio
import aioredis
import pytest
import random
from aiolimit.aiolimit import rate_limit, RateLimit


@rate_limit(key="test_global", rate=5, burst=5)
async def g():
    print("hello")


def user_limit(user_id):
    return "limit_user_id_{user_id}".format(user_id=user_id)


@rate_limit(key_builder=user_limit, rate=5, burst=5)
async def fu(user_id):
    print("hello ", user_id)


@rate_limit(key_builder=user_limit, rate=5, burst=5)
async def fu2(user_id):
    print("hello ", user_id)


@rate_limit(key_builder=user_limit, rate=5, burst=5)
async def fu3(user_id):
    print("hello ", user_id)



@pytest.fixture(scope='function')
async def redis_pool():
    pool = await aioredis.create_redis_pool(
            ("127.0.0.1", 6379), minsize=10, maxsize=60)
    yield pool
    pool.close()
    print("after use pool")


@pytest.mark.asyncio
async def test_fu_failed():
    with pytest.raises(RateLimit) as rateinfo:

        while True:
            await fu(1)
            await fu3(3)
            await asyncio.sleep(0.1)

        print(rateinfo)


@pytest.mark.asyncio
async def test_fu_success():

    call_n = 0
    while True:
        await fu2(9)
        # try to make it pass
        await asyncio.sleep(0.22)
        call_n += 1
        if call_n > 20:
            print("already call out 20")
            break


@pytest.mark.asyncio
async def test_g():
    with pytest.raises(RateLimit) as rateinfo:

        while True:
            await g()
            await asyncio.sleep(0.1)

        print(rateinfo)


@pytest.mark.asyncio
async def test_fu_failed_with_redis_pool(redis_pool):

    @rate_limit(key_builder=user_limit, rate=5, burst=5, redis_pool=redis_pool)
    async def fu4(user_id):
        print("hello ", user_id)

    with pytest.raises(RateLimit) as rateinfo:

        while True:
            await fu4(4)
            await asyncio.sleep(0.1)

        print(rateinfo)

