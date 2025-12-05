import asyncio
from typing import List

from batch_data_types.api_types import ApiBatchTask, ApiRequestTask, ApiRequestParams
from network.send_task_util import SendTaskUtil


def format_res_fn(api_request_task: ApiRequestTask):
    r = api_request_task.res.json()
    if r.get("code") == 200:
        api_request_task.is_success = True
        api_request_task.format_data = r.get("data", None)
    else:
        api_request_task.is_success = False
        api_request_task.error_message = r.get("message", "未知错误")
    return api_request_task


def all_complete_callback(api_request_task_list: List[ApiRequestTask]):
    for api_request_task in api_request_task_list:
        print(api_request_task.format_data)
    print("所有请求已完成")


origin_batch_list: List[ApiRequestTask] = [
    ApiRequestTask(
        origin_data=None,
        api_param=ApiRequestParams(
            full_url=f"http://localhost:8000/test/test1",
            methods="GET",
            params={"token": f"user{i}"}
        ),
        format_res_fn=format_res_fn
    )
    for i in range(5)
]

asyncio.run(
    SendTaskUtil.send_start(
        ApiBatchTask(
            origin_batch_list=origin_batch_list,
            concurrency=2,  # 并发数
            sleep_time=0.1,  # 每次请求间隔时间，单位秒
            all_complete_callback=all_complete_callback  # 请求全部结束后的回调函数
        )
    )
)
