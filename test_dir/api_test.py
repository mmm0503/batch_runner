import asyncio
from typing import List

from batch_data_types.api_types import ApiBatchTask, ApiRequestTask, ApiRequestParams
from network.send_task_util import SendTaskUtil


# 结果格式化函数
def format_res_fn(api_request_task: ApiRequestTask):
    r = api_request_task.res.json()
    if r.get("code") == 200:
        api_request_task.is_success = True
        api_request_task.format_data = r.get("data", None)
    else:
        api_request_task.is_success = False
        api_request_task.error_message = r.get("message", "未知错误")
    return api_request_task


# 所有请求结束后的回调函数
def all_complete_callback(api_batch_task: ApiBatchTask):
    print("所有请求已完成")
    for api_request_task in api_batch_task.origin_batch_list:
        print(api_request_task.format_data, api_request_task.time_cost)


origin_batch_list: List[ApiRequestTask] = [
    ApiRequestTask(
        origin_data=None,
        api_param=ApiRequestParams(
            full_url=f"http://localhost:8000/test/getTest",
            methods="GET",
            params={"time": "1"}
        ),
        format_res_fn=format_res_fn
    )
    for i in range(2)
]


def main():
    asyncio.run(
        SendTaskUtil.send_start(
            ApiBatchTask(
                origin_batch_list=origin_batch_list,
                concurrency=2,  # 并发数
                all_complete_callback=all_complete_callback  # 请求全部结束后的回调函数
            )
        )
    )


main()
