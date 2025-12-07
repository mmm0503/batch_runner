import asyncio
from typing import Optional, Callable

from more_itertools import chunked

from batch_data_types.api_types import ApiBatchTask, ApiRequestTask
from network.httpx_client import HttpxClient


class HttpBatchHandler:
    origin_batch_data_list: list
    create_api_task_params_fn: Optional[Callable] = None  # 根据原始数据row创建 ApiRequestParams 的函数
    format_res_fn: Optional[Callable] = None  # 格式化接口返回结果的函数
    complete_callback: Optional[Callable] = None  # 请求完成后的回调函数

    def __init__(self, origin_batch_data_list: list):
        self.origin_batch_data_list = origin_batch_data_list

    async def batch_run(self, requests):
        chunk_list = self.chunked()
        # 切片后的请求总数
        total_count = len(chunk_list)
        # 已完成请求数
        completed_count = 0

        for chunk in chunk_list:
            api_request_task_list: list[ApiRequestTask] = chunk
            print(f"并发量：{self.concurrency}, 开始处理第 {completed_count} / {total_count - 1} 批次请求...")
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
                if self.complete_callback:
                    self.complete_callback()
                return self.get_api_batch_task()

    def chunked(self):
        """将请求列表分块为指定大小的块"""
        return list(chunked(self.api_request_task_list, self.concurrency))

    def get_api_batch_task(self) -> ApiBatchTask:
        return ApiBatchTask(
            api_request_task_list=self.api_request_task_list,
            concurrency=self.concurrency,
            sleep_time=self.sleep_time,
            callback_trigger_count=self.callback_trigger_count,
            complete_callback=self.complete_callback,
        )
