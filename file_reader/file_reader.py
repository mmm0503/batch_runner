from abc import ABC, abstractmethod
from typing import Any


class FileReader(ABC):
    file_path: str
    # 保存读取的内容
    content_list: list[dict[str, Any]] = []
    # 允许读取的文件后缀
    allowed_extensions: list[str] = []

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        if not self.validate_reader_file():
            raise ValueError(f"该文件格式不被支持: {file_path}。 允许的格式有: {self.allowed_extensions}")

    @abstractmethod
    def read(self) -> list[dict[str, Any]]:
        '''
        读取文件内容并返回一个包含字典的列表，每个字典表示文件中的一条记录。
        读取的值，保存到 content_list 属性中。
        '''
        pass

    def validate_reader_file(self) -> bool:
        '''
        验证文件格式是否正确。从文件路径中提取文件后缀，并检查是否在 allowed_extensions 列表中。
        返回 True 如果格式正确，否则返回 False。
        '''
        extension = self.file_path.split('.')[-1].lower()
        return extension in self.allowed_extensions

    def get_content(self) -> list[dict[str, Any]]:
        '''
        返回读取的内容列表。
        '''
        return self.content_list

    # 判断读取的内容是否为空
    def is_content_empty(self) -> bool:
        '''
        检查 content_list 是否为空。
        返回 True 如果为空，否则返回 False。
        '''
        return len(self.content_list) == 0
