import asyncio


async def worker(n):
    try:
        await asyncio.sleep(n)
        return f"done {n}"
    finally:
        print(f"worker {n} cleaned up")


async def main():
    # 并发运行两个协程
    t1 = asyncio.create_task(worker(2))
    t2 = asyncio.create_task(worker(3))

    try:
        results = await asyncio.gather(t1, t2)
        return results
    except asyncio.CancelledError:
        # 做必要的清理
        raise


if __name__ == "__main__":
    res = asyncio.run(main())
    print(res)
