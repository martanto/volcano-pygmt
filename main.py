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
            style="a0.3c",  # star inset
            fill="red",
            pen="0.5p,black",
        )

    return fig


def add_relief(
    fig: pygmt.Figure,
    region: list[float],
    projection: str,
    hillshade: bool = False,
    contour: bool = False,
    contour_interval: float = 100.0,
    contour_annotation: float | None = None,
    color_relief: bool = False,
    colorbar: bool = False,
    relief_cmap: str = "gmt/haxby",
) -> pygmt.Figure:
    """Load earth relief and render hillshade, color relief, and/or contours onto the figure.

    Args:
        fig: The PyGMT figure to draw on.
        region: Map region as [lon_min, lon_max, lat_min, lat_max].
        projection: PyGMT projection string.
        hillshade: Whether to render a hillshade layer. Defaults to False.
        contour: Whether to draw elevation contour lines. Defaults to False.
        contour_interval: Contour interval in meters. Defaults to 100.0.
        contour_annotation: Interval at which contour lines are labeled. If None,
            defaults to 5x the contour_interval.
        color_relief: Whether to render a color-filled relief map. Defaults to False.
        colorbar: Whether to add a colorbar showing the elevation scale. Only
            relevant when color_relief is True. Defaults to False.
        relief_cmap: GMT colormap name for color relief. Defaults to "gmt/haxby".
            Use "gray" for a light-gray-to-gray grayscale rendering. Any valid GMT
            colormap name works — e.g. "geo", "topo", "dem1", "gray".

    Returns:
        The same pygmt.Figure with relief layers added.
    """
    grid = pygmt.datasets.load_earth_relief(resolution="03s", region=region)

    if hillshade:
        # normalize="e0.6" applies exponential normalization with a scale of 0.6,
        # which compresses the gradient range and produces a noticeably lighter hillshade.
        dgrid = pygmt.grdgradient(grid, radiance=[315, 45], normalize="e0.6")
        fig.grdimage(grid=grid, cmap="gray", shading=dgrid, projection=projection)

    if contour:
        if color_relief:
            dgrid = (
                pygmt.grdgradient(grid, radiance=[315, 45], normalize="e0.6")
                if hillshade
                else None
            )
            cpt = pygmt.makecpt(cmap=relief_cmap, series=[0, float(grid.max())])
            fig.coast(region=region, projection=projection, land="c")
            fig.grdimage(grid=grid, cmap=cpt, shading=dgrid, projection=projection)
            fig.coast(Q=True)
            if colorbar:
                fig.colorbar(frame=["x+lelevation", "y+lm"])

        annotation = (
            contour_annotation
            if contour_annotation is not None
            else contour_interval * 5
        )
        fig.grdcontour(
            grid=grid,
            levels=contour_interval,
            annotation=annotation,
            pen=["c0.3p,gray30", "a0.5p,gray10"],
            projection=projection,
        )

    return fig


def create_figure(
    volcano: dict,
    stations: dict | None = None,
    padding_km: float = 5.0,
    country: str = "Indonesia",
    hillshade: bool = False,
    contour: bool = False,
    contour_interval: float = 100.0,
    contour_annotation: float | None = None,
    color_relief: bool = False,
    colorbar: bool = False,
    relief_cmap: str = "gmt/haxby",
    show_title: bool = True,
) -> pygmt.Figure:
    """Create a PyGMT scientific map for a volcano and its stations.

    Args:
        volcano: Dict with keys lon, lat, elev, name.
        stations: Dict mapping station code to dict with lon and lat.
        padding_km: Map extent padding around the volcano in kilometers. Defaults to 5.0.
        country: Country name for the locator inset. Defaults to "Indonesia".
        hillshade: Whether to render a hillshade basemap. Defaults to False.
        contour: Whether to draw elevation contour lines. Defaults to False.
        contour_interval: Contour interval in meters. Defaults to 100.0.
        contour_annotation: Interval at which contour lines are labeled. Defaults to
            5x contour_interval.
        color_relief: Whether to render a color-filled relief map. Defaults to False.
        colorbar: Whether to add a colorbar (used with color_relief). Defaults to False.
        relief_cmap: GMT colormap for color relief. Defaults to "gmt/haxby".
            Use "gray" for a light-gray-to-gray grayscale rendering.
        show_title: Whether to display the volcano name as the map title. Defaults to True.

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
        title_frame = ["af", f"+t{name}"] if show_title else ["af"]
        fig.basemap(region=region, projection=projection, frame=title_frame)

    fig.coast(
        region=region,
        projection=projection,
        land=("white" if (hillshade or contour) else "lightgray"),
        water="white",
        shorelines="1/2.0p",
        borders="1/0.5p",
        frame="ag",
    )

    if hillshade or contour or color_relief:
        add_relief(
            fig,
            region,
            projection,
            hillshade=hillshade,
            contour=contour,
            contour_interval=contour_interval,
            contour_annotation=contour_annotation,
            color_relief=color_relief,
            colorbar=colorbar,
            relief_cmap=relief_cmap,
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
        font="10p,Helvetica-Bold,black",
        offset="0/-0.4c",
    )

    # Plot stations if not None
    if stations:
        for index, (code, sta) in enumerate(stations.items()):
            fig.plot(
                x=sta["lon"],
                y=sta["lat"],
                style="i0.3c",
                fill="green",
                pen="0.8p,black",
                label=(
                    "Station+S0.25c" if index == 0 else None
                ),  # +S0.25c sets the legend symbol size to 0.25 cm, which matches the 7p font size
            )
            fig.text(
                x=sta["lon"],
                y=sta["lat"],
                text=code,
                font="7p,Helvetica-Bold,black",
                offset="0/-0.4c",
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
            hillshade=map.get("hillshade", False),
            contour=map.get("contour", False),
            contour_interval=map.get("contour_interval", 100.0),
            contour_annotation=map.get("contour_annotation", None),
            color_relief=map.get("color_relief", False),
            colorbar=map.get("colorbar", False),
            relief_cmap=map.get("relief_cmap", "gmt/haxby"),
            show_title=map.get("show_title", False),
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
            "color_relief": False,
            "contour": True,
            "contour_interval": 300.0,
            "contour_annotation": 600.0,
            "colorbar": True,
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
            "color_relief": False,
            "contour": True,
            "contour_interval": 300.0,
            "contour_annotation": 300.0,
            "colorbar": True,
        },
        {
            "padding_km": 5,
            "volcano": {"lon": 125.3667, "lat": 2.3031, "elev": 703, "name": "Ruang"},
            "stations": {
                "VG.RUA3.EHZ.00": {"lat": 2.3196, "lon": 125.3814},
            },
            "color_relief": False,
            "contour": True,
            "contour_interval": 200.0,
            "contour_annotation": 200.0,
            "colorbar": True,
        },
    ]

    main(_maps)
