import click
from tabulate import tabulate

from database import connect_to_db
from config import load_config
from utils import levenshtein
from validators import validate_fname, validate_lname, validate_id


@click.group("ctm")
def customers_group():
    pass


@customers_group.command()
@click.option(
    "-fn",
    "--first-name",
    type=str,
    callback=validate_fname,
    required=True,
)
@click.option(
    "-ln",
    "--last-name",
    type=str,
    callback=validate_lname,
    required=True,
)
def add(first_name: str, last_name: str):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        result = cur.execute(
            "insert or ignore into customers (first_name, last_name) values (?, ?) returning id, first_name, last_name, created_at",
            (
                first_name,
                last_name,
            ),
        )
        row = cur.fetchall()
        if result.rowcount > 0:
            click.echo("Запись добавлена")
            click.echo(
                tabulate(
                    row,
                    ["id", "first_name", "last_name", "created_at"],
                )
            )
        else:
            click.echo("Запись уже существует")
        db.commit()
        cur.close()


@customers_group.command()
@click.argument("id", type=int, callback=validate_id, required=True)
def get(id: int):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        cur.execute(
            """
  SELECT
    id,
    first_name,
    last_name,
    created_at,
    is_deleted
  FROM
    customers
  WHERE
    id = ?
""",
            (id,),
        )
        if row := cur.fetchall():
            click.echo(f"Найдено {len(row)} записей")
            click.echo(
                tabulate(
                    row, ["id", "first_name", "last_name", "created_at", "is_deleted"]
                )
            )
        else:
            click.echo("Запись не найдена")

        db.commit()
        cur.close()


@customers_group.command()
@click.option("-i", "--id", type=int, callback=validate_id, required=True)
@click.option(
    "-fn",
    "--first-name",
    type=str,
    callback=validate_fname,
    required=True,
)
@click.option(
    "-ln",
    "--last-name",
    type=str,
    callback=validate_lname,
    required=True,
)
def upd(id: int, first_name: str, last_name: str):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        result = cur.execute(
            """
  UPDATE customers
  SET
    first_name = coalesce(?, first_name),
    last_name = coalesce(?, last_name)
  WHERE id = ? AND is_deleted = FALSE
  RETURNING id,
    first_name,
    last_name,
    created_at
""",
            (
                first_name,
                last_name,
                id,
            ),
        )
        row = cur.fetchall()
        if result.rowcount > 0:
            click.echo("Запись обновлена")
            click.echo(
                tabulate(
                    row,
                    ["id", "first_name", "last_name", "created_at"],
                )
            )
        else:
            click.echo("Запись не найдена")
        db.commit()
        cur.close()


@customers_group.command()
@click.argument("id", type=int, callback=validate_id, required=True)
def rem(id: int):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        result = cur.execute(
            """
UPDATE customers
SET is_deleted = TRUE
RETURNING id,
    first_name,
    last_name,
    created_at
""",
            (id,),
        )
        row = cur.fetchall()
        if result.rowcount > 0:
            click.echo(tabulate(row, ["id", "first_name", "last_name", "created_at"]))
            db.commit()
            click.echo("Запись удалена")
        else:
            click.echo("Запись не найдена")
        cur.close()


@customers_group.command()
@click.argument("id", type=int, callback=validate_id, required=True)
def res(id: int):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        result = cur.execute(
            """
UPDATE customers
SET is_deleted = FALSE
RETURNING id,
    first_name,
    last_name,
    created_at
""",
            (id,),
        )
        row = cur.fetchall()
        if result.rowcount > 0:
            click.echo(tabulate(row, ["id", "first_name", "last_name", "created_at"]))
            db.commit()
            click.echo("Запись восстановлен")
        else:
            click.echo("Запись не найдена")
        cur.close()


@customers_group.command(name="del")
@click.argument("id", type=int, callback=validate_id, required=True)
@click.option("-y", is_flag=True, default=False)
def _del(id: int, y: bool):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        result = cur.execute(
            """
DELETE FROM customers
WHERE
    id = ? returning id,
    first_name,
    last_name,
    created_at
""",
            (id,),
        )
        row = cur.fetchall()
        if result.rowcount > 0:
            click.echo(tabulate(row, ["id", "first_name", "last_name", "created_at"]))
            if y:
                db.commit()
                click.echo("Запись удалена")
            else:
                if click.confirm("Вы действительно хотите удалить эту запись?"):
                    db.commit()
                    click.echo("Запись удалена")
                else:
                    db.rollback()
                    click.echo("Удаление отменено")
        else:
            click.echo("Запись не найдена")
        cur.close()


@customers_group.command()
@click.option(
    "-fn",
    "--first-name",
    type=str,
    callback=validate_fname,
    required=False,
    default="",
)
@click.option(
    "-ln",
    "--last-name",
    type=str,
    callback=validate_lname,
    required=False,
    default="",
)
def find(first_name: str, last_name: str):
    full_name = first_name + " " + last_name
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        db.create_function("levenshtein", 2, levenshtein)
        cur.execute(
            "select id, first_name, last_name, levenshtein(first_name || ' ' || last_name, ?) as rank from customers where rank <= ? AND is_deleted = FALSE order by rank asc",
            (full_name, 10),
        )
        row = cur.fetchall()
        click.echo(f"Найдено {len(row)} совпадений")
        click.echo(tabulate(row, ["id", "first_name", "last_name", "rank"]))
        db.commit()
        cur.close()


@customers_group.command()
def list():
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        cur.execute(
            """
SELECT
    id,
    first_name,
    last_name,
    created_at
FROM customers""",
        )
        row = cur.fetchall()
        click.echo(f"Найдено {len(row)} записей")
        click.echo(tabulate(row, ["id", "first_name", "last_name", "created_at"]))
        db.commit()
        cur.close()
