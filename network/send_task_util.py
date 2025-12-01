import asyncio

from network.httpx_client import HttpxClient


class SendTaskUtil:
    '''
    跑批接口类
        - 可以指定并发数
        - 可以指定每次请求的间隔时间，防止请求过快被限流
    '''

    async def send_start(
            self,
            # 请求参数列表，里面有：{url, method, params, data, headers, format_res, timeout}
            origin_batch_list=[],
            # 并发数
            concurrency=1,
            # 每次请求间隔时间，单位秒
            sleep_time=2,
            # 请求到一定次数，触发一次回调函数
            callback_trigger_count=0,
            # 请求全部结束后的回调函数
            all_complete_callback=None,
    ):
        # 判断请求参数列表是否为空
        if not origin_batch_list:
            print("请求参数列表为空，无法发送请求")
            return []

        chunks = origin_batch_list.copy()
        if concurrency > 1:
            # 将request_params_list分割为多个子列表，每个子列表长度为concurrency
            chunks = [
                origin_batch_list[i:i + concurrency]
                for i in range(0, len(origin_batch_list), concurrency)
            ]

        # 总请求数
        total_count = len(chunks)
        # 已完成请求数
        completed_count = 0
        # 返回结果列表
        result_list = []

        for chunk in chunks:
            # chunk转为taskItem列表
            result_chunk = [
                HttpxClient().get_task_item(
                    url=item.get("url", ""),
                    methods=item.get("method", "GET"),
                    params=item.get("params", None),
                    data=item.get("data", None),
                    headers=item.get("headers", None),
                    format_res_fn=item.get("format_res_fn", None),
                    timeout=item.get("timeout", None)
                ) for item in chunk
            ]
            # 构建协程列表并执行
            result_chunk = [
                HttpxClient().get_http_task(
                    url=item["taskParam"]["url"],
                    methods=item["taskParam"]["methods"],
                    params=item["taskParam"]["params"],
                    data=item["taskParam"]["data"],
                    headers=item["taskParam"]["headers"],
                    format_res_fn=item["taskParam"]["format_res_fn"],
                    timeout=item["taskParam"]["timeout"]
                ) for item in result_chunk
            ]
            # 并发执行当前chunk的请求
            responses = await asyncio.gather(*result_chunk)

            completed_count += 1

            # 每次请求后休眠指定时间
            if sleep_time > 0:
                import time
                time.sleep(sleep_time)

            # 触发部分完成回调函数
            if callback_trigger_count > 0 and completed_count % callback_trigger_count == 0:
                if all_complete_callback:
                    all_complete_callback(partial=True, completed_count=completed_count, total_count=total_count)

# async def fetch_all(objects):
#     async with httpx.AsyncClient() as client:
#         # 构造任务列表
#         tasks = [client.get(obj['url']) for obj in objects]
#         # 按顺序等待所有结果
#         responses = await asyncio.gather(*tasks)
#         # 如果你想要响应的文本结果，可以这样处理
#         result = [resp.text for resp in responses]
#         return result
