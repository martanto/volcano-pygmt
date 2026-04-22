import os
from pathlib import Path

from dotenv import load_dotenv


_VAR = "GMT_LIBRARY_PATH"


def load_config() -> None:
    """Configure ``GMT_LIBRARY_PATH`` for PyGMT, checking environment then ``.env``.

    Resolution order:

    1. User / system environment variable (already present in ``os.environ``).
    2. ``.env`` file in the current working directory (loaded only when the
       variable is absent from the environment).

    After the variable is resolved, its value is prepended to ``PATH`` so that
    PyGMT can locate the GMT shared library at runtime.

    Returns:
        None

    Raises:
        OSError: If ``GMT_LIBRARY_PATH`` is not found in the environment or in
            the ``.env`` file.

    Examples:
        >>> from volcano_plot.config import load_config
        >>> load_config()  # checks env first, then .env; raises OSError if missing
    """
    # 1. Check user / system environment first.
    gmt_path = os.environ.get(_VAR, "").strip()

    # 2. Fall back to .env only when the variable is absent.
    if not gmt_path:
        env_file = Path.cwd() / ".env"
        load_dotenv(env_file, override=False)
        gmt_path = os.environ.get(_VAR, "").strip()

    if not gmt_path:
        raise OSError(
            f"{_VAR} is not set.\n\n"
            "To fix this, choose one of:\n"
            f"  a) Set {_VAR} as a user or system environment variable.\n"
            f"  b) Add {_VAR}=<path> to a .env file in your project root.\n\n"
            "     Example value: D:\\Projects\\gmt6\\bin\n\n"
            "  Download GMT from https://www.generic-mapping-tools.org/download/\n"
            "  See also: https://www.pygmt.org/latest/install.html"
            "#error-loading-gmt-shared-library-at\n"
        )

    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    if gmt_path not in path_dirs:
        os.environ["PATH"] = gmt_path + os.pathsep + os.environ.get("PATH", "")
