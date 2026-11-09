from datetime import datetime
import itertools

import click
from tabulate import tabulate
from database import connect_to_db
from config import load_config
from validators import validate_id


@click.group("sales")
def sales_group():
    pass


@sales_group.command()
@click.option("-ri", "--recipe-id", type=int, callback=validate_id, required=True)
@click.option("-ci", "--customer-id", type=int, callback=validate_id, required=True)
@click.option("-q", "--quantity", type=int, callback=validate_id, required=True)
def add(recipe_id: int, customer_id: int, quantity: int):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        result = cur.execute(
            """
  INSERT INTO sales (recipe_id, customer_id, cost, cost_price, quantity) 
              VALUES (
                  :recipe_id, 
                  :customer_id, 
                  (SELECT cost FROM recipes WHERE id = :recipe_id), 
                  (SELECT COALESCE(SUM(i.price * ri.quantity), 0) 
                   FROM recipe_ingredients ri 
                   LEFT JOIN ingredients i ON ri.ingredient_id = i.id 
                   WHERE ri.recipe_id = :recipe_id), 
                  :quantity
              ) 
              RETURNING 
                  id, 
                  recipe_id,
                  (SELECT title FROM recipes WHERE id = :recipe_id) AS recipe_title, 
                  customer_id,
                  (SELECT first_name || ' ' || last_name FROM customers WHERE id = :customer_id) AS customer_name, 
                  cost, 
                  cost_price, 
                  quantity
""",
            {
                "recipe_id": recipe_id,
                "customer_id": customer_id,
                "quantity": quantity,
            },
        )
        row = cur.fetchall()
        if result.rowcount > 0:
            click.echo("Запись добавлена")
            click.echo(
                tabulate(
                    row,
                    [
                        "id",
                        "recipe_id",
                        "recipe_title",
                        "customer_id",
                        "customer_fullname",
                        "cost",
                        "cost_price",
                        "quantity",
                        "created_at",
                    ],
                )
            )
        else:
            click.echo("Запись уже существует")
        db.commit()
        cur.close()


@sales_group.command()
@click.argument("id", type=int, callback=validate_id, required=True)
def get(id: int):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        cur.execute(
            """
  SELECT
    id,
    (SELECT title FROM recipes WHERE id = recipe_id),
    (SELECT first_name || ' ' || last_name FROM customers WHERE id = customer_id),
    cost,
    cost_price,
    quantity,
    created_at
      FROM sales WHERE id = ?
""",
            (id,),
        )
        if row := cur.fetchall():
            click.echo(f"Найдено {len(row)} записей")
            click.echo(
                tabulate(
                    row,
                    [
                        "id",
                        "recipe_title",
                        "customer_fullname",
                        "cost",
                        "cost_price",
                        "quantity",
                        "created_at",
                    ],
                )
            )
        else:
            click.echo("Запись не найдена")

        db.commit()
        cur.close()


@sales_group.command()
@click.option("-i", "--id", type=int, callback=validate_id, required=True)
@click.option("-ri", "--recipe-id", type=int, callback=validate_id, required=False)
@click.option("-ci", "--customer-id", type=int, callback=validate_id, required=False)
@click.option("-q", "--quantity", type=int, callback=validate_id, required=False)
@click.option("-c", "--cost", type=int, callback=validate_id, required=False)
def upd(id: int, recipe_id: int, customer_id: int, quantity: int, cost: float):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        result = cur.execute(
            """
  UPDATE sales SET
      recipe_id = COALESCE(:recipe_id, recipe_id),
      customer_id = COALESCE(:customer_id, customer_id),
      quantity = COALESCE(:quantity, quantity),
      cost = COALESCE(:cost, cost)
  WHERE id = :id
  RETURNING
  id
  (SELECT title FROM recipes WHERE id = :recipe_id),
  (SELECT first_name || ' ' || last_name FROM customers WHERE id = :customer_id),
  cost,
  cost_price,
  quantity
""",
            {
                "id": id,
                "cost": cost,
                "recipe_id": recipe_id,
                "customer_id": customer_id,
                "quantity": quantity,
            },
        )
        row = cur.fetchall()
        if result.rowcount > 0:
            click.echo("Запись обновлена")
            click.echo(
                tabulate(
                    row,
                    [
                        "id",
                        "recipe_title",
                        "customer_fullname",
                        "cost",
                        "cost_price",
                        "quantity",
                        "created_at",
                    ],
                )
            )
        else:
            click.echo("Запись не найдена")
        db.commit()
        cur.close()


@sales_group.command(name="del")
@click.argument("id", type=int, callback=validate_id, required=True)
@click.option("-y", is_flag=True, default=False)
def _del(id: int, y: bool):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        result = cur.execute(
            """delete FROM sales WHERE id = :recipe_id RETURNING 
                id,
                (SELECT title FROM recipes WHERE id = :recipe_id),
                (SELECT first_name || ' ' || last_name FROM customers WHERE id = customer_id),
                cost,
                cost_price,
                quantity""",
            {"recipe_id": id},
        )
        row = cur.fetchall()
        if result.rowcount > 0:
            if y:
                db.commit()
                click.echo("Запись удалена")
            else:
                click.echo(
                    tabulate(
                        row,
                        [
                            "id",
                            "recipe_title",
                            "customer_fullname",
                            "cost",
                            "cost_price",
                            "quantity",
                            "created_at",
                        ],
                    )
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


@sales_group.command()
@click.option("-b", "--begin", type=click.DateTime(), required=True)
@click.option("-ci", "--customer-id", type=int, callback=validate_id, required=False)
@click.option(
    "-e", "--end", type=click.DateTime(), required=False, default=datetime.now()
)
def stats(begin: datetime, end: datetime, customer_id: int):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        cur.execute(
            """SELECT SUM(cost * quantity), SUM(cost_price * quantity), SUM(cost * quantity) - SUM(cost_price * quantity)
        FROM sales WHERE customer_id = COALESCE(?, customer_id) AND created_at >= ? AND created_at <= ?""",
            (
                customer_id,
                begin,
                end,
            ),
        )
        row = cur.fetchall()
        if all(row[0]):
            click.echo(f"Найдено {len(row)} записей")
            click.echo(tabulate(row, ["Доходы", "Расходы", "Прибыль"]))
        else:
            click.echo("Записей не найдено")
        db.commit()
        cur.close()


@sales_group.command()
@click.option("-b", "--begin", type=click.DateTime(), required=True)
@click.option("-ci", "--customer-id", type=int, callback=validate_id, required=False)
@click.option(
    "-e",
    "--end",
    type=click.DateTime(),
    required=False,
    default=datetime.now().replace(microsecond=0),
)
def list(begin: datetime, end: datetime, customer_id: int):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        cur.execute(
            """SELECT 
                 id,
                 recipe_id,
                 (SELECT title FROM recipes WHERE id = recipe_id),
                 customer_id,
                 (SELECT first_name || ' ' || last_name FROM customers WHERE id = customer_id),
                 cost,
                 cost_price,
                 quantity,
                 created_at
               FROM sales WHERE customer_id = COALESCE(?, customer_id) AND created_at >= ? AND created_at <= ?""",
            (
                customer_id,
                begin,
                end,
            ),
        )
        if row := cur.fetchall():
            click.echo(f"Найдено {len(row)} записей")
            click.echo(
                tabulate(
                    row,
                    [
                        "id",
                        "recipe_id",
                        "recipe_title",
                        "customer_id",
                        "customer_fullname",
                        "cost",
                        "cost_price",
                        "quantity",
                        "created_at",
                    ],
                )
            )
        else:
            print(row)
            click.echo("Записей не найдено")
        db.commit()
        cur.close()
