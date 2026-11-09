import click
from re import fullmatch


def validate_fname(ctx, param, value: str):
    if value is "":
        return ""
    if fullmatch(r"^[а-яА-ЯёЁA-Za-z]{3,20}$", value):
        return value.lower()
    raise click.BadParameter("Некорректная имя")


def validate_lname(ctx, param, value: str):
    if value is "":
        return ""
    if fullmatch(r"^[а-яА-ЯёЁA-Za-z]{0,20}$", value):
        return value.lower()
    raise click.BadParameter("Некорректная фамилия")


def validate_desc(ctx, param, value: str):
    if value is None:
        return None
    if fullmatch(r"^[а-яА-ЯёЁA-Za-z0-9\ ]{3,200}$", value):
        return value.lower()
    raise click.BadParameter("Некорректная фамилия")


def validate_title(ctx, param, value: str | None):
    if value is None:
        return None
    if fullmatch(r"^[а-яА-ЯёЁA-Za-z0-9\ ]{3,60}$", value):
        return value.lower()
    raise click.BadParameter("Некорректное название")


def validate_id(ctx, param, value: int):
    if value is None:
        return None
    if value > 0:
        return value
    raise click.BadParameter("ID не может быть отрицательным")


def validate_price(ctx, param, value: float):
    if value is None:
        return None
    if value >= 0:
        return value
    raise click.BadParameter("Цена не может быть отрицательной")


def validate_quantity(ctx, param, value: float):
    if value is None:
        return None
    if value > 0:
        return value
    raise click.BadParameter("Количество не может быть отрицательным")


def validate_unit(ctx, param, value: str | None):
    if value is None:
        return None
    value = value.upper()
    if value in {"KG", "L"}:
        return value
    raise click.BadParameter(
        "Некорректная мера измерения. Допустимые меры измерения: KG, L (регистр не важен)"
    )
