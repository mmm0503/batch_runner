from os import path

from file_utils.jsonl_file_util import JSONLFileUtil

jsonl_file_path = path.abspath('test_file/jsonl_test.jsonl')
test_data = [
    {"name": "Alice", "age": 30, "city": "New York", "data": {"a": "123", "b": 2}},
    {"name": "Bob", "age": 25, "city": "Los Angeles"},
    {"name": "Charlie", "age": 35, "city": "Chicago"}
]
JSONLFileUtil.write_jsonl(file_path=jsonl_file_path, write_data_list=test_data, write_type='w')  # 写入jsonl
jsonl_data_list = JSONLFileUtil.read_jsonl(jsonl_file_path)  # 读取jsonl
print(jsonl_data_list)
