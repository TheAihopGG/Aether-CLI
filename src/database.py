import yoyo
import sqlite3
from consts import BASE_DIR


def run_migrations(config: dict):
    backend = yoyo.get_backend(f"sqlite:///{config['db']['path']}")
    migrations = yoyo.read_migrations(str(BASE_DIR / "src/migrations"))

    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))


def connect_to_db(config: dict) -> sqlite3.Connection:
    conn = sqlite3.connect(config["db"]["path"])
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
