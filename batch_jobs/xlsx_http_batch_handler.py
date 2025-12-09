import asyncio
from dataclasses import dataclass
from copy import deepcopy
from typing import Optional, Callable, Any

from more_itertools import chunked

from batch_data_types.api_types import ApiRequestTask, ApiRequestParams
from batch_data_types.xslx_types import XlsxFormatCelSuccessOption
from file_reader.xlsx_file_handler import XlsxFileHandler
from network.httpx_handler import HttpxHandler


@dataclass
class AppendHeaderType:
    label: str
    key: str


class XlsxHttpBatchHandler:
    '''
    Xlsx跑批类
    '''
    # xlsx文件路径
    __file_path: str
    # 写入结果的xlsx文件路径，默认覆盖原文件
    __write_file_path: str = None
    # 工作表名称，默认第一个工作表
    __sheet_name: Optional[str] = None
    __xlsx_file_handler: XlsxFileHandler

    # 内容行起始索引，默认第一行是标题行，内容从第二行开始
    __content_row_start_index: int = 1
    # 并发数
    __concurrency: int = 1
    # 每次请求间隔时间
    __sleep_time: int = 1

    # 根据原始数据row创建 ApiRequestParams 的函数
    __create_api_task_params_fn: Optional[Callable] = None
    # 格式化接口返回结果的函数
    __format_res_fn: Optional[Callable] = None

    # 要追加的结果列
    __append_header: list[AppendHeaderType] = [
        {"label": "跑批请求耗时（秒）", "key": "time_cost"},
        {"label": "跑批结果是否符合预期", "key": "format_data_is_success"},
        {"label": "跑批响应格式化后结果", "key": "format_data"},
        {"label": "跑批响应原始结果", "key": "res"},
    ]

    def __init__(self,
                 # xlsx文件路径
                 file_path: str,
                 # 写入结果的xlsx文件路径，默认覆盖原文件
                 write_file_path: str = None,
                 # 工作表名称，默认第一个工作表
                 sheet_name: str = None,
                 # 内容行起始索引，默认第一行是标题行，内容从第二行开始
                 content_row_start_index: int = 1,
                 # 并发数
                 concurrency: int = 1,
                 # 每次请求间隔时间，单位秒
                 sleep_time: int = 1,
                 # 根据原始数据row创建 ApiRequestParams 的函数
                 create_api_task_params_fn: Callable[[list, list], ApiRequestParams] = None,
                 # 格式化接口返回结果的函数
                 format_res_fn: Callable = None,
                 ):
        self.__file_path = file_path
        self.__write_file_path = write_file_path or file_path
        self.__sheet_name = sheet_name
        self.__content_row_start_index = content_row_start_index
        self.__create_api_task_params_fn = create_api_task_params_fn
        self.__format_res_fn = format_res_fn or self.__default_format_res_fn
        self.__concurrency = concurrency
        self.__sleep_time = sleep_time
        # 初始化xlsx文件处理类
        self.__xlsx_file_handler = XlsxFileHandler(self.__file_path)

    def __default_format_res_fn(self):
        '''默认格式化接口返回结果函数'''
        pass

    async def batch_run(self):
        '''开始跑批'''

        # 1: 读取xlsx文件，获取原始数据列表
        xlsx_header_row_list, xlsx_content_row_list = self.__reader_xlsx_data()

        # 2: 请求前处理
        # 追加 标题列
        self._format_result_to_header(xlsx_header_row_list)
        # 构建请求任务列表
        api_request_task_list: list[ApiRequestTask] = self._get_api_request_task_list(
            xlsx_header_row_list=xlsx_header_row_list,
            xlsx_content_row_list=xlsx_content_row_list
        )

        # 并发切片列表
        task_chunk_list = list(chunked(api_request_task_list, self.__concurrency))
        # 并发切片content
        content_chunk_list = list(chunked(xlsx_content_row_list, self.__concurrency))
        # 切片后的请求总数
        total_count = len(task_chunk_list)

        # 初始化httpx处理类
        httpx_handler = HttpxHandler()
        # 3: 切片并发处理请求
        for task_chunk_index, task_chunk in enumerate(task_chunk_list):
            # 构建协程列表并执行
            await httpx_handler.async_send_api_task_list(task_chunk)

            # 4: 请求后处理
            # 格式化接口返回结果
            list(map(self.__format_res_fn, task_chunk))
            # 追加 结果列
            # 当前正在跑的索引
            self._format_result_to_content(
                xlsx_header_row_list,
                content_chunk_list[task_chunk_index],
                task_chunk
            )

            # 设置xlsx内容
            self.__xlsx_file_handler.set_content(content_list=[
                *xlsx_header_row_list,
                *xlsx_content_row_list
            ])

            # 格式化xlsx结果单元格颜色
            self.__xlsx_file_handler.format_sheet_cel_success(xlsx_format_options=[
                XlsxFormatCelSuccessOption(
                    format_key_name="跑批结果是否符合预期",
                    is_success_fn=lambda cell_value: cell_value is True,
                    start_index=self.__content_row_start_index + 1
                )
            ])

            # 5: 每跑一次，保存一次
            self.__xlsx_file_handler.write_handle(self.__write_file_path)

            # 每次请求间隔时间, 单位秒
            await asyncio.sleep(self.__sleep_time)
            # 进度打印
            print(f"并发量：{self.__concurrency}, 第 {task_chunk_index} / {total_count - 1} 批次请求处理完....")

        print("跑批结束")

    def _get_api_request_task_list(self, xlsx_header_row_list: list, xlsx_content_row_list: list) -> list[
        ApiRequestTask]:
        api_request_task_list: list[ApiRequestTask] = [
            ApiRequestTask(
                api_param=self.__create_api_task_params_fn(
                    data_row=row_data,
                    header_row=(xlsx_header_row_list)
                ),
                origin_data=row_data
            )
            for row_index, row_data in enumerate(xlsx_content_row_list)
        ]
        return api_request_task_list

    def _format_row_list(self, row: list) -> list:
        '''格式化行列表，如果是None，就返回"" '''
        formatted_list = []
        for cell in row:
            if isinstance(cell, dict) or isinstance(cell, list):
                formatted_list.append(str(cell))
            else:
                formatted_list.append(cell)
        return formatted_list

    def __reader_xlsx_data(self) -> list:
        '''读取xlsx文件数据'''
        # 1：确认要读取的sheet
        if self.__sheet_name:
            self.__xlsx_file_handler.change_sheet(self.__sheet_name)
        else:
            # 默认读取第一个sheet
            sheet_names = self.__xlsx_file_handler.get_sheet_names()
            if sheet_names:
                self.__xlsx_file_handler.change_sheet(sheet_names[0])

        # 2：读取xlsx数据
        xlsx_data = self.__xlsx_file_handler.read_handle()
        # 3：分离标题行和内容行
        # 标题行
        xlsx_header_row = []
        # 内容行
        xlsx_content_rows = []
        if self.__content_row_start_index:
            xlsx_header_row = xlsx_data[0:self.__content_row_start_index]
            xlsx_content_rows = xlsx_data[self.__content_row_start_index:]
        return [deepcopy(xlsx_header_row), deepcopy(xlsx_content_rows)]

    def _format_result_to_header(self, header_row: list) -> list:
        ''' 在标题行中添加结果列 '''
        # 只在内容行从第一行开始的情况下，添加结果列
        if self.__content_row_start_index == 1:
            # 复制 原始标题行
            # 判断是否已经添加过结果列，避免重复添加
            h_0: AppendHeaderType = self.__append_header[0]
            is_not_includes = h_0['label'] not in header_row[0]
            if is_not_includes:
                append_header_row = [h['label'] for h in self.__append_header]
                header_row[0] = [*header_row[0], *append_header_row]
            return header_row
        else:
            return header_row

    def _format_result_to_content(self,
                                  header_row: list,
                                  content_row_chunk: list,
                                  task_chunk: list[ApiRequestTask]
                                  ) -> list:
        '''在内容行中添加结果列'''
        for task_index, task in enumerate(task_chunk):
            # 复制 原始数据列
            content_row = content_row_chunk[task_index]
            # 根据header头顺序，添加 结果列
            for h in self.__append_header:
                # 获取当前h的索引
                idx = header_row[0].index(h['label'])
                append_value = task[h['key']]
                # 如果是dict or list类型，转换成字符串
                if isinstance(append_value, dict) or isinstance(append_value, list):
                    append_value = str(append_value)
                if len(content_row) < len(header_row[0]):
                    content_row.append(append_value)
                else:
                    content_row[len(header_row) - len(self.__append_header) + idx] = append_value
        return content_row_chunk
