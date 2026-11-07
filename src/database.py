import yoyo
import sqlite3
from consts import BASE_DIR


def run_migrations(config: dict):
    backend = yoyo.get_backend(f"sqlite3:///{config['db']['path']}")
    migrations = yoyo.read_migrations(BASE_DIR / "src/migrations")

    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))
        backend.rollback_migrations(backend.to_rollback(migrations))


def connect_to_db(config: dict) -> sqlite3.Connection:
    return sqlite3.connect(config["db"]["path"])
