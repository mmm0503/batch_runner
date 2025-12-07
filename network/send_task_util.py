import asyncio
import time
from itertools import chain
from typing import List

from more_itertools import chunked, flatten

from batch_data_types.api_types import ApiBatchTask, ApiRequestTask
from network.httpx_client import HttpxClient


class SendTaskUtil:
    '''
    跑批接口类
        - 可以指定并发数
        - 可以指定每次请求的间隔时间，防止请求过快被限流
    '''

    @staticmethod
    async def send_start(api_batch_task: ApiBatchTask):
        # 判断请求参数列表是否为空
        if not api_batch_task.api_request_task_list:
            print("请求参数列表为空，直接返回")
            return []

        # 并发数切片
        api_request_task_list_list: List[List[ApiRequestTask]] = list(
            chunked(api_batch_task.api_request_task_list, api_batch_task.concurrency)
        )

        # 切片后的请求总数
        total_count = len(api_request_task_list_list)
        # 已完成请求数
        completed_count = 0

        for api_request_task_list in api_request_task_list_list:
            api_request_task_list: List[ApiRequestTask] = api_request_task_list
            print(f"并发量：{api_batch_task.concurrency}, 开始处理第 {completed_count} / {total_count - 1} 批次请求...")

            # 构建协程列表并执行
            httpx_list = [
                HttpxClient.create_http_task(api_request_task=api_request_task)
                for api_request_task in api_request_task_list
            ]
            # 并发执行当前chunk的请求
            await asyncio.gather(*httpx_list)

            completed_count += 1

            # 是否最后一批次
            if completed_count == total_count:
                flatten_list = flatten(api_request_task_list_list)
                if api_batch_task.all_complete_callback:
                    api_batch_task.all_complete_callback(api_batch_task)
                return api_batch_task

            # 如果不是最后一批次，且设置了触发回调函数的请求次数
            callback_trigger_count = api_batch_task.callback_trigger_count
            if callback_trigger_count > 0 and completed_count >= callback_trigger_count and completed_count % callback_trigger_count == 0:
                if api_batch_task.all_complete_callback:
                    api_batch_task.all_complete_callback(api_batch_task)

            # 每次请求后休眠指定时间
            if api_batch_task.sleep_time > 0:
                time.sleep(api_batch_task.sleep_time)
