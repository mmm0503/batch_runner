from abc import ABC, abstractmethod
from typing import Any


class FileHandler(ABC):
    # 允许读取的文件后缀
    _allowed_extensions: list[str] = []
    _file_path: str
    # 保存读取的内容
    _content_list: list[dict[str, Any]] = []

    def __init__(self, file_path: str) -> None:
        self._file_path = file_path
        if not self.validate_reader_file():
            raise ValueError(f"该文件格式不被支持: {file_path}。 允许的格式有: {self._allowed_extensions}")

    def get_allowed_extensions(self) -> list[str]:
        '''
        返回允许的文件后缀列表。
        '''
        return self._allowed_extensions

    def get_content(self) -> list[dict[str, Any]]:
        '''
        返回读取的内容列表。
        '''
        return self._content_list

    def validate_reader_file(self) -> bool:
        '''
        验证文件格式是否正确。从文件路径中提取文件后缀，并检查是否在 allowed_extensions 列表中。
        返回 True 如果格式正确，否则返回 False。
        '''
        extension = self._file_path.split('.')[-1].lower()
        return extension in self._allowed_extensions

    # 判断读取的内容是否为空
    def is_content_empty(self) -> bool:
        '''
        检查 content_list 是否为空。
        返回 True 如果为空，否则返回 False。
        '''
        return len(self._content_list) == 0

    def set_content(self, content_list: list[dict[str, Any]]) -> None:
        '''
        设置 content_list 属性的值。
        :param content_list: 要设置的内容列表
        '''
        self._content_list = content_list

    @abstractmethod
    def read_handle(self) -> list[dict[str, Any]]:
        '''
        读取文件内容并返回一个包含字典的列表，每个字典表示文件中的一条记录。
        读取的值，保存到 content_list 属性中。
        '''
        pass

    @abstractmethod
    def write_handle(self, writer_file_path: str, write_type='w', encoding='utf-8') -> bool:
        '''
        将数据写入文件。
        :param writer_file_path : 文件路径
        :param write_type: 写入模式，'w' 覆盖写入，'a' 追加写入
        :param encoding: 文件编码
        :return: 写入成功返回 True，失败返回 False
        '''
        pass
