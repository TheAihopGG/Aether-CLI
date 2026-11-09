import click
from tabulate import tabulate

from config import load_config
from database import connect_to_db
from validators import validate_id, validate_title, validate_price, validate_unit


@click.group("ing")
def ingredients_group():
    pass


@ingredients_group.command()
@click.option("-t", "--title", type=str, callback=validate_title, required=True)
@click.option("-p", "--price", type=float, callback=validate_price, required=True)
@click.option("-u", "--unit", type=str, callback=validate_unit, required=True)
def add(title: str, price: float, unit: str):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        result = cur.execute(
            """
  INSERT
  OR ignore INTO ingredients (title, price, unit)
  VALUES
    (?, ?, ?) returning id,
    title,
    price,
    unit
""",
            (
                title,
                price,
                unit,
            ),
        )
        row = cur.fetchall()
        if result.rowcount > 0:
            click.echo("Запись добавлена")
            click.echo(
                tabulate(
                    row,
                    ["id", "title", "price", "unit"],
                )
            )
        else:
            click.echo("Запись уже существует")
        db.commit()
        cur.close()


@ingredients_group.command()
@click.argument("id", type=int, callback=validate_id, required=True)
def get(id: int):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        cur.execute(
            "select id, title, price, unit, updated_at from ingredients where id = ?",
            (id,),
        )
        if row := cur.fetchall():
            click.echo(f"Найдено {len(row)} записей")
            click.echo(tabulate(row, ["id", "title", "price", "unit", "updated_at"]))
        else:
            click.echo("Запись не найдена")

        db.commit()
        cur.close()


@ingredients_group.command()
@click.option("-i", "--id", type=int, callback=validate_id, required=True)
@click.option("-t", "--title", type=str, callback=validate_title, required=False)
@click.option("-p", "--price", type=float, callback=validate_price, required=False)
@click.option("-u", "--unit", type=str, callback=validate_unit, required=False)
def upd(
    id: int,
    title: str | None = None,
    price: float | None = None,
    unit: str | None = None,
):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()

        cur.execute(
            """
  UPDATE ingredients
  SET
    title = coalesce(?, title),
    price = coalesce(?, price),
    unit = coalesce(?, unit)
  WHERE
    id = ? returning id,
    title,
    price,
    unit
""",
            (title, price, unit, id),
        )
        row = cur.fetchall()
        if cur.rowcount > 0:
            db.commit()
            click.echo("Запись обновлена")
            click.echo(tabulate(row, headers=["id", "title", "price", "unit"]))
        else:
            click.echo("Запись не найдена")

        cur.close()


@ingredients_group.command(name="del")
@click.argument("id", type=int, callback=validate_id, required=True)
@click.option("-y", is_flag=True, default=False)
def _del(id: int, y: bool):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        result = cur.execute(
            "delete from ingredients where id = ? returning id, title, price, unit, updated_at",
            (id,),
        )
        row = cur.fetchall()
        if result.rowcount > 0:
            if y:
                db.commit()
                click.echo("Запись удалена")
            else:
                click.echo(
                    tabulate(row, ["id", "title", "price", "unit", "updated_at"])
                )
                if click.confirm("Вы действительно хотите удалить эту запись?"):
                    db.commit()
                    click.echo("Запись удалена")
                else:
                    db.rollback()
                    click.echo("Удаление отменено")
        else:
            click.echo("Запись не найдена")
        cur.close()


@ingredients_group.command()
def list():
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        cur.execute("select id, title, price, unit, updated_at from ingredients")
        row = cur.fetchall()
        db.commit()
        click.echo(f"Найдено {len(row)} записей")
        click.echo(tabulate(row, ["id", "title", "price", "unit", "updated_at"]))
        cur.close()
