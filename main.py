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

cli.add_command(service)
cli.add_command(worker)

if __name__ == "__main__":
    cli()