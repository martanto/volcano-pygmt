from pathlib import Path

from volcano_plot.utils import slugify, km_to_degrees
from volcano_plot.config import load_config
from volcano_plot.constant import COUNTRY_REGIONS


load_config()
import pygmt


def add_inset(
    fig: pygmt.Figure,
    volcano: dict,
    country: str = "Indonesia",
) -> pygmt.Figure:
    """Add a country-level locator inset to an existing figure.

    Draws a small overview map in the bottom-left corner of ``fig`` showing
    the full extent of ``country`` with a red star marking the volcano
    position.

    Args:
        fig (pygmt.Figure): The PyGMT figure to add the inset to.
        volcano (dict): Mapping with at least the keys:

            * ``"lon"`` (float) — volcano longitude in decimal degrees.
            * ``"lat"`` (float) — volcano latitude in decimal degrees.

        country (str): Country name used to look up the bounding region in
            :data:`~volcano_plot.constant.COUNTRY_REGIONS`.  Defaults to
            ``"Indonesia"``.

    Returns:
        pygmt.Figure: The same ``fig`` object with the inset map added in-place.

    Raises:
        ValueError: If ``country`` is not a key in
            :data:`~volcano_plot.constant.COUNTRY_REGIONS`.

    Examples:
        >>> import pygmt
        >>> from volcano_plot.plot import add_inset
        >>> fig = pygmt.Figure()
        >>> volcano = {"lon": 107.65, "lat": -6.9}
        >>> fig = add_inset(fig, volcano, country="Indonesia")
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
    """Load SRTM earth relief and render hillshade, color relief, and/or contours.

    Downloads (or uses a cached copy of) the 3-arc-second SRTM grid for
    ``region`` and composites one or more of the following layers onto ``fig``:

    * **Hillshade** — a grayscale shaded-relief image (radiance 315°/45°).
    * **Color relief** — a colour-mapped elevation image, optionally with an
      accompanying colorbar.
    * **Contours** — elevation isolines with optional annotation labels.

    Args:
        fig (pygmt.Figure): The PyGMT figure to draw on.
        region (list[float]): Map extent as ``[lon_min, lon_max, lat_min, lat_max]``
            in decimal degrees.
        projection (str): PyGMT/GMT projection string, e.g. ``"M10c"``.
        hillshade (bool): Render a hillshade (gray shaded-relief) layer.
            Defaults to ``False``.
        contour (bool): Draw elevation contour lines.  Defaults to ``False``.
        contour_interval (float): Spacing between contour lines in metres.
            Defaults to ``100.0``.
        contour_annotation (float | None): Interval at which contour lines are
            labelled.  When ``None``, defaults to ``5 × contour_interval``.
        color_relief (bool): Render a colour-filled elevation image using
            ``relief_cmap``.  Only applied when ``contour`` is also ``True``.
            Defaults to ``False``.
        colorbar (bool): Add a colorbar showing the elevation scale.  Only
            relevant when ``color_relief`` is ``True``.  Defaults to ``False``.
        relief_cmap (str): GMT colormap name for the colour-relief image.
            Defaults to ``"gmt/haxby"``.  Any valid GMT CPT name is accepted,
            e.g. ``"geo"``, ``"topo"``, ``"dem1"``, ``"gray"``.

    Returns:
        pygmt.Figure: The same ``fig`` object with the requested relief layers
            added in-place.

    Examples:
        >>> import pygmt
        >>> from volcano_plot.plot import add_relief
        >>> fig = pygmt.Figure()
        >>> region = [106.5, 108.5, -8.0, -6.0]
        >>> fig = add_relief(fig, region, "M10c", hillshade=True, contour=True)
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
            annotation=f"{annotation}+f6p",
            pen=["c0.3p,gray40", "a0.5p,gray10"],
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
    """Create a PyGMT scientific map for a single volcano and its seismic stations.

    Composes a complete map including coastlines, optional terrain relief, station
    and volcano symbols, a legend, a scale bar, a north-arrow rose, and a
    country-level locator inset.

    Args:
        volcano (dict): Volcano metadata with at least the following keys:

            * ``"lon"`` (float) — longitude in decimal degrees.
            * ``"lat"`` (float) — latitude in decimal degrees.
            * ``"name"`` (str) — volcano name used for the title and label.

        stations (dict | None): Mapping of station code (str) to a dict
            containing ``"lon"`` (float) and ``"lat"`` (float).  When ``None``
            or an empty dict, no stations are plotted.  Defaults to ``None``.
        padding_km (float): Half-width of the map extent around the volcano
            centre in kilometres.  Defaults to ``5.0``.
        country (str): Country name for the locator inset passed to
            :func:`add_inset`.  Defaults to ``"Indonesia"``.
        hillshade (bool): Render a hillshade basemap layer.  Defaults to
            ``False``.
        contour (bool): Draw elevation contour lines.  Defaults to ``False``.
        contour_interval (float): Contour line spacing in metres.  Defaults to
            ``100.0``.
        contour_annotation (float | None): Contour label interval.  When
            ``None``, defaults to ``5 × contour_interval``.
        color_relief (bool): Render a colour-filled elevation image.  Defaults
            to ``False``.
        colorbar (bool): Add an elevation colorbar (requires
            ``color_relief=True``).  Defaults to ``False``.
        relief_cmap (str): GMT colormap for colour relief.  Defaults to
            ``"gmt/haxby"``.
        show_title (bool): Display the volcano name as the map title.
            Defaults to ``True``.

    Returns:
        pygmt.Figure: A fully rendered PyGMT figure ready to save or display.

    Examples:
        >>> from volcano_plot.plot import create_figure
        >>> volcano = {"lon": 107.65, "lat": -6.9, "name": "Example Volcano"}
        >>> fig = create_figure(volcano, padding_km=10.0, contour=True)
        >>> fig.savefig("example.png")
    """
    lon = volcano["lon"]
    lat = volcano["lat"]
    name = volcano["name"]

    lat_deg, lon_deg = km_to_degrees(padding_km, lat)

    region = [lon - lon_deg, lon + lon_deg, lat - lat_deg, lat + lat_deg]
    projection = "M10c"

    fig = pygmt.Figure()

    with pygmt.config(FONT_TITLE="10p", MAP_TITLE_OFFSET="2p"):
        title_frame = [f"+t{name}"] if show_title else []
        if title_frame:
            fig.basemap(region=region, projection=projection, frame=title_frame)

    with pygmt.config(FONT_ANNOT_PRIMARY="7p"):
        fig.coast(
            region=region,
            projection=projection,
            land=("white" if (hillshade or contour) else "lightgray"),
            water="white",
            shorelines="1/2.0p",
            borders="1/0.5p",
            frame="a",
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

    with pygmt.config(FONT_ANNOT_PRIMARY="6p"):
        fig.legend(position="JBR+jBR+o0.2c/0.6c", box="+gwhite+p0.5p")

    scale_km = round(padding_km * 0.4)
    with pygmt.config(FONT_ANNOT_PRIMARY="6p"):
        fig.basemap(
            region=region,
            projection=projection,
            map_scale=f"jBR+o0.2c/0.3c+w{scale_km}+f",
            rose="jTR+o0.3c+w1.2c",
        )

    add_inset(fig, volcano, country=country)

    return fig


def simple_plot(maps: list) -> list[Path]:
    """Render a batch of volcano maps and save each as a PNG file.

    Iterates over a list of map specification dicts, calls :func:`create_figure`
    for each entry, and writes the output to ``<cwd>/output/<slug>.png``.  The
    output directory is created automatically if it does not exist.

    Args:
        maps (list[dict]): Sequence of map specification dicts.  Each dict
            must contain:

            * ``"volcano"`` (dict) — passed directly to :func:`create_figure`;
              must include ``"lon"``, ``"lat"``, and ``"name"``.
            * ``"padding_km"`` (float) — map half-extent in kilometres.
            * ``"stations"`` (dict | None) — optional station dict.

            The following keys are optional and fall back to the
            :func:`create_figure` defaults when absent:

            * ``"country"`` (str) — defaults to ``"Indonesia"``.
            * ``"hillshade"`` (bool) — defaults to ``False``.
            * ``"contour"`` (bool) — defaults to ``False``.
            * ``"contour_interval"`` (float) — defaults to ``100.0``.
            * ``"contour_annotation"`` (float | None) — defaults to ``None``.
            * ``"color_relief"`` (bool) — defaults to ``False``.
            * ``"colorbar"`` (bool) — defaults to ``False``.
            * ``"relief_cmap"`` (str) — defaults to ``"gmt/haxby"``.
            * ``"show_title"`` (bool) — defaults to ``False``.

    Returns:
        list[Path]: Absolute :class:`pathlib.Path` objects for every PNG file
            written, in the same order as ``maps``.

    Examples:
        >>> from volcano_plot import simple_plot
        >>> maps = [
        ...     {
        ...         "volcano": {"lon": 107.65, "lat": -6.9, "name": "Tangkuban Parahu"},
        ...         "padding_km": 10.0,
        ...         "stations": {"TNGK": {"lon": 107.60, "lat": -6.85}},
        ...     }
        ... ]
        >>> files = simple_plot(maps)
        >>> print(files[0])  # e.g. .../output/tangkuban-parahu.png
    """
    output_dir = Path.cwd() / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    files = []

    for _map in maps:
        filename = slugify(_map["volcano"]["name"])
        filepath = output_dir / f"{filename}.png"
        padding_km = _map["padding_km"]

        fig = create_figure(
            volcano=_map["volcano"],
            stations=_map["stations"],
            padding_km=padding_km,
            country=_map.get("country", "Indonesia"),
            hillshade=_map.get("hillshade", False),
            contour=_map.get("contour", False),
            contour_interval=_map.get("contour_interval", 100.0),
            contour_annotation=_map.get("contour_annotation", None),
            color_relief=_map.get("color_relief", False),
            colorbar=_map.get("colorbar", False),
            relief_cmap=_map.get("relief_cmap", "gmt/haxby"),
            show_title=_map.get("show_title", False),
        )

        fig.savefig(filepath)

        files.append(filepath)

    return files
