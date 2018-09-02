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


def check_failed(ret):
    if ret % 2 == 0:
        return True
    else:
        return False

@rate_limit(key_builder=user_limit,
            rate=5, burst=5,
            only_check_failed=True,
            check_failed=check_failed)
async def fu(user_id):
    # ret = random.randint(0, 10)
    ret = 2
    print("hello ", user_id, "ret ", ret)
    return ret


@rate_limit(key_builder=user_limit,
            rate=5, burst=5,
            only_check_failed=True,
            check_failed=check_failed)
async def fu1(user_id):
    ret = random.randint(0, 10)
    print("hello ", user_id, "ret ", ret)
    return ret


@pytest.mark.asyncio
async def test_fu_check_failed_random():
    with pytest.raises(RateLimit) as rateinfo:
        total1 = 0
        while True:
            await fu(6)
            await asyncio.sleep(0.1)
            total1 += 1

    with pytest.raises(RateLimit) as rateinfo:
        total2 = 0
        failed2 = 0
        while True:
            ret = await fu1(7)
            if check_failed(ret):
                failed2 += 1
            await asyncio.sleep(0.1)
            total2 += 1
    print("after running total2")
    
    # restart
    await  asyncio.sleep(1)
    with pytest.raises(RateLimit) as rateinfo:
        total3 = 0
        failed3 = 0
        while True:
            ret = await fu1(7)
            if check_failed(ret):
                failed3 += 1
            await asyncio.sleep(0.1)
            total3 += 1

    print("total1 {} total2 {} ".format(total1, total2))
    print("failed2 {}".format(failed2))
    assert total2 >= total1
    assert total3 >= total1
    