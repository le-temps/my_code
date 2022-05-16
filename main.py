import click
import uvicorn
from utils.config import settings

@click.group()
def cli():
    pass

@click.command()
def service():
    from service.service import app
    uvicorn.run(app=app, host=settings.service.host, port=settings.service.port)

@click.command()
def worker():
    from worker.worker import start_worker
    start_worker()

@click.command()
@click.option("--i", type=str, help="需要备份的ES索引名")
@click.option("--d", type=str, help="需要备份的日期")
def bakup_index_by_date():
    from scripts.bakup_index_by_date import bakup_index_by_date
    bakup_index_by_date(i, d)

@click.command()
@click.option("--q", type=str, help="elasticsearch query_string输入")
@click.option("--t", type=str, help="raw_table类型")
def produce_update_task_by_query():
    from scripts.produce_update_task_by_query import produce_update_task_by_query
    produce_update_task_by_query(t, q)

cli.add_command(service)
cli.add_command(worker)
cli.add_command(bakup_index_by_date)
cli.add_command(produce_update_task_by_query)

if __name__ == "__main__":
    cli()