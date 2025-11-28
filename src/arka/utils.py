import os
import json
import tempfile
from typing import Optional,Any
from pathlib import Path
from urllib.parse import quote
from importlib.util import find_spec

def app_exists(name):
    return find_spec(name) is not None


def load_secret_key(
    environment: str, base_dir: Path
) -> Optional[str]:
    key = None
    _secret = base_dir / ".secret"
    try:
        with open(_secret, "r") as fh:
            key = " ".join(fh.readlines()).strip()
            print(f"Loaded production secret: {key[:5]}....")
    except (OSError, FileNotFoundError) as e:
        raise e
    if key:
        print(f"Loaded secret: {key[:5]}....")
        return key
    else:
        raise ValueError(
            f"Could not read secret key: DJANGO_ENV:{environment}, BASE_DIR:{base_dir}, SECRET_KEY:{key}"
        )

def build_broker_url(config: dict[str, str]) -> str:
    """
    Builds a string for the broker url from a dictionary
    """
    scheme = config.get("scheme", "amqp")
    username = quote(config["username"])
    password = quote(config["password"])
    host = config["host"]
    port = config.get("port", 5672)
    vhost = quote(config.get("vhost", "/"), safe="")
    return f"{scheme}://{username}:{password}@{host}:{port}/{vhost}"

def check_logdir(logdir: Optional[str]):
    """
    Validates log directory:
        - exists
        - is a directory
        - is writeable
    If
        - Is not directory raise NotADirectoryError
        - Does not exist, create, if fail catch OSError as PermissionError
        - Isn't writeable raise PermissionError
    """
    if not logdir:
        raise ValueError(f"Log directory value was not specified, ARKA_LOGDIR:{logdir}")
    p = Path(logdir)
    # Is not a directory raise
    if p.exists() and not p.is_dir():
        raise NotADirectoryError(f"{p} is a file, not a directory")

    try:
        # Try to create, this raises OSError on fail
        p.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise PermissionError(f"Cannot create log directory {p}") from e

    try:
        # mkdir should check write permissions
        # but just to be safe verify it's writeable
        with tempfile.TemporaryFile(dir=p) as _:
            pass
    # Raise a permission error for clarity (not writeable)
    except OSError as e:
        raise PermissionError(f"Cannot write to log directory {p}") from e

def load_config_file(environment:str,base_dir: Path)->Any:
    """
    Loads json config file:
        - First checks if environment variable is set if so load that path
        - Else uses predefined paths to load the file
        - If the path does not exist returns an empty set 
    """
    config_file = os.environ.get("ARKA_CONFIG_FILE", None)
    if config_file:
        config_path = Path(config_file)
    else:
        config_path = base_dir / "config.json" if environment == "production" else base_dir / "config.dev.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {}