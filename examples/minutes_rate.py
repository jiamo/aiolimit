import asyncio
import aioredis
import pytest
import random
from aiolimit.aiolimit import rate_limit, RateLimit


# 1 minite 1
@rate_limit(key="test_global", rate=(1/30), burst=1)
async def g():
    print("hello")

    
async def main():
    call_n = 0
    while True:
        try:
            await g()
            # try to make it pass
            await asyncio.sleep(1)
            call_n += 1
            if call_n > 4:
                print("already call out 4")
                break
        except RateLimit as e:
            print("RateLimit", e)
            await asyncio.sleep(30)
            
            
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())