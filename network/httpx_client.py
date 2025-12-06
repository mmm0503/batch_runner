import ssl
import httpx
import time

from batch_data_types.api_types import ApiRequestTask, ApiRequestParams

context = ssl.create_default_context()
# Python 3.10 以上，OpenSSL 3.0 的情况
if hasattr(ssl, "OP_LEGACY_SERVER_CONNECT"):
    context.options |= ssl.OP_LEGACY_SERVER_CONNECT

api_client = httpx.AsyncClient(verify=context)


class HttpxClient:

    # 构建HTTP请求协程
    @staticmethod
    async def create_http_task(api_request_task: ApiRequestTask):
        try:
            res = None
            start_time = time.time()
            methods = api_request_task.api_param.methods.upper()
            match methods:
                case "GET":
                    res = await api_client.get(
                        url=api_request_task.api_param.full_url,
                        params=api_request_task.api_param.params,
                        headers=api_request_task.api_param.headers,
                        timeout=api_request_task.api_param.timeout
                    )
                case "POST":
                    # json 和 data 只能传一个,否则会报错
                    if api_request_task.api_param.data and api_request_task.api_param.json:
                        raise ValueError("POST请求中，json和data参数只能传一个")
                    res = await api_client.post(
                        url=api_request_task.api_param.full_url,
                        params=api_request_task.api_param.params,
                        headers=api_request_task.api_param.headers,
                        json=api_request_task.api_param.json,
                        data=api_request_task.api_param.data,
                        timeout=api_request_task.api_param.timeout
                    )
            end_time = time.time()
            api_request_task.time_cost = end_time - start_time  # 计算接口总耗时
            api_request_task.res = res
            # 执行后处理函数
            if api_request_task.format_res_fn:
                api_request_task.format_res_fn(api_request_task)
        except Exception as e:
            print("HTTP请求异常：", e)
