import json


class JSONLFileUtil:

    @staticmethod
    def read_jsonl(file_path, encoding='utf-8') -> list[dict]:
        """读取 JSONL 文件，返回包含所有行的列表，每行是一个字典。"""
        try:
            file_data_list = []
            with open(file_path, 'r', encoding=encoding) as file:
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
