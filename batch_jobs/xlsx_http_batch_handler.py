import asyncio
from copy import deepcopy
from typing import Optional, Callable, Any

from more_itertools import chunked

from batch_data_types.api_types import ApiRequestTask, ApiRequestParams
from batch_data_types.xslx_types import XlsxFormatCelSuccessOption
from file_reader.xlsx_file_handler import XlsxFileHandler
from network.httpx_client import HttpxClient
from network.httpx_handler import HttpxHandler


class XlsxHttpBatchHandler:
    '''
    Xlsx跑批类
    '''
    __file_path: str  # xlsx文件路径
    __write_file_path: str = None  # 写入结果的xlsx文件路径，默认覆盖原文件
    __sheet_name: Optional[str] = None  # 工作表名称，默认第一个工作表
    __xlsx_file_handler: XlsxFileHandler

    __content_row_start_index: int = 1  # 内容行起始索引，默认第一行是标题行，内容从第二行开始
    __concurrency: int = 1  # 并发数
    __sleep_time: int = 1  # 每次请求间隔时间

    __create_api_task_params_fn: Optional[Callable] = None  # 根据原始数据row创建 ApiRequestParams 的函数
    __format_res_fn: Optional[Callable] = None  # 格式化接口返回结果的函数

    def __init__(self,
                 file_path: str,  # xlsx文件路径
                 write_file_path: str = None,  # 写入结果的xlsx文件路径，默认覆盖原文件
                 sheet_name: str = None,  # 工作表名称，默认第一个工作表
                 content_row_start_index: int = 1,  # 内容行起始索引，默认第一行是标题行，内容从第二行开始
                 concurrency: int = 1,  # 并发数
                 sleep_time: int = 1,  # 每次请求间隔时间，单位秒
                 create_api_task_params_fn: Callable[[list, list], ApiRequestParams] = None,
                 # 根据原始数据row创建 ApiRequestParams 的函数
                 format_res_fn: Callable = None,  # 格式化接口返回结果的函数
                 ):
        self.__file_path = file_path
        self.__write_file_path = write_file_path or file_path
        self.__sheet_name = sheet_name
        self.__content_row_start_index = content_row_start_index
        self.__create_api_task_params_fn = create_api_task_params_fn
        self.__format_res_fn = format_res_fn
        self.__concurrency = concurrency
        self.__sleep_time = sleep_time
        self.__xlsx_file_handler = XlsxFileHandler(self.__file_path)  # 初始化xlsx文件处理类

    async def batch_run(self):
        '''开始跑批'''

        # 1: 读取xlsx文件，获取原始数据列表
        xlsx_header_row_list, xlsx_content_row_list = self.__reader_xlsx_data()

        # 2: 构建ApiRequestTask列表
        api_request_task_list: list[ApiRequestTask] = self._get_api_request_task_list(
            xlsx_header_row_list=xlsx_header_row_list,
            xlsx_content_row_list=xlsx_content_row_list
        )

        task_chunk_list = list(chunked(api_request_task_list, self.__concurrency))  # 并发切片列表
        total_count = len(task_chunk_list)  # 切片后的请求总数
        completed_count = 0  # 已完成请求数

        httpx_handler = HttpxHandler()  # 初始化httpx处理类
        # 3: 切片并发处理请求
        for task_chunk in task_chunk_list:
            # 构建协程列表并执行
            await httpx_handler.async_send_api_task_list(task_chunk)

            # 4: 请求后处理
            # 格式化接口返回结果
            for api_request_task in task_chunk:
                # 格式化接口返回结果
                if self.__format_res_fn:
                    self.__format_res_fn(api_request_task)

            # 5: 写入结果到xlsx文件
            self.write_xlsx_file(
                xlsx_header_row_list=xlsx_header_row_list,
                api_request_task_list=api_request_task_list
            )

            # 每次请求间隔时间, 单位秒
            if self.__sleep_time > 0:
                await asyncio.sleep(self.__sleep_time)

            print(f"并发量：{self.__concurrency}, 第 {completed_count} / {total_count - 1} 批次请求处理完....")
            completed_count += 1

        print("跑批结束")

    def write_xlsx_file(self, xlsx_header_row_list: list, api_request_task_list: list[ApiRequestTask]):
        '''写入结果到xlsx文件'''
        # 格式化标题行，添加结果列
        xlsx_header_row_list = self._format_result_to_header(xlsx_header_row_list)
        # 构建写入内容列表
        xlsx_content_row_list = []
        for api_request_task in api_request_task_list:
            xlsx_content_row_list.append(self._format_row_list([
                *deepcopy(api_request_task.origin_data),

                api_request_task.time_cost,  # 请求耗时（秒）
                api_request_task.format_data_is_success,  # 响应格式化后结果是否符合预期

                api_request_task.format_data,  # 响应格式化后结果
                api_request_task.res,  # 响应原始结果
            ]))
        # 设置xlsx内容
        self.__xlsx_file_handler.set_content(content_list=[*xlsx_header_row_list, *xlsx_content_row_list])
        # 格式化xlsx结果单元格颜色
        self.__xlsx_file_handler.format_sheet_cel_success(xlsx_format_options=[
            XlsxFormatCelSuccessOption(
                format_key_name="跑批结果是否符合预期",
                is_success_fn=lambda cell_value: cell_value is True,
                start_index=self.__content_row_start_index + 1
            )
        ])
        # 写入xlsx文件
        self.__xlsx_file_handler.write_handle(self.__write_file_path)

    def _get_api_request_task_list(self, xlsx_header_row_list: list, xlsx_content_row_list: list) -> list[
        ApiRequestTask]:
        api_request_task_list: list[ApiRequestTask] = [
            ApiRequestTask(
                api_param=deepcopy(self.__create_api_task_params_fn(
                    row=deepcopy(row_data),
                    header_row=deepcopy(xlsx_header_row_list)
                )),
                origin_data=deepcopy(row_data)
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
        xlsx_header_row = []  # 标题行
        xlsx_content_rows = []  # 内容行
        if self.__content_row_start_index:
            xlsx_header_row = xlsx_data[0:self.__content_row_start_index]
            xlsx_content_rows = xlsx_data[self.__content_row_start_index:]
        return [deepcopy(xlsx_header_row), deepcopy(xlsx_content_rows)]

    def _format_result_to_header(self, header_row: list) -> list:
        if self.__content_row_start_index == 1:
            '''在标题行中添加结果列'''
            header_row = deepcopy(header_row)
            append_header = [
                "跑批请求耗时（秒）",
                "跑批结果是否符合预期",

                "跑批响应格式化后结果",
                "跑批响应原始结果",
            ]
            # 判断是否已经存在结果列，避免重复添加， 这里简单判断一下第一个结果列是否存在
            if "跑批接口请求是否成功" not in header_row[0]:
                header_row[0] = [
                    *header_row[0],
                    *append_header
                ]
            return header_row
        else:
            return header_row
