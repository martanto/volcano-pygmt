import math
from pathlib import Path

from volcano_plot import pygmt


COUNTRY_REGIONS: dict[str, list[float]] = {
    "Indonesia": [94, 141, -12, 8],
}


def km_to_degrees(km: float, lat: float) -> tuple[float, float]:
    """Convert a distance in kilometers to degrees of latitude and longitude.

    Args:
        km: Distance in kilometers.
        lat: Reference latitude in decimal degrees (used for longitude conversion).

    Returns:
        A tuple of (lat_deg, lon_deg).
    """
    lat_deg = km / 111.32
    lon_deg = km / (111.32 * math.cos(math.radians(lat)))
    return lat_deg, lon_deg


def add_inset(
    fig: pygmt.Figure,
    volcano: dict,
    country: str = "Indonesia",
) -> pygmt.Figure:
    """Add a country-level locator inset to an existing figure.

    Args:
        fig: The PyGMT figure to add the inset to.
        volcano: Dict with keys lon and lat for the volcano location.
        country: Country name to use as the inset region. Defaults to "Indonesia".

    Returns:
        The same pygmt.Figure with the inset added.

    Raises:
        ValueError: If country is not in the supported COUNTRY_REGIONS dict.
    """
    if country not in COUNTRY_REGIONS:
        raise ValueError(
            f"Country '{country}' is not supported. "
            f"Available options: {list(COUNTRY_REGIONS.keys())}"
        )

    region = COUNTRY_REGIONS[country]

    inset_width = 3.0
    lon_span = region[1] - region[0]
    lat_span = region[3] - region[2]
    inset_height = round(inset_width * (lat_span / lon_span), 2)

    with fig.inset(
        position=f"JBL+jBL+o0.2c+w{inset_width}c/{inset_height}c", box="+gwhite+p0.5p"
    ):
        fig.coast(
            region=region,
            projection="M3c",
            land="lightgray",
            water="white",
            shorelines="1/0.3p",
            borders="1/0.3p",
        )
        fig.plot(
            x=volcano["lon"],
            y=volcano["lat"],
            style="a0.4c",
            fill="red",
            pen="0.5p,black",
        )

    return fig


def create_figure(
    volcano: dict,
    stations: dict | None = None,
    padding_km: float = 5.0,
    country: str = "Indonesia",
) -> pygmt.Figure:
    """Create a PyGMT scientific map for a volcano and its stations.

    Args:
        volcano: Dict with keys lon, lat, elev, name.
        stations: Dict mapping station code to dict with lon and lat.
        padding_km: Map extent padding around the volcano in kilometers. Defaults to 5.0.
        country: Country name for the locator inset. Defaults to "Indonesia".

    Returns:
        A pygmt.Figure with the rendered map.
    """
    lon = volcano["lon"]
    lat = volcano["lat"]
    name = volcano["name"]

    lat_deg, lon_deg = km_to_degrees(padding_km, lat)

    region = [lon - lon_deg, lon + lon_deg, lat - lat_deg, lat + lat_deg]
    projection = "M10c"

    fig = pygmt.Figure()

    with pygmt.config(FONT_TITLE="10p", MAP_TITLE_OFFSET="2p"):
        fig.basemap(region=region, projection=projection, frame=["af", f"+t{name}"])

    fig.coast(
        region=region,
        projection=projection,
        land="lightgray",
        water="white",
        shorelines="1/0.5p",
        borders="1/0.5p",
        frame="ag",
    )

    fig.plot(
        x=lon,
        y=lat,
        style="t0.4c",
        fill="red",
        pen="0.5p,black",
        label="Volcano+S0.25c",
    )

    fig.text(
        x=lon,
        y=lat,
        text=name,
        font="10p,Helvetica,black",
        offset="0/-0.4c",
    )

    # Plot stations if not None
    if stations:
        for index, (code, sta) in enumerate(stations.items()):
            fig.plot(
                x=sta["lon"],
                y=sta["lat"],
                style="i0.3c",
                fill="blue",
                pen="0.8p,black",
                label=(
                    "Station+S0.25c" if index == 0 else None
                ),  # +S0.25c sets the legend symbol size to 0.25 cm, which matches the 7p font size
            )
            fig.text(
                x=sta["lon"],
                y=sta["lat"],
                text=code,
                font="8p,Helvetica,black",  # 10p means 10 points, where "p" stands for points
                offset="0/0.4c",
            )

    with pygmt.config(FONT_ANNOT_PRIMARY="7p"):
        fig.legend(position="JBR+jBR+o0.2c", box="+gwhite+p0.5p")

    add_inset(fig, volcano, country=country)

    return fig


def main(maps: list):
    output_dir = Path.cwd() / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    files = []

    for map in maps:
        filepath = output_dir / f"{map['volcano']['name']}.png"
        padding_km = map["padding_km"]

        fig = create_figure(
            volcano=map["volcano"],
            stations=map["stations"],
            padding_km=padding_km,
            country=map.get("country", "Indonesia"),
        )

        fig.savefig(filepath)

        files.append(filepath)

    return files


if __name__ == "__main__":
    _maps = [
        {
            "padding_km": 20,
            "volcano": {"lon": 112.922, "lat": -8.108, "elev": 3672, "name": "Semeru"},
            "stations": {
                "VG.LEKR.EHZ.00": {"lat": -8.137244444, "lon": 112.9858444},
            },
        },
        {
            "padding_km": 10,
            "volcano": {
                "lon": 122.775,
                "lat": -8.542,
                "elev": 3672,
                "name": "Lewotobi Laki-laki",
            },
            "stations": {
                "VG.OJN.EHZ.00": {"lat": -8.502944444, "lon": 122.7737222},
            },
        },
        {
            "padding_km": 5,
            "volcano": {"lon": 125.3667, "lat": 2.3031, "elev": 703, "name": "Ruang"},
            "stations": {
                "VG.RUA3.EHZ.00": {"lat": 2.3196, "lon": 125.3814},
            },
        },
    ]

    main(_maps)
