import tempfile
from typing import Optional
from pathlib import Path
from urllib.parse import quote

from django.core.management.utils import get_random_secret_key


def load_secret_key(
    environment: str, base_dir: str, key: Optional[str]
) -> Optional[str]:
    if environment == "development" and key is None:
        _secret = Path(base_dir, "dev.secret").resolve()
        try:
            with open(_secret, "r") as fh:
                key = " ".join(fh.readlines()).strip()
                print(f"Loaded development secret: {key}")
        except OSError:
            with open(_secret, "w") as fh:
                key = get_random_secret_key()
                fh.write(key)
                print(f"Generated and stored new secret key: {key}")
    elif environment == "production":
        _secret = Path(base_dir, ".secret").resolve()
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
            f"Secret key was neither read nor generated: DJANGO_ENV:{environment}, BASE_DIR:{base_dir}, SECRET_KEY:{key}"
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


def check_logdir(logdir: str):
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
