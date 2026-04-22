from pathlib import Path

from volcano_plot import pygmt


def create_figure(volcano: dict, stations: dict) -> pygmt.Figure:
    """Create a PyGMT scientific map for a volcano and its stations.

    Args:
        volcano: Dict with keys lon, lat, elev, name.
        stations: Dict mapping station code to dict with lon and lat.

    Returns:
        A pygmt.Figure with the rendered map.
    """
    lon = volcano["lon"]
    lat = volcano["lat"]
    name = volcano["name"]
    padding = 0.5

    region = [lon - padding, lon + padding, lat - padding, lat + padding]
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
            "volcano": {"lon": 125.3671, "lat": 2.3058, "elev": 703, "name": "Ruang"},
            "stations": {
                "RUA3": {"lat": 2.3196, "lon": 125.3814},
            },
        },
    ]

    main(maps)
