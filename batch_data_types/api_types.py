from dataclasses import dataclass
from typing import Optional, Any, Callable

from pydantic.v1.dataclasses import Dataclass


@dataclass
class ApiRequestParams:
    full_url: str
    methods: str
    params: Optional[Any] = None
    headers: Optional[Any] = None
    data: Optional[Any] = None
    timeout: Optional[float] = 10.0


@dataclass
class ApiRequestTask:
    api_param: ApiRequestParams  # 请求参数
    origin_data: Optional[Any]  # 原始数据
    res: Optional[Any] = None  # 请求结果
    time_cost: Optional[float] = None  # 请求耗时
    is_success: bool = False  # 请求是否成功
    error_message: Optional[str] = None  # 错误信息
    format_data: Optional[Any] = None  # 格式化后的结果
    format_res_fn: Optional[Callable[[Any, 'ApiRequestTask'], Any]] = None  # 结果格式化函数


# 批量请求任务的 入参类型
@Dataclass
class ApiBatchTask:
    origin_batch_list: list[ApiRequestTask]  # 请求类型列表
    concurrency: int = 1  # 并发数
    sleep_time: float = 2.0  # 每次请求间隔时间，单位秒
    callback_trigger_count: int = 0  # 请求到一定次数，触发一次回调函数
    all_complete_callback: Optional[Callable[[list[Any]], None]] = None  # 请求全部结束后的回调函数,通常是保存结果
