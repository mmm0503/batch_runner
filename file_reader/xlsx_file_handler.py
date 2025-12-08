from typing import List, override, Any

import openpyxl
from openpyxl import utils
from openpyxl.styles import PatternFill
from openpyxl.worksheet.worksheet import Worksheet

from batch_data_types.xslx_types import XlsxFormatCelSuccessOption
from file_reader.file_handler import FileHandler

from copy import deepcopy


class XlsxFileHandler(FileHandler):
    _allowed_extensions = ['xlsx', 'xls']
    __workbook: openpyxl.Workbook
    __current_sheet: Worksheet

    __content_row_start_index: int

    def __init__(self,
                 file_path: str,
                 is_create=False,
                 default_sheet_name="sheet1"
                 ) -> None:
        super().__init__(file_path)
        # 如果 is_create 为 True，则创建一个新的工作簿，否则加载现有的工作簿
        if is_create:
            self.__workbook = openpyxl.Workbook()
            self.__current_sheet = self.__workbook.active
            self.__current_sheet.title = default_sheet_name
        else:
            self.__workbook = openpyxl.load_workbook(file_path)
            # 默认读取第一个 sheet
            sheets = self.__workbook.sheetnames
            if sheets:
                self.__current_sheet = self.__workbook[sheets[0]]

    def __get_current_sheet(self) -> Worksheet:
        return self.__current_sheet

    def get_deepcopy_workbook(self) -> openpyxl.Workbook:
        return deepcopy(self.__workbook)

    def get_deepcopy_current_sheet(self) -> Worksheet:
        return deepcopy(self.__current_sheet)

    def get_sheet_names(self) -> list[str]:
        return self.__workbook.sheetnames

    def change_sheet(self, sheet_name: str) -> bool:
        """切换当前工作表到指定的 sheet_name。如果切换成功，返回 True，否则返回 False。"""
        if sheet_name in self.__workbook.sheetnames:
            self.__current_sheet = self.__workbook[sheet_name]
            return True
        else:
            print(f"change_sheet()报错：工作表 {sheet_name} 不存在")
            return False

    def set_content(self, content_list: list[Any]):
        """设置当前工作表的内容为 content_list。"""
        sheet = self.__get_current_sheet()
        # 清空现有内容
        sheet.delete_rows(1, sheet.max_row)
        # 将新的内容写入工作表
        for row in content_list:
            sheet.append(row)

    @override
    def read_handle(self) -> list[dict]:
        """读取 XLSX 文件内容，并将其保存到 content_list 属性中。"""
        data = self.__read_xlsx()
        if isinstance(data, list):  # 如果是列表，则直接赋值
            self.content_list = data
        else:
            print(f"read()报错：XLSX 文件内容格式不正确，必须是列表")
            self.content_list = []
        return self.content_list

    def __read_xlsx(self) -> list[dict]:
        '''
        读取 XLSX 文件，返回包含所有行的列表，每行是一个字典。
        '''
        data = []
        sheet = self.__get_current_sheet()
        for row in sheet.iter_rows(values_only=True):
            data.append(list(row))
        return data

    def format_sheet_cel_success(self, xlsx_format_options: List[XlsxFormatCelSuccessOption] = None):
        '''
        根据指定的格式化选项，对工作表中的单元格进行格式化。
        通常用于根据某些条件（如成功或失败）来改变单元格的背景颜色。
        :param xlsx_format_options: 可以根据某列的值是否满足某个条件来设置单元格的背景颜色为绿色（成功）或红色（失败）。
        '''
        sheet = self.__get_current_sheet()
        if xlsx_format_options:
            for o in xlsx_format_options:
                format_key = o.format_key
                format_key_name = o.format_key_name
                start_index = o.start_index or 2
                is_success_fn = o.is_success_fn

                # 如果没有设置format_key，那么从format_key_name中寻找
                if not format_key and format_key_name:
                    # 根据列名找到对应的列字母
                    for col in range(1, sheet.max_column + 1):
                        cell_value = sheet.cell(row=1, column=col).value
                        if cell_value == format_key_name:
                            format_key = utils.get_column_letter(col)
                            break

                # 如果没有找到格式化列，跳过
                if not format_key:
                    continue

                for row in range(start_index, sheet.max_row + 1):
                    cell = f"{format_key}{row}"
                    cell_value = sheet[cell].value
                    if is_success_fn:
                        if is_success_fn(cell_value):
                            sheet[cell].fill = PatternFill(fill_type='solid', fgColor='90EE90')  # 背景色为浅绿色
                        else:
                            sheet[cell].fill = PatternFill(fill_type='solid', fgColor='FFB6C1')  # 背景色为浅红色

    @override
    def write_handle(self, writer_file_path: str = None, **kwargs):
        '''
        将数据写入 XLSX 文件。
        :param writer_file_path : 文件路径, 如果为 None，则覆盖原文件
        '''
        if writer_file_path is None:
            writer_file_path = self._file_path

        workbook = self.__workbook
        workbook.save(writer_file_path)
