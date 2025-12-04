from os import path

from file_utils.json_file_util import JSONFileUtil

json_file_path = path.abspath('test_file/json_test.json')
d1 = {"name": "Alice", "age": 30, "city": "New York", "data": {"a": "123", "b": 2}}
JSONFileUtil.write_json(file_path=json_file_path, write_dict=d1, write_type='w')  # 写入
json_data = JSONFileUtil.read_json(json_file_path)  # 读取
print(json_data)