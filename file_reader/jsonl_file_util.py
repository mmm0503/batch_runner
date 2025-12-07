import json

from typing_extensions import override

from file_reader.file_reader import FileReader


class JSONLFileReader(FileReader):
    allowed_extensions = ['jsonl']

    def __init__(self, file_path: str) -> None:
        super().__init__(file_path)

    @override
    def read(self) -> list[dict]:
        """读取 JSONL 文件内容，并将其保存到 content_list 属性中。"""
        data = self.read_jsonl()

        if isinstance(data, list):  # 如果是列表，则直接赋值
            self.content_list = data
        else:
            print(f"read()报错：JSONL 文件内容格式不正确，必须是字典列表")
            self.content_list = []
        return self.content_list

    def read_jsonl(self, encoding='utf-8') -> list[dict]:
        """读取 JSONL 文件，返回包含所有行的列表，每行是一个字典。"""
        try:
            file_data_list = []
            with open(self.file_path, 'r', encoding=encoding) as file:
                for line in file:
                    file_data_list.append(json.loads(line.strip()))
            return file_data_list

        except Exception as e:
            print(f"read_jsonl()报错：找不到文件或读取文件出错: {e}")
            return []

    @staticmethod
    def write_jsonl(file_path, write_data_list, write_type='w', encoding='utf-8') -> bool:
        """
        将字典列表写入 JSONL 文件，每个字典作为一行。
        :param file_path: 文件路径
        :param write_data_list: 要写入的字典列表
        :param write_type: 写入模式，'w' 覆盖写入，'a' 追加写入
        :param encoding: 文件编码
        :return: 写入成功返回 True，失败返回 False
        """

        try:
            # write_data_list 必须是列表
            if not isinstance(write_data_list, list):
                print("write_jsonl()报错：write_data_list 必须是列表类型")
                return False

            with open(file_path, write_type, encoding=encoding) as file:
                for entry in write_data_list:
                    file.write(json.dumps(entry, ensure_ascii=False) + '\n')
            return True

        except Exception as e:
            print(f"write_jsonl()报错：写入文件出错: {e}")
            return False
