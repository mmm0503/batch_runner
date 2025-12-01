import time
import httpx
import ssl

context = ssl.create_default_context()
# Python 3.10 以上，OpenSSL 3.0 的情况
if hasattr(ssl, "OP_LEGACY_SERVER_CONNECT"):
    context.options |= ssl.OP_LEGACY_SERVER_CONNECT


class HttpxClient:
    base_url = ""
    headers = {}
    default_timeout = 10
    client = None
    format_res_fn = None

    def __init__(self, base_url=None, headers=None, timeout=10):
        self.base_url = base_url or ""
        self.headers = headers or {}
        self.default_timeout = timeout
        self.client = httpx.AsyncClient(verify=context)

    def get_task_item(
            self,
            url=None,
            methods="GET",
            params=None,
            headers=None,
            data=None,
            format_res_fn=None,
            timeout=None
    ):
        return {
            "taskParam": {
                "url": url,
                "methods": methods,
                "params": params,
                "headers": headers,
                "data": data,
                "format_res_fn": format_res_fn,
                "timeout": timeout
            },
            "result": None,
            "time_cost": None,
            "is_success": False,
            "error_message": None
        }

    def get_http_task(
            self,
            task_item=None
    ):
        # 构建要执行的协程（未执行）
        full_url = self.base_url + task_item["taskParam"]["url"]
        request_headers = task_item["taskParam"]["headers"] or self.headers
        elapsed = task_item["taskParam"]["default_timeout"] or self.default_timeout
        params = task_item["taskParam"]["params"]
        data = task_item["taskParam"]["data"]
        format_res_fn = task_item["taskParam"]["format_res_fn"]

        # 方法大小写一致
        methods = task_item["taskParam"]["methods"].upper()

        # 定义异步请求协程
        async def request_coroutine():
            start_time = time.time()
            try:
                if methods == "GET":
                    resp = await self.client.get(
                        full_url, params=params, headers=request_headers, timeout=elapsed,
                    )
                elif methods == "POST":
                    resp = await self.client.post(
                        full_url, data=data, params=params, headers=request_headers, timeout=elapsed
                    )
                # 你可以继续支持 PUT/DELETE
                else:
                    raise ValueError(f"找不到方法类型: {methods}")
                end_time = time.time()
                # 返回结果
                if format_res_fn:
                    return format_res_fn(result=resp, time_cost=end_time - start_time, task_item=task_item)
                return {
                    **task_item,
                    "result": resp,
                    "time_cost": end_time - start_time
                }
            except BaseException as e:
                print("HTTP请求异常：", e)
                end_time = time.time()
                if format_res_fn:
                    return format_res_fn(result=None, time_cost=end_time - start_time, task_item=task_item)
                return {
                    **task_item,
                    "result": None,
                    "time_cost": end_time - start_time
                }

            # 返回未执行的协程对象
            return request_coroutine
