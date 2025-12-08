import json

from typing_extensions import override

from file_reader.file_handler import FileHandler


class JSONLFileHandler(FileHandler):
    _allowed_extensions = ['jsonl']

    def __init__(self, file_path: str) -> None:
        super().__init__(file_path)

    @override
    def read_handle(self) -> list[dict]:
        """读取 JSONL 文件内容，并将其保存到 content_list 属性中。"""
        data = self.read_jsonl()

        if isinstance(data, list):  # 如果是列表，则直接赋值
            self.__content_list = data
        else:
            print(f"read()报错：JSONL 文件内容格式不正确，必须是字典列表")
            self.__content_list = []
        return self.__content_list

    def read_jsonl(self, encoding='utf-8') -> list[dict]:
        """读取 JSONL 文件，返回包含所有行的列表，每行是一个字典。"""
        try:
            file_data_list = []
            with open(self._file_path, 'r', encoding=encoding) as file:
                for line in file:
                    file_data_list.append(json.loads(line.strip()))
            return file_data_list

        except Exception as e:
            print(f"read_jsonl()报错：找不到文件或读取文件出错: {e}")
            return []

    @override()
    def write_handle(self,
                     writer_file_path=None,
                     write_type='w',
                     encoding='utf-8'
                     ) -> bool:
        """
        将字典列表写入 JSONL 文件，每个字典作为一行。
        :param file_path: 文件路径
        :param write_data: 要写入的字典列表
        :param write_type: 写入模式，'w' 覆盖写入，'a' 追加写入
        :param encoding: 文件编码
        :return: 写入成功返回 True，失败返回 False
        """

        try:
            if writer_file_path is None:
                writer_file_path = self._file_path
            # write_data 必须是列表
            if not isinstance(self.__content_list, list):
                print("write_jsonl()报错：write_data 必须是列表类型")
                return False

            with open(writer_file_path, write_type, encoding=encoding) as file:
                for entry in self.__content_list:
                    file.write(json.dumps(entry, ensure_ascii=False) + '\n')
            return True

        except Exception as e:
            print(f"write_jsonl()报错：写入文件出错: {e}")
            return False
