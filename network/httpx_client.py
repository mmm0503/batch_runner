import ssl
import copy
import httpx

from batch_data_types.api_types import ApiRequestTask, ApiRequestParams

context = ssl.create_default_context()
# Python 3.10 以上，OpenSSL 3.0 的情况
if hasattr(ssl, "OP_LEGACY_SERVER_CONNECT"):
    context.options |= ssl.OP_LEGACY_SERVER_CONNECT

api_client = httpx.AsyncClient(verify=context)


class HttpxClient:

    # 构建HTTP请求协程
    async def create_http_task(self, api_request_task: ApiRequestTask):
        methods = api_request_task.api_param.methods.upper()
        try:
            if methods == "GET":
                return await api_client.get(
                    url=api_request_task.api_param.full_url,
                    params=api_request_task.api_param.params,
                    headers=api_request_task.api_param.headers,
                    timeout=api_request_task.api_param.timeout
                )
            elif methods == "POST":
                # json 和 data 只能传一个,否则会报错
                if api_request_task.api_param.data and api_request_task.api_param.json:
                    raise ValueError("POST请求中，json和data参数只能传一个")

                return await api_client.post(
                    url=api_request_task.api_param.full_url,
                    params=api_request_task.api_param.params,
                    headers=api_request_task.api_param.headers,
                    json=api_request_task.api_param.data,
                    data=api_request_task.api_param.data,
                    timeout=api_request_task.api_param.timeout
                )
            else:
                raise ValueError(f"找不到方法类型: {methods}")
        except Exception as e:
            print("HTTP请求异常：", e)
            return None
