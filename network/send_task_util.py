import asyncio
import time

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
        if concurrency > 0:
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
            print(f"开始处理第 {completed_count} / {total_count - 1} 批次请求...")
            # chunk转为taskItem列表
            task_item_list = [HttpxClient().get_task_item(**c) for c in chunk]
            # 构建协程列表并执行
            httpx_list = [HttpxClient().get_http_task(task_item=task_item) for task_item in task_item_list]
            # 并发执行当前chunk的请求
            responses = await asyncio.gather(*httpx_list)
            # 处理响应结果
            format_responses = []
            for i, resp in enumerate(responses):
                format_res_fn = chunk[i].get("format_res_fn", None)
                if format_res_fn and callable(format_res_fn):
                    format_responses.append(format_res_fn(result=resp, task_item=task_item_list[i]))
                else:
                    format_responses.append(resp)

            completed_count += 1

            # 累计结果
            result_list.extend(format_responses)

            # 请求结束后触发回调函数
            if completed_count == total_count:
                if all_complete_callback:
                    all_complete_callback(result_list=result_list)
                    return

            # 如果不是最后一批次，且设置了触发回调函数的请求次数
            if callback_trigger_count > 0 and completed_count >= callback_trigger_count and completed_count % callback_trigger_count == 0:
                if all_complete_callback:
                    all_complete_callback(result_list=result_list)

            # 每次请求后休眠指定时间
            if sleep_time > 0:
                time.sleep(sleep_time)
