from dataclasses import dataclass
from typing import Optional, Callable


@dataclass
class XlsxFormatCelSuccessOption:  # xlsx_format_option
    format_key: str = None  # 指定格式化的列 如：'A'
    format_key_name: str = None  # 指定格式化的列名称,如：'跑批结果'， 有format_key时优先使用format_key
    start_index: int = None  # 起始行数，默认从第二行开始
    is_success_fn: Optional[Callable] = None  # 判断值是否成功的函数：(cell_value) -> bool
