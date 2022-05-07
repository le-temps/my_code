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

cli.add_command(service)

if __name__ == "__main__":
    cli()