import click
from tabulate import tabulate

from database import connect_to_db
from config import load_config
from validators import validate_title, validate_desc, validate_id, validate_quantity


@click.group("rps")
def recipes_group():
    pass


@recipes_group.command()
@click.option("-t", "--title", type=str, callback=validate_title, required=True)
@click.option("-c", "--cost", type=float, callback=validate_quantity, required=True)
@click.option(
    "-d",
    "--description",
    type=str,
    callback=validate_desc,
    required=False,
    default=None,
)
def add(title: str, description: str, cost: float):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        result = cur.execute(
            "insert or ignore into recipes (title, description, cost) values (?, ?, ?) returning id, title, cost, description",
            (title, description, cost),
        )
        row = cur.fetchall()
        if result.rowcount > 0:
            click.echo("Запись добавлена")
            click.echo(
                tabulate(
                    row,
                    ["id", "title", "cost", "description"],
                )
            )
        else:
            click.echo("Запись уже существует")
        db.commit()
        cur.close()


@recipes_group.command()
@click.argument("id", type=int, callback=validate_id, required=True)
def get(id: int):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        cur.execute(
            "select id, title, cost, description from recipes where id = ?",
            (id,),
        )
        if row := cur.fetchall():
            click.echo(f"Найдено {len(row)} записей")
            click.echo(tabulate(row, ["id", "title", "cost", "description"]))
        else:
            click.echo("Запись не найдена")

        db.commit()
        cur.close()


@recipes_group.command()
@click.option("-i", "--id", type=int, callback=validate_id, required=True)
@click.option("-t", "--title", type=str, callback=validate_title, required=False)
@click.option("-c", "--cost", type=float, callback=validate_quantity, required=True)
@click.option("-d", "--description", type=str, callback=validate_desc, required=False)
def upd(
    id: int,
    title: str | None = None,
    description: str | None = None,
    cost: float | None = None,
):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()

        cur.execute(
            """
            update recipes 
            set title = coalesce(?, title), 
                description = coalesce(?, description),
                cost = coalesce(?, cost)
            where id = ? returning id, title, description, cost, created_at
            """,
            (title, description, cost, id),
        )
        row = cur.fetchall()
        if cur.rowcount > 0:
            db.commit()
            click.echo("Запись обновлена")
            click.echo(
                tabulate(
                    row, headers=["id", "title", "description", "cost", "created_at"]
                )
            )
        else:
            click.echo("Запись не найдена")

        cur.close()


@recipes_group.command(name="del")
@click.argument("id", type=int, callback=validate_id, required=True)
@click.option("-y", is_flag=True, default=False)
def _del(id: int, y: bool):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        result = cur.execute(
            "delete from recipes where id = ? returning id, title, description, created_at",
            (id,),
        )
        row = cur.fetchall()
        if result.rowcount > 0:
            if y:
                db.commit()
                click.echo("Запись удалена")
            else:
                click.echo(tabulate(row, ["id", "title", "description", "created_at"]))
                if click.confirm("Вы действительно хотите удалить эту запись?"):
                    db.commit()
                    click.echo("Запись удалена")
                else:
                    db.rollback()
                    click.echo("Удаление отменено")
        else:
            click.echo("Запись не найдена")
        cur.close()


@recipes_group.command()
def list():
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        cur.execute("select id, title, description, cost, created_at from recipes")
        if row := cur.fetchall():
            click.echo(f"Найдено {len(row)} записей")
            click.echo(
                tabulate(row, ["id", "title", "description", "cost", "created_at"])
            )
        else:
            click.echo("Записей не найдено")
        db.commit()
        cur.close()


@recipes_group.command()
@click.argument("recipe-id", type=int, callback=validate_id, required=True)
def info(recipe_id: int):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        cur.execute(
            "select (select title from recipes where id = :recipe_id), (select cost from recipes where id = :recipe_id), SUM(ingredients.price * recipe_ingredients.quantity) from recipe_ingredients left join ingredients on recipe_ingredients.ingredient_id = ingredients.id where recipe_ingredients.recipe_id = :recipe_id",
            {"recipe_id": recipe_id},
        )
        if row := cur.fetchall():
            click.echo(tabulate(row, ["title", "cost", "cost_price"]))
        db.commit()
        cur.close()


@recipes_group.group("ing")
def recipes_ingredients_group():
    pass


@recipes_ingredients_group.command(name="add")
@click.option("-ri", "--recipe-id", type=int, callback=validate_id, required=True)
@click.option("-ii", "--ingredient-id", type=int, callback=validate_id, required=True)
@click.option("-q", "--quantity", type=float, callback=validate_quantity, required=True)
def recipes_ingredients_add(recipe_id: int, ingredient_id: int, quantity: float):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        result = cur.execute(
            """insert or ignore 
            into recipe_ingredients (recipe_id, ingredient_id, quantity)
            values (?, ?, ?)""",
            (
                recipe_id,
                ingredient_id,
                quantity,
            ),
        )
        db.commit()
        if result.rowcount > 0:
            click.echo("Запись добавлена")
            click.echo(
                tabulate(
                    [
                        [
                            recipe_id,
                            ingredient_id,
                            quantity,
                        ]
                    ],
                    [
                        "recipe_id",
                        "ingredient_id",
                        "quantity",
                    ],
                )
            )
        else:
            click.echo("Запись уже существует")
        cur.close()


@recipes_ingredients_group.command(name="del")
@click.option("-ri", "--recipe-id", type=int, callback=validate_id, required=True)
@click.option("-ii", "--ingredient-id", type=int, callback=validate_id, required=True)
@click.option("-y", is_flag=True, default=False)
def recipes_ingredients_del(recipe_id: int, ingredient_id: int, y: bool):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        result = cur.execute(
            """delete from recipe_ingredients
                                where recipe_id = ? and ingredient_id = ?
                                returning (select title from recipes where id = ?),
                                          (select title from ingredients where id = ?)""",
            (recipe_id, ingredient_id, recipe_id, ingredient_id),
        )
        row = cur.fetchall()
        if result.rowcount > 0:
            if y:
                db.commit()
                click.echo("Запись удалена")
            else:
                click.echo(tabulate(row, ["recipe_title", "ingredient_title"]))
                if click.confirm("Вы действительно хотите удалить эту запись?"):
                    db.commit()
                    click.echo("Запись удалена")
                else:
                    db.rollback()
                    click.echo("Удаление отменено")
        else:
            click.echo("Запись не найдена")
        cur.close()


@recipes_ingredients_group.command(name="upd")
@click.option("-ri", "--recipe-id", type=int, callback=validate_id, required=True)
@click.option("-ii", "--ingredient-id", type=int, callback=validate_id, required=True)
@click.option("-q", "--quantity", type=float, callback=validate_quantity, required=True)
def recipes_ingredients_upd(recipe_id: int, ingredient_id: int, quantity: float):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        result = cur.execute(
            """update recipe_ingredients
               set quantity = :quantity where recipe_id = :recipe_id and ingredient_id = :ingredient_id
               returning (select title from recipes where id = :recipe_id),
                         (select title from ingredients where id = :ingredient_id),
                         (select quantity || ' ' || (select unit from ingredients where id = :ingredient_id) from recipe_ingredients where recipe_id = :recipe_id and ingredient_id = :ingredient_id)""",
            {
                "recipe_id": recipe_id,
                "ingredient_id": ingredient_id,
                "quantity": quantity,
            },
        )
        row = cur.fetchall()
        if result.rowcount > 0:
            click.echo("Запись обновлена")
            click.echo(tabulate(row, ["recipe_title", "ingredient_title", "quantity"]))
        else:
            click.echo("Запись не найдена")
        db.commit()
        cur.close()


@recipes_ingredients_group.command(name="list")
@click.argument("recipe-id", type=int, callback=validate_id, required=True)
def recipes_ingredients_list(recipe_id: int):
    with connect_to_db(load_config()) as db:
        cur = db.cursor()
        cur.execute(
            """select ingredients.id, ingredients.title, recipe_ingredients.quantity || ' ' || ingredients.unit as quantity, recipe_ingredients.quantity * ingredients.price || ' ' || ingredients.unit
                       from recipe_ingredients
                       left join ingredients on recipe_ingredients.ingredient_id = ingredients.id
                       where recipe_id = ?""",
            (recipe_id,),
        )
        if row := cur.fetchall():
            click.echo(f"Найдено {len(row)} записей")
            click.echo(
                tabulate(
                    row,
                    ["id", "title", "quantity", "price"],
                )
            )
        else:
            click.echo("Записей не найдено")
        db.commit()
        cur.close()
