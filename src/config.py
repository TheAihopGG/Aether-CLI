import platformdirs
import tomllib
import os
from consts import BASE_DIR


def load_config():
    _project_data: dict = tomllib.load(open(BASE_DIR / "pyproject.toml", "rb")).get(
        "project", {}
    )

    assert _project_data.get("name", False)
    assert _project_data.get("version", False)

    _dirs = platformdirs.PlatformDirs(
        appname=_project_data["name"],
        version=_project_data["version"],
        ensure_exists=True,
    )
    _config_file = _dirs.user_config_path / "config.toml"

    if not _config_file.exists():
        with open(_config_file, "w") as file:

            file.write(f"""[db]
path = '{_dirs.user_data_path / "database.db"}'
""")
        os.chmod(_config_file, 0o700)

    return tomllib.load(open(_config_file, "rb"))
