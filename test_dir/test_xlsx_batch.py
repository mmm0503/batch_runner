import json

from batch_data_types.api_types import ApiRequestParams, ApiRequestTask
from batch_jobs.xlsx_http_batch_handler import XlsxHttpBatchHandler


def create_api_task_params_fn(row: list, header_row: list) -> ApiRequestParams:
    '''根据xlsx行数据，创建ApiRequestParams'''
    quota_type_dict = {
        "个股": "STOCK",
        "基金": "FUND",
    }
    return ApiRequestParams(
        full_url="http://localhost:8000/test/batchTest",
        methods="POST",
        json={
            "quotaName": row[1],
            "quotaType": quota_type_dict[row[2]] or "",
        },
        headers={
            "Content-Type": "application/json"
        }
    )


def format_res_fn(api_request_task: ApiRequestTask):
    '''格式化接口返回结果'''
    res = api_request_task.res
    try:
        api_request_task.format_data = json.dumps(res.get("data"))
        quota_value = res.get("data", {}).get("quotaValue", "")
        api_request_task.format_data_is_success = quota_value > 5
    except Exception as e:
        print(e)
        api_request_task.format_data = None
        api_request_task.format_data_is_success = False


async def main():
    xlsx_batch_handler = XlsxHttpBatchHandler(
        file_path="example_workbook.xlsx",
        write_file_path="example_workbook_result.xlsx",
        create_api_task_params_fn=create_api_task_params_fn,
        format_res_fn=format_res_fn,
        concurrency=3,
        sleep_time=0
    )
    await xlsx_batch_handler.batch_run()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
