import click

from database import run_migrations
from config import load_config
from commands import sales_group, recipes_group, ingredients_group, customers_group


@click.group()
def cli():
    pass


@cli.command()
def sync_db():
    run_migrations(load_config())
    click.echo("База данных синхронизирована")


groups = {sales_group, recipes_group, ingredients_group, customers_group}
[cli.add_command(group) for group in groups]

if __name__ == "__main__":
    cli()
