import click
from re import fullmatch


def validate_name(ctx, param, value: str):
    if fullmatch(r"^[а-яА-ЯёЁA-Za-z]{3,20}$", value):
        return value.lower()
    raise click.BadParameter("Некорректная имя/фамилия")
