from pathlib import Path

from volcano_pygmt.utils import slugify, km_to_degrees
from volcano_pygmt.config import load_config
from volcano_pygmt.logger import logger
from volcano_pygmt.constant import COUNTRY_REGIONS

import xarray as xr
from rioxarray.merge import merge_arrays


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
            :data:`~volcano_pygmt.constant.COUNTRY_REGIONS`.  Defaults to
            ``"Indonesia"``.

    Returns:
        pygmt.Figure: The same ``fig`` object with the inset map added in-place.

    Raises:
        ValueError: If ``country`` is not a key in
            :data:`~volcano_pygmt.constant.COUNTRY_REGIONS`.

    Examples:
        >>> import pygmt
        >>> from volcano_pygmt.plot import add_inset
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
            ``relief_cmap``.  Defaults to ``False``.
        colorbar (bool): Add a colorbar showing the elevation scale.  Only
            relevant when ``color_relief`` is ``True``.  Defaults to ``False``.
        relief_cmap (str): GMT colormap name for the colour-relief image.
            Defaults to ``"gmt/haxby"``.

    Returns:
        pygmt.Figure: The same ``fig`` object with the requested relief layers
            added in-place.

    Examples:
        >>> import pygmt
        >>> from volcano_pygmt.plot import add_relief
        >>> fig = pygmt.Figure()
        >>> region = [106.5, 108.5, -8.0, -6.0]
        >>> fig = add_relief(fig, region, "M10c", hillshade=True, contour=True)
    """
    logger.debug("Loading earth relief data for region {}", region)
    grid = pygmt.datasets.load_earth_relief(resolution="03s", region=region)

    # Compute gradient once; reused by both hillshade and color_relief if needed.
    dgrid = None
    if hillshade or color_relief:
        # normalize="e0.6" applies exponential normalization with a scale of 0.6,
        # which compresses the gradient range and produces a noticeably lighter hillshade.
        dgrid = pygmt.grdgradient(grid, radiance=[315, 45], normalize="e0.6")

    if hillshade:
        fig.grdimage(grid=grid, cmap="gray", shading=dgrid, projection=projection)

    if color_relief:
        cpt = pygmt.makecpt(cmap=relief_cmap, series=[0, float(grid.max())])
        fig.coast(region=region, projection=projection, land="c")
        fig.grdimage(grid=grid, cmap=cpt, shading=dgrid, projection=projection)
        fig.coast(Q=True)
        if colorbar:
            fig.colorbar(frame=["x+lelevation", "y+lm"])

    if contour:
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


def plot_from_dem(
    fig: pygmt.Figure,
    dem_files: str | list[str],
    projection: str,
    region: list[float] | None = None,
    hillshade: bool = False,
    contour: bool = False,
    contour_interval: float = 100.0,
    contour_annotation: float | None = None,
    color_relief: bool = False,
    colorbar: bool = False,
    relief_cmap: str = "gmt/haxby",
    water_color: str = "lightblue",
) -> pygmt.Figure:
    """Load one or more local DEM files and render hillshade, color relief, and/or contours.

    Reads the given GeoTIFF DEM file(s), merges them when more than one is
    supplied, and composites one or more of the following layers onto ``fig``:

    * **Hillshade** — a grayscale shaded-relief image (radiance 315°/45°).
    * **Color relief** — a colour-mapped elevation image, optionally with a colorbar.
    * **Contours** — elevation isolines with optional annotation labels.

    Args:
        fig (pygmt.Figure): The PyGMT figure to draw on.
        dem_files (str | list[str]): Path or list of paths to GeoTIFF DEM files.
            When multiple files are given they are merged before plotting.
        projection (str): PyGMT/GMT projection string, e.g. ``"M10c"``.
        region (list[float] | None): Map extent as ``[lon_min, lon_max, lat_min, lat_max]``
            used to clip the DEM and passed to PyGMT rendering calls.  When
            ``None``, the full DEM extent is used.  Defaults to ``None``.
        hillshade (bool): Render a hillshade layer.  Defaults to ``False``.
        contour (bool): Draw elevation contour lines.  Defaults to ``False``.
        contour_interval (float): Spacing between contour lines in metres.
            Defaults to ``100.0``.
        contour_annotation (float | None): Interval at which contour lines are
            labelled.  When ``None``, defaults to ``5 × contour_interval``.
        color_relief (bool): Render a colour-filled elevation image.  Defaults
            to ``False``.
        colorbar (bool): Add a colorbar showing the elevation scale.  Defaults
            to ``False``.
        relief_cmap (str): GMT colormap name for the colour-relief image.
            Defaults to ``"gmt/haxby"``.
        water_color (str): Fill colour for sea/water areas (pixels with
            elevation ≤ 0 are masked to transparent).  Accepted values:
            ``"white"``, ``"blue"``, ``"lightblue"``, ``"lightgray"``.
            Defaults to ``"lightblue"``.

    Returns:
        pygmt.Figure: The same ``fig`` object with the requested relief layers
            added in-place.

    Examples:
        >>> import pygmt
        >>> from volcano_pygmt.plot import plot_from_dem
        >>> fig = pygmt.Figure()
        >>> region = [112.5, 113.3, -8.5, -7.7]
        >>> fig = plot_from_dem(fig, "dem.tif", "M10c", region=region, hillshade=True, contour=True)
    """
    if isinstance(dem_files, str):
        dem_files = [dem_files]

    logger.debug("Loading {} DEM file(s)", len(dem_files))
    arrays = [xr.open_dataarray(f, engine="rasterio") for f in dem_files]

    # DEMNAS and similar tiles often lack an embedded CRS; assume WGS84.
    arrays = [a if a.rio.crs else a.rio.write_crs("EPSG:4326") for a in arrays]

    if len(arrays) > 1:
        grid = merge_arrays(arrays).squeeze()
    else:
        grid = arrays[0].squeeze()

    if region is not None:
        grid = grid.rio.clip_box(
            minx=region[0], maxx=region[1], miny=region[2], maxy=region[3]
        )
    else:
        region = [
            float(grid.x.min()),
            float(grid.x.max()),
            float(grid.y.min()),
            float(grid.y.max()),
        ]

    grid = grid.where(grid > 0)

    dgrid = None
    if hillshade:
        dgrid = pygmt.grdgradient(grid, radiance=[315, 45], normalize="e0.6")
        fig.grdimage(
            grid=grid, cmap="gray", shading=dgrid, projection=projection, region=region
        )

    if color_relief:
        cpt = pygmt.makecpt(
            cmap=relief_cmap, series=[float(grid.min()), float(grid.max())]
        )
        fig.grdimage(
            grid=grid, cmap=cpt, shading=dgrid, projection=projection, region=region
        )
        if colorbar:
            fig.colorbar(frame=["x+lelevation", "y+lm"])

    if contour:
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
            region=region,
        )

    # Plot water color
    fig.coast(
        region=region, projection=projection, water=water_color, shorelines="1/2.0p"
    )

    return fig


def create_figure(
    volcano: dict,
    stations: dict | None = None,
    padding_km: float = 5.0,
    country: str = "Indonesia",
    dem_files: list[str] | None = None,
    hillshade: bool = False,
    contour: bool = False,
    contour_interval: float = 100.0,
    contour_annotation: float | None = None,
    color_relief: bool = False,
    colorbar: bool = False,
    relief_cmap: str = "gmt/haxby",
    show_title: bool = True,
    water_color: str = "lightblue",
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
        dem_files (list[str] | None): List of DEM files. Defaults to ``None``.
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
        water_color (str): Fill colour for sea/water areas when ``dem_files``
            is provided.  Accepted values: ``"white"``, ``"blue"``,
            ``"lightblue"``, ``"lightgray"``.  Ignored when no DEM files are
            given (water is always ``"white"`` in that case).  Defaults to
            ``"lightblue"``.

    Returns:
        pygmt.Figure: A fully rendered PyGMT figure ready to save or display.

    Examples:
        >>> from volcano_pygmt.plot import create_figure
        >>> volcano = {"lon": 107.65, "lat": -6.9, "name": "Example Volcano"}
        >>> fig = create_figure(volcano, padding_km=10.0, contour=True)
        >>> fig.savefig("example.png")
    """
    lon = volcano["lon"]
    lat = volcano["lat"]
    name = volcano["name"]

    logger.info("Creating figure for volcano: {}", name)

    lat_deg, lon_deg = km_to_degrees(padding_km, lat)

    region = [lon - lon_deg, lon + lon_deg, lat - lat_deg, lat + lat_deg]
    projection = "M10c"

    fig = pygmt.Figure()

    # 1. Load Basemap
    with pygmt.config(FONT_TITLE="10p", MAP_TITLE_OFFSET="2p"):
        title_frame = [f"+t{name}"] if show_title else []
        if title_frame:
            fig.basemap(region=region, projection=projection, frame=title_frame)

    # 2. Add coast color (land, water, shorelines, etc)
    with pygmt.config(FONT_ANNOT_PRIMARY="7p"):
        fig.coast(
            region=region,
            projection=projection,
            land=("white" if (hillshade or contour or color_relief) else "lightgray"),
            water=(None if dem_files else "white"),
            shorelines=None if dem_files else "1/2.0p",
            borders="1/0.5p",
            frame="a",
        )

    # 3. Add relief (hillshade, contour, or color)
    if hillshade or contour or color_relief:
        if dem_files:
            plot_from_dem(
                fig,
                dem_files,
                projection,
                region=region,
                hillshade=hillshade,
                contour=contour,
                contour_interval=contour_interval,
                contour_annotation=contour_annotation,
                color_relief=color_relief,
                colorbar=colorbar,
                relief_cmap=relief_cmap,
                water_color=water_color,
            )
        else:
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

    # 4. Plot volcano location
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

    # 5. Plot location station
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

    # 6. Add legend
    with pygmt.config(FONT_ANNOT_PRIMARY="6p"):
        fig.legend(position="JBR+jBR+o0.2c/0.6c", box="+gwhite+p0.5p")

    # 7. Add scale bar
    scale_km = max(1, round(padding_km * 0.4))
    with pygmt.config(FONT_ANNOT_PRIMARY="6p"):
        fig.basemap(
            region=region,
            projection=projection,
            map_scale=f"jBR+o0.2c/0.3c+w{scale_km}+f",
            rose="jTR+o0.3c+w1.2c",
        )

    # 8. Add inset
    add_inset(fig, volcano, country=country)

    return fig


def plot(
    maps: list, file_type: str = "png", water_color: str = "lightblue"
) -> list[Path]:
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

            The following keys are optional and fall back to the
            :func:`create_figure` defaults when absent:

            * ``"stations"`` (dict | None) — defaults to ``None``.
            * ``"country"`` (str) — defaults to ``"Indonesia"``.
            * ``"hillshade"`` (bool) — defaults to ``False``.
            * ``"contour"`` (bool) — defaults to ``False``.
            * ``"contour_interval"`` (float) — defaults to ``100.0``.
            * ``"contour_annotation"`` (float | None) — defaults to ``None``.
            * ``"color_relief"`` (bool) — defaults to ``False``.
            * ``"colorbar"`` (bool) — defaults to ``False``.
            * ``"relief_cmap"`` (str) — defaults to ``"gmt/haxby"``.
            * ``"show_title"`` (bool) — defaults to ``False``.
            * ``"water_color"`` (str) — defaults to ``"lightblue"``.

        file_type (str): Output file format, either ``"png"`` or ``"pdf"``.
            Defaults to ``"png"``.
        water_color (str): Fill colour for sea/water areas when ``dem_files``
            is provided.  Accepted values: ``"white"``, ``"blue"``,
            ``"lightblue"``, ``"lightgray"``.  Ignored when no DEM files are
            given (water is always ``"white"`` in that case).  Defaults to
            ``"lightblue"``.

    Returns:
        list[Path]: Absolute :class:`pathlib.Path` objects for every file
            written, in the same order as ``maps``.

    Examples:
        >>> from volcano_pygmt import plot
        >>> maps = [
        ...     {
        ...         "volcano": {"lon": 107.65, "lat": -6.9, "name": "Tangkuban Parahu"},
        ...         "padding_km": 10.0,
        ...         "stations": {"TNGK": {"lon": 107.60, "lat": -6.85}},
        ...     }
        ... ]
        >>> files = plot(maps)
        >>> print(files[0])  # e.g. .../output/tangkuban-parahu.png
    """
    if file_type not in ("png", "pdf"):
        raise ValueError(f"file_type must be 'png' or 'pdf', got '{file_type}'")

    output_dir = Path.cwd() / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    files = []

    for _map in maps:
        filename = slugify(_map["volcano"]["name"])
        filepath = output_dir / f"{filename}.{file_type}"

        fig = create_figure(
            volcano=_map["volcano"],
            stations=_map.get("stations"),
            padding_km=_map["padding_km"],
            country=_map.get("country", "Indonesia"),
            dem_files=_map.get("dem_files", None),
            hillshade=_map.get("hillshade", False),
            contour=_map.get("contour", False),
            contour_interval=_map.get("contour_interval", 100.0),
            contour_annotation=_map.get("contour_annotation", None),
            color_relief=_map.get("color_relief", False),
            colorbar=_map.get("colorbar", False),
            relief_cmap=_map.get("relief_cmap", "gmt/haxby"),
            show_title=_map.get("show_title", False),
            water_color=_map.get("water_color", water_color),
        )

        fig.savefig(filepath)
        logger.info("Saved figure to {}", filepath)

        files.append(filepath)

    return files
