from os import path

from file_utils.jsonl_file_util import JSONLFileUtil
from file_utils.json_file_util import JSONFileUtil

jsonl_file_path = path.abspath('test_file/jsonl_test.jsonl')
test_data = [
    {"name": "Alice", "age": 30, "city": "New York", "data": {"a": "123", "b": 2}},
    {"name": "Bob", "age": 25, "city": "Los Angeles"},
    {"name": "Charlie", "age": 35, "city": "Chicago"}
]
# 写入jsonl
# JSONLFileUtil.write_jsonl(file_path=jsonl_file_path, write_data_list=test_data, write_type='w')

# 读取jsonl
# jsonl_data_list = JSONLFileUtil.read_jsonl(jsonl_file_path)

# print(jsonl_data_list)


json_file_path = path.abspath('test_file/json_test.json')
# 读取
json_data = JSONFileUtil.read_json(json_file_path)
print(json_data)

d1 = {"name": "Alice", "age": 30, "city": "New York", "data": {"a": "123", "b": 2}}
# 写入
JSONFileUtil.write_json(file_path=json_file_path, write_dict=d1, write_type='w')
