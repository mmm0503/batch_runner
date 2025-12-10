import asyncio
import time
import httpx

from batch_data_types.api_types import ApiRequestTask


class HttpxHandler:
    client: httpx.Client
    async_client: httpx.AsyncClient

    def __init__(self):
        self.client = httpx.Client()
        self.async_client = httpx.AsyncClient()

    def get_client(self):
        return self.client

    def get_async_client(self):
        return self.async_client

    async def async_send_api_task(self, api_request_task: ApiRequestTask):
        '''
        发送单个异步请求,并保存结果到 api_request_task 中
        结果包括：
            - http_is_success: 请求是否成功
            - res: 请求响应结果
            - time_cost: 请求耗时
        '''
        try:
            # 如果任务已经成功，则不再发送请求
            if api_request_task.task_is_success:
                return

            print(api_request_task.api_param.json)
            res = None
            start_time = time.time()
            methods = api_request_task.api_param.methods.upper()
            is_stream = api_request_task.api_param.is_stream
            match methods:
                case "GET":
                    res = await self.async_client.get(
                        url=api_request_task.api_param.full_url,
                        params=api_request_task.api_param.params,
                        headers=api_request_task.api_param.headers,
                        timeout=api_request_task.api_param.timeout
                    )
                case "POST":
                    # json 和 data 只能传一个,否则会报错
                    if api_request_task.api_param.data and api_request_task.api_param.json:
                        raise ValueError("POST请求中，json和data参数只能传一个")

                    if is_stream:
                        async with self.async_client.stream(
                                method="POST",
                                url=api_request_task.api_param.full_url,
                                params=api_request_task.api_param.params,
                                headers=api_request_task.api_param.headers,
                                json=api_request_task.api_param.json,
                                data=api_request_task.api_param.data,
                                timeout=api_request_task.api_param.timeout
                        ) as response:
                            chunks = []
                            async for chunk in response.aiter_bytes():
                                chunks.append(chunk)
                            res = b"".join(chunks)
                    else:
                        res = await self.async_client.post(
                            url=api_request_task.api_param.full_url,
                            params=api_request_task.api_param.params,
                            headers=api_request_task.api_param.headers,
                            json=api_request_task.api_param.json,
                            data=api_request_task.api_param.data,
                            timeout=api_request_task.api_param.timeout
                        )
            end_time = time.time()
            api_request_task.time_cost = end_time - start_time  # 计算接口总耗时
            if is_stream:
                api_request_task.res = res.decode("utf-8")  # 保存响应结果
            else:
                api_request_task.res = res.json()  # 保存响应结果
        except Exception as e:
            print("HTTP请求异常：", e)

    async def async_send_api_task_list(self, api_request_task_list: list[ApiRequestTask]):
        '''
        批量发送异步请求
        '''
        async_api_tasks = [
            self.async_send_api_task(api_request_task)
            for api_request_task in api_request_task_list
        ]
        await asyncio.gather(*async_api_tasks)
