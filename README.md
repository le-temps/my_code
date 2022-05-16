# Squint_data

Squint检索系统的数据处理模块，实现将原始数据落盘数据库，触发关联任务，实时更新宽表以供检索查询最新数据


### TASK_DEFINE

{
    "source_index_type": "organization_businessinfo", # 源Raw_table名
    "destination_index_type": "organization", # 目的更新宽表名
    "value": "xxxx公司", # update根据的extract条件值
    "try_num": 0  # 已经尝试处理次数
    "create_time": "2022-05-16 00:00:00" # 任务创建时间
    "finish_time": "2022-05-16 01:00:00" # 任务完成时间
}