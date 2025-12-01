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
                return await api_client.get(**api_request_task.api_param)
            elif methods == "POST":
                return await api_client.post(**api_request_task.api_param)
            else:
                raise ValueError(f"找不到方法类型: {methods}")
        except BaseException as e:
            print("HTTP请求异常：", e)
            return None
