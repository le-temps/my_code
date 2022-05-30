import click
import uvicorn
from utils.config import settings
from utils.logger import logger

@click.group()
def cli():
    pass

@click.command()
def service():
    from service.service import app
    uvicorn.run(app=app, host=settings.service_auth.host, port=settings.service_auth.port)

@click.command()
@click.option("--w", type=int, help="worker num")
def worker(w):
    from worker.worker import start_worker
    start_worker(w)

@click.command()
@click.option("--i", type=str, help="需要备份的ES索引名")
@click.option("--d", type=str, help="需要备份的日期")
def bakup_index_by_date(i, d):
    from scripts.bakup_index_by_date import bakup_index_by_date
    bakup_index_by_date(i, d)

@click.command()
@click.option("--q", type=str, help="elasticsearch query_string输入")
@click.option("--t", type=str, help="raw_table类型")
def produce_update_task_by_query(q, t):
    from scripts.produce_update_task_by_query import produce_update_task_by_query
    produce_update_task_by_query(t, q)

@click.command()
def clear_redis_queue():
    from scripts.clear_redis_queue import clear_redis_queue
    clear_redis_queue()

@click.command()
@click.option("--m", type=str, help="test module.")
def test(m):
    from tests import test_module
    if m not in test_module:
        logger.error(f"Try to test unknown module: {m}")
    test_module[m]()

cli.add_command(service)
cli.add_command(worker)
cli.add_command(bakup_index_by_date)
cli.add_command(produce_update_task_by_query)
cli.add_command(clear_redis_queue)
cli.add_command(test)

if __name__ == "__main__":
    cli()