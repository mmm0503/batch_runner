from typing import List, override, Any

import openpyxl
from openpyxl import utils
from openpyxl.styles import PatternFill
from openpyxl.worksheet.worksheet import Worksheet

from batch_data_types.xslx_types import XlsxFormatCelSuccessOption
from file_reader.file_handler import FileHandler


class XlsxFileHandler(FileHandler):
    allowed_extensions = ['xlsx', 'xls']
    workbook: openpyxl.Workbook
    current_sheet: Worksheet

    def __init__(self, reader_file_path: str, is_create=False, default_sheet_name="sheet1") -> None:
        super().__init__(reader_file_path)
        # 如果 is_create 为 True，则创建一个新的工作簿，否则加载现有的工作簿
        if is_create:
            self.workbook = openpyxl.Workbook()
            self.current_sheet = self.workbook.active
            self.current_sheet.title = default_sheet_name
        else:
            self.workbook = openpyxl.load_workbook(reader_file_path)
            # 默认读取第一个 sheet
            sheets = self.workbook.sheetnames
            if sheets:
                self.current_sheet = self.workbook[sheets[0]]

    def get_workbook(self) -> openpyxl.Workbook:
        return self.workbook

    def get_current_sheet(self) -> Worksheet:
        return self.current_sheet

    def get_sheet_names(self) -> list[str]:
        return self.workbook.sheetnames

    def change_sheet(self, sheet_name: str) -> bool:
        """切换当前工作表到指定的 sheet_name。如果切换成功，返回 True，否则返回 False。"""
        if sheet_name in self.workbook.sheetnames:
            self.current_sheet = self.workbook[sheet_name]
            return True
        else:
            print(f"change_sheet()报错：工作表 {sheet_name} 不存在")
            return False

    def set_content(self, content_list: list[Any]):
        """设置当前工作表的内容为 content_list。"""
        sheet = self.get_current_sheet()
        # 清空现有内容
        sheet.delete_rows(1, sheet.max_row)
        # 将新的内容写入工作表
        for row in content_list:
            sheet.append(row)

    @override
    def read_handle(self) -> list[dict]:
        """读取 XLSX 文件内容，并将其保存到 content_list 属性中。"""
        data = self.read_xlsx()
        if isinstance(data, list):  # 如果是列表，则直接赋值
            self.content_list = data
        else:
            print(f"read()报错：XLSX 文件内容格式不正确，必须是列表")
            self.content_list = []
        return self.content_list

    def read_xlsx(self) -> list[dict]:
        data = []
        sheet = self.get_current_sheet()
        for row in sheet.iter_rows(values_only=True):
            data.append(list(row))
        return data

    def format_sheet_cel_success(self, xlsx_format_options: List[XlsxFormatCelSuccessOption] = None):
        '''
        根据指定的格式化选项，对工作表中的单元格进行格式化。
        通常用于根据某些条件（如成功或失败）来改变单元格的背景颜色。
        :param xlsx_format_options: 可以根据某列的值是否满足某个条件来设置单元格的背景颜色为绿色（成功）或红色（失败）。
        '''
        sheet = self.get_current_sheet()
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
        workbook = self.workbook
        workbook.save(writer_file_path or self.reader_file_path)
