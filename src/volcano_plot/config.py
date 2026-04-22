import os
from pathlib import Path

from dotenv import load_dotenv


_ENV_FILE = Path.cwd() / ".env"
_VAR = "GMT_LIBRARY_PATH"


def load_config() -> None:
    """Load environment variables from .env and configure GMT_LIBRARY_PATH."""
    load_dotenv(_ENV_FILE, override=False)

    gmt_path = os.environ.get(_VAR, "").strip()

    if not gmt_path:
        raise OSError(
            f"{_VAR} is not set.\n\n"
            "To fix this:\n"
            "  1. Copy .env.example to .env in your project root.\n"
            f"  2. Set {_VAR} to the GMT bin directory, e.g.:\n"
            f"       {_VAR}=D:\\Projects\\gmt6\\bin\n"
            "  3. Download GMT from https://www.generic-mapping-tools.org/download/\n"
            "     See also: https://www.pygmt.org/latest/install.html"
            "#error-loading-gmt-shared-library-at\n"
        )

    if gmt_path not in os.environ.get("PATH", ""):
        os.environ["PATH"] = gmt_path + os.pathsep + os.environ.get("PATH", "")
