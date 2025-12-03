import json


class JSONFileUtil:

    @staticmethod
    def read_json(file_path, encoding='utf-8') -> dict:
        """读取 JSON 文件，返回字典。"""
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                # 判断文件内容是否为空
                file_content = file.read().strip()
                if not file_content:
                    print(f"{file_path} 文件内容为空，返回空字典")
                    return {}

                file.seek(0)  # 重置文件指针到开头
                return json.load(file)

        except Exception as e:
            print(f"{file_path} read_json()报错：找不到文件或读取文件出错: {e}")
            return {}

    @staticmethod
    def write_json(file_path, write_dict, write_type='w', encoding='utf-8') -> bool:
        """
        将字典写入 JSON 文件。
        :param file_path: 文件路径
        :param write_dict: 要写入的字典
        :param write_type: 写入模式，'w' 覆盖写入，'a' 追加写入
        :param encoding: 文件编码
        :return: 写入成功返回 True，失败返回 False
        """

        try:
            # write_data 必须是字典
            if not isinstance(write_dict, dict):
                print("write_json()报错：write_data 必须是字典类型")
                return False

            with open(file_path, write_type, encoding=encoding) as file:
                json.dump(write_dict, file, ensure_ascii=False, indent=4)
            return True

        except Exception as e:
            print(f"write_json()报错：写入文件出错: {e}")
            return False
