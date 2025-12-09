from dataclasses import dataclass
from typing import Optional, Any, Callable


@dataclass
class ApiRequestParams:  # api_request_params
    full_url: str
    methods: str
    params: Optional[Any] = None
    headers: Optional[Any] = None
    data: Optional[Any] = None
    json: Optional[Any] = None
    timeout: Optional[float] = 10.0


@dataclass
class ApiRequestTask:  # api_request_task
    api_param: ApiRequestParams  # 请求参数
    origin_data: Optional[Any]  # 原始数据

    time_cost: Optional[float] = None  # 请求耗时
    res: Optional[Any] = None  # 请求结果

    format_data: Optional[Any] = None  # 格式化后的结果
    format_data_is_success: bool = None  # 格式化后，判断res是符合预期

    task_is_success: bool = False  # 任务是否成功完成

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)
