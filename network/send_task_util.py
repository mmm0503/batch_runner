import asyncio
from typing import List
import time

from batch_data_types.api_types import ApiBatchTask, ApiRequestTask, ApiRequestParams
from network.httpx_client import HttpxClient


class SendTaskUtil:
    '''
    跑批接口类
        - 可以指定并发数
        - 可以指定每次请求的间隔时间，防止请求过快被限流
    '''

    async def send_start(self, api_batch_task: ApiBatchTask):
        concurrency = api_batch_task.concurrency

        # 判断请求参数列表是否为空
        if not api_batch_task.origin_batch_list:
            print("请求参数列表为空，无法发送请求")
            return []

        # 并发数切片
        api_request_task_list_list: List[List[ApiRequestTask]] = [
            api_batch_task.origin_batch_list[i:i + concurrency]
            for i in range(0, len(api_batch_task.origin_batch_list), concurrency)
        ]

        # 切片后的请求总数
        total_count = len(api_request_task_list_list)
        # 已完成请求数
        completed_count = 0

        for api_request_task_list in api_request_task_list_list:
            api_request_task_list: List[ApiRequestTask] = api_request_task_list
            print(f"开始处理第 {completed_count} / {total_count - 1} 批次请求...")

            # 构建协程列表并执行
            httpx_list = [
                HttpxClient().create_http_task(api_request_task=api_request_task)
                for api_request_task in api_request_task_list
            ]
            # 并发执行当前chunk的请求
            res_list = await asyncio.gather(*httpx_list)

            # 处理响应结果
            for i, res in enumerate(res_list):
                curr_task: ApiRequestTask = api_request_task_list[i]
                curr_task.res = res
                # 执行后处理函数
                if curr_task.format_res_fn:
                    curr_task.format_res_fn(curr_task)

            completed_count += 1

            # 请求结束后触发回调函数
            all_complete_callback = api_batch_task.all_complete_callback
            if completed_count == total_count:
                if all_complete_callback:
                    all_complete_callback(api_request_task_list_list)
                    return

            # 如果不是最后一批次，且设置了触发回调函数的请求次数
            callback_trigger_count = api_batch_task.callback_trigger_count
            if callback_trigger_count > 0 and completed_count >= callback_trigger_count and completed_count % callback_trigger_count == 0:
                if all_complete_callback:
                    all_complete_callback(api_request_task_list_list)

            # 每次请求后休眠指定时间
            if api_batch_task.sleep_time > 0:
                time.sleep(api_batch_task.sleep_time)
