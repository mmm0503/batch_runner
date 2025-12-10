import json

from typing_extensions import override

from file_reader.file_handler import FileHandler


class JsonFileHandler(FileHandler):
    _allowed_extensions = ['json']

    def __init__(self, file_path: str) -> None:
        super().__init__(file_path)

    @override
    def read_handle(self) -> list | dict:
        """读取 JSONL 文件内容，并将其保存到 content_list 属性中。"""
        data = self._read_json()
        # 如果是列表 or 字典，则直接赋值
        if isinstance(data, list) or isinstance(data, dict):
            self.__content_list = data
        else:
            print(f"read()报错：JSONL 文件内容格式不正确，必须是dict、list")
            self.__content_list = []
        return self.__content_list

    def _read_json(self, encoding='utf-8') -> dict | list:
        """读取 JSON 文件，返回字典。"""
        try:
            with open(self._file_path, 'r', encoding=encoding) as file:
                # 判断文件内容是否为空
                file_content = file.read().strip()
                if not file_content:
                    print(f"{self._file_path} 文件内容为空，返回空字典")
                    return {}
                file.seek(0)  # 重置文件指针到开头
                return json.load(file)
        except Exception as e:
            print(f"_read_json()报错：找不到文件或读取文件出错: {e}")
            return {}

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
            # write_data 必须是列表 or 字典
            if not isinstance(self.__content_list, list) and not isinstance(self.__content_list, dict):
                print("write_jsonl()报错：write_data 必须是列表或字典类型")
                return False
            with open(writer_file_path, write_type, encoding=encoding) as file:
                json.dump(self.__content_list, file, ensure_ascii=False, indent=4)
            return True

        except Exception as e:
            print(f"write_jsonl()报错：写入文件出错: {e}")
            return False
