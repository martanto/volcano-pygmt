import math
from pathlib import Path

from volcano_plot import pygmt


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


def create_figure(
    volcano: dict, stations: dict, padding_km: float = 20.0
) -> pygmt.Figure:
    """Create a PyGMT scientific map for a volcano and its stations.

    Args:
        volcano: Dict with keys lon, lat, elev, name.
        stations: Dict mapping station code to dict with lon and lat.
        padding_km: Map extent padding around the volcano in kilometers. Defaults to 20.0.

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
    fig.basemap(region=region, projection=projection, frame=["af", f"+t{name}"])
    fig.coast(
        region=region,
        projection=projection,
        land="lightgray",
        water="lightblue",
        shorelines="0.5p,black",
        borders="1/0.5p,gray",
    )

    fig.plot(x=lon, y=lat, style="t0.4c", fill="red", pen="0.5p,black", label="Volcano")

    for code, sta in stations.items():
        fig.plot(
            x=sta["lon"],
            y=sta["lat"],
            style="i0.3c",
            fill="blue",
            pen="0.5p,black",
            label="Station",
        )
        fig.text(
            x=sta["lon"],
            y=sta["lat"],
            text=code,
            font="6p,Helvetica,black",
            offset="0/0.2c",
        )

    fig.legend(position="JBR+jBR+o0.2c", box="+gwhite+p0.5p")

    return fig


def main(maps: list):
    output_dir = Path.cwd() / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    files = []

    for map in maps:
        filepath = output_dir / f"{map['volcano']['name']}.png"

        fig = create_figure(map["volcano"], map["stations"])
        fig.savefig(filepath)

        files.append(filepath)

    return files


if __name__ == "__main__":
    maps = [
        {
            "volcano": {"lon": 112.922, "lat": -8.108, "elev": 3672, "name": "Semeru"},
            "stations": {
                "LEKR": {"lat": -8.137244444, "lon": 112.9858444},
            },
        },
        {
            "volcano": {
                "lon": 122.775,
                "lat": -8.542,
                "elev": 3672,
                "name": "Lewotobi Laki-laki",
            },
            "stations": {
                "OJN": {"lat": -8.502944444, "lon": 122.7737222},
            },
        },
        {
            "volcano": {"lon": 125.3667, "lat": 2.3031, "elev": 703, "name": "Ruang"},
            "stations": {
                "RUA3": {"lat": 2.3196, "lon": 125.3814},
            },
        },
    ]

    main(maps)
