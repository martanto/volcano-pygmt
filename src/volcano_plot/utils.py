import os
import re
import math


def km_to_degrees(km: float, lat: float) -> tuple[float, float]:
    """Convert a distance in kilometers to degrees of latitude and longitude.

    Uses the standard approximation of 111.32 km per degree of latitude and
    adjusts longitude degrees by the cosine of the reference latitude.

    Args:
        km (float): Distance in kilometers to convert.
        lat (float): Reference latitude in decimal degrees used to scale the
            longitude conversion.

    Returns:
        tuple[float, float]: A ``(lat_deg, lon_deg)`` tuple where both values
            represent the equivalent angular distance in decimal degrees.

    Raises:
        ZeroDivisionError: If ``lat`` is exactly ±90°, ``cos(lat)`` is zero and
            longitude conversion is undefined.

    Examples:
        >>> lat_deg, lon_deg = km_to_degrees(10.0, 0.0)
        >>> round(lat_deg, 4)
        0.0898
        >>> lat_deg, lon_deg = km_to_degrees(10.0, 45.0)
        >>> round(lon_deg, 4)
        0.127
    """
    lat_deg = km / 111.32
    lon_deg = km / (111.32 * math.cos(math.radians(lat)))
    return lat_deg, lon_deg


def slugify(text: str, hyphen: str = "-") -> str:
    """Convert arbitrary text into a safe filename slug.

    Lowercases the input, replaces whitespace and underscores with the chosen
    separator, strips non-alphanumeric characters (except the separator), and
    collapses consecutive separators into one.

    Args:
        text (str): Text to slugify.
        hyphen (str): Separator character to use. Defaults to ``"-"``.

    Returns:
        str: Slugified filename-safe string.

    Examples:
        >>> slugify("Hello World")
        'hello-world'
        >>> slugify("Hello World", hyphen="_")
        'hello_world'
        >>> slugify("  Multiple   Spaces  ")
        'multiple-spaces'
    """
    s = text.lower()
    s = re.sub(r"[\s_]+", hyphen, s)
    escaped = re.escape(hyphen)
    s = re.sub(rf"[^a-z0-9{escaped}]", "", s)
    s = re.sub(rf"{escaped}+", hyphen, s)
    return s.strip(hyphen)


def ensure_dir(path: str) -> str:
    """Create a directory (and any missing parents) if it does not already exist.

    A thin wrapper around ``os.makedirs(path, exist_ok=True)`` that returns
    the path so callers can chain it inline, e.g. as a default argument.

    Args:
        path (str): Absolute or relative directory path to create.

    Returns:
        str: The same ``path`` that was passed in, unchanged.

    Raises:
        PermissionError: If the process lacks write permission for the target
            location or one of its parent directories.
        NotADirectoryError: If a component of ``path`` already exists as a file
            rather than a directory.

    Examples:
        >>> import tempfile, os
        >>> tmp = tempfile.mkdtemp()
        >>> result = ensure_dir(os.path.join(tmp, "a", "b"))
        >>> os.path.isdir(result)
        True
    """
    os.makedirs(path, exist_ok=True)
    return path
