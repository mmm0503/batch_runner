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
        {"label": "跑批是否成功", "key": "task_is_success"},
        {"label": "跑批结果是否符合预期", "key": "format_data_is_success"},
        {"label": "跑批响应格式化后结果", "key": "format_data"},
        {"label": "跑批响应原始结果", "key": "res"},
    ]

    __xlsx_header_row_list = []
    __xlsx_content_row_list = []

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
        self.__reader_xlsx_data()

        # 2: 请求前处理
        # 追加 标题列
        self._format_result_to_header()

        # 构建请求任务列表
        api_request_task_list = self._get_api_request_task_list()

        # 并发切片列表
        task_chunk_list = list(chunked(api_request_task_list, self.__concurrency))
        # 并发切片content
        content_chunk_list = list(chunked(self.__xlsx_content_row_list, self.__concurrency))
        # 切片后的请求总数
        total_count = len(task_chunk_list)

        # 初始化httpx处理类
        httpx_handler = HttpxHandler()
        # 3: 切片并发处理请求
        for task_chunk_index, task_chunk in enumerate(task_chunk_list):
            # 构建协程列表并执行
            await httpx_handler.async_send_api_task_list(task_chunk)

            # 4: 请求后处理
            for task_index, task in enumerate(task_chunk):
                row_data = content_chunk_list[task_chunk_index][task_index]
                self.post_processing_task(task=task, row_data=row_data)

            # 5 xlsx处理
            self.post_processing_xlsx()

            # 5: 每跑一次，保存一次
            self.__xlsx_file_handler.write_handle(self.__write_file_path)

            # 每次请求间隔时间, 单位秒
            await asyncio.sleep(self.__sleep_time)
            # 进度打印
            print(f"并发量：{self.__concurrency}, 第 {task_chunk_index} / {total_count - 1} 批次请求处理完....")

        print("跑批结束")
        self.show_success_rate()

    # 计算成功率
    def show_success_rate(self):
        # 总行数
        total_rows = len(self.__xlsx_content_row_list)
        # 成功行数
        success_rows = 0
        for row_data in self.__xlsx_content_row_list:
            is_success = self.get_cell_value_by_header_name(row_data=row_data, header_name="跑批是否成功", )
            if is_success:
                success_rows += 1
        success_rate = (success_rows / total_rows) * 100 if total_rows > 0 else 0
        print(f"成功行数: {success_rows}/{total_rows}, 成功率: {success_rate:.2f}%")

    def post_processing_task(self, task: ApiRequestTask, row_data: list):
        '''请求后处理任务'''
        # 如果任务已经成功，跳过格式化
        if task.task_is_success:
            return

        # 格式化接口返回结果
        self.__format_res_fn(task)

        # 追加 结果列
        self._format_result_to_content(task=task, row_data=row_data)

    def post_processing_xlsx(self):
        # 设置xlsx内容
        self.__xlsx_file_handler.set_content(content_list=[
            *self.__xlsx_header_row_list,
            *self.__xlsx_content_row_list
        ])

        # 格式化xlsx结果单元格颜色
        self.__xlsx_file_handler.format_sheet_cel_success(xlsx_format_options=[
            XlsxFormatCelSuccessOption(
                format_key_name="跑批结果是否符合预期",
                is_success_fn=lambda cell_value: cell_value is True,
                start_index=self.__content_row_start_index + 1
            ),
            XlsxFormatCelSuccessOption(
                format_key_name="跑批是否成功",
                is_success_fn=lambda cell_value: cell_value is True,
                start_index=self.__content_row_start_index + 1
            )
        ])

    def _get_api_request_task_list(self) -> list[ApiRequestTask]:
        api_request_task_list: list[ApiRequestTask] = [
            ApiRequestTask(
                api_param=self.__create_api_task_params_fn(
                    data_row=row_data,
                    header_row=(self.__xlsx_header_row_list)
                ),
                origin_data=row_data,
                task_is_success=self.get_task_is_success(row_data, self.__xlsx_header_row_list)
            )
            for row_index, row_data in enumerate(self.__xlsx_content_row_list)
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

    def __reader_xlsx_data(self):
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
        self.__xlsx_header_row_list = deepcopy(xlsx_header_row)
        self.__xlsx_content_row_list = deepcopy(xlsx_content_rows)

    def _format_result_to_header(self):
        header_row = self.__xlsx_header_row_list
        ''' 在标题行中添加结果列 '''
        h_0: AppendHeaderType = self.__append_header[0]
        is_includes = h_0['label'] in header_row[0]
        # 避免重复添加
        if not is_includes:
            append_header_row = [h['label'] for h in self.__append_header]
            header_row[0] = [*header_row[0], *append_header_row]
        return header_row

    def _format_result_to_content(self, task: ApiRequestTask, row_data: list):
        '''在内容行中添加结果列'''
        header_row: list = self.__xlsx_header_row_list
        # 根据header头顺序，添加 结果列
        for h in self.__append_header:
            # 获取当前h的索引
            idx = header_row[0].index(h['label'])
            append_value = task[h['key']]
            # 如果是dict or list类型，转换成字符串
            if isinstance(append_value, dict) or isinstance(append_value, list):
                append_value = str(append_value)

            if len(row_data) < len(header_row[0]):
                row_data.append(append_value)
            else:
                row_data[idx] = append_value

    def get_cell_value_by_header_name(self, row_data: list, header_name: str) -> Any:
        '''根据标题名称获取行数据对应的值'''
        try:
            header_row: list = self.__xlsx_header_row_list
            header_index = header_row[0].index(header_name)
            if header_index >= len(row_data):
                return None
            return row_data[header_index]
        except ValueError:
            return None

    def get_task_is_success(self, row_data: list, header_row: list) -> bool:
        '''根据行数据获取任务是否成功'''
        return self.get_cell_value_by_header_name(
            row_data=row_data,
            header_name="跑批是否成功",
        )
