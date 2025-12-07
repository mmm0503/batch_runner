from batch_data_types.api_types import ApiBatchTask, ApiRequestTask, ApiRequestParams
from file_reader.xlsx_file_handler import XlsxFileHandler


def main():
    reader_file_path: str = "example_workbook.xlsx"
    writer_file_path: str = "example_output.xlsx"

    # 读取文件内容
    xlsx_reader_handler = XlsxFileHandler(reader_file_path)
    reader_data = xlsx_reader_handler.read_handle()
    for row in reader_data:
        print(row)

    # 跑批数据预处理
    quota_type_dict = {
        "个股": "STOCK",
        "基金": "FUND",
    }
    # 跑批res处理函数
    api_batch_task: ApiBatchTask = ApiBatchTask(
        api_request_task_list=[
            ApiRequestTask(
                api_param=ApiRequestParams(
                    full_url="http://localhost:8000/test/batchTest",
                    methods="POST",
                    json={
                        "quotaName": row[0],
                        "quotaType": quota_type_dict.get(row[1], ""),
                    },
                    headers={
                        "Content-Type": "application/json",
                    }
                ),
                origin_data=row,
            )
            for row in reader_data
        ],
        concurrency=5,
        sleep_time=1.0,
        callback_trigger_count=10,
        all_complete_callback=None,
    )
    # 开始跑批

    # 跑批结果后处理

    # 写入文件内容
    xslx_writer_handler = XlsxFileHandler(writer_file_path, is_create=True)
    xslx_writer_handler.set_content(reader_data)
    xslx_writer_handler.write_handle()


main()
