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

    # 获取任务项模板入参
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

    # 构建HTTP请求协程
    async def get_http_task(
            self,
            task_item=None
    ):
        task_param = task_item.get("taskParam", {})
        # 构建要执行的协程（未执行）
        full_url = self.base_url + task_param.get("url", "")
        request_headers = task_param.get("headers", "") or self.headers
        elapsed = task_param.get("default_timeout", "") or self.default_timeout
        params = task_param.get("params", {})
        data = task_param.get("data", {})
        format_res_fn = task_param.get("format_res_fn", None)

        # 方法大小写一致
        methods = task_param["methods"].upper()

        # 定义异步请求协程
        # start_time = time.time()
        try:
            resp = None
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
            return resp
        except BaseException as e:
            print("HTTP请求异常：", e)
            return None
            #     end_time = time.time()
            #     # 返回结果
            #     if format_res_fn:
            #         return format_res_fn(result=resp, time_cost=end_time - start_time, task_item=task_item)
            #     return {
            #         **task_item,
            #         "result": resp,
            #         "time_cost": end_time - start_time
            #     }
            # except BaseException as e:
            #     print("HTTP请求异常：", e)
            #     end_time = time.time()
            #     if format_res_fn:
            #         return format_res_fn(result=None, time_cost=end_time - start_time, task_item=task_item)
            #     return {
            #         **task_item,
            #         "result": None,
            #         "time_cost": end_time - start_time
            #     }
