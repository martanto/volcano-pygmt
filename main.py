import os
import sys
import atexit

from volcano_pygmt import plot


def _suppress_gmt_shutdown_noise() -> None:
    # GMT's C library cleanup fires after Python tears down sys.excepthook,
    # causing spurious "Error in sys.excepthook" lines on Windows.
    # Redirecting fd 2 at the OS level silences them even from C code.
    sys.stderr.flush()
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull_fd, 2)
    os.close(devnull_fd)


atexit.register(_suppress_gmt_shutdown_noise)


if __name__ == "__main__":
    _maps = [
        {
            "volcano": {"lon": 112.922, "lat": -8.108, "elev": 3672, "name": "Semeru"},
            "stations": {
                "VG.LEKR.EHZ.00": {"lat": -8.137244444, "lon": 112.9858444},
            },
            "dem_files": [
                "DEMNAS_1608-12_v1.0.tif",
                "DEMNAS_1608-21_v1.0.tif",
                "DEMNAS_1607-42_v1.0.tif",
                "DEMNAS_1607-44_v1.0.tif",
                "DEMNAS_1607-53_v1.0.tif",
            ],
            "padding_km": 20,
            "color_relief": False,
            "contour": True,
            "contour_interval": 300.0,
            "contour_annotation": 600.0,
            "colorbar": True,
        },
        {
            "volcano": {
                "lon": 122.775,
                "lat": -8.542,
                "elev": 3672,
                "name": "Lewotobi Laki-laki",
            },
            "stations": {
                "VG.OJN.EHZ.00": {"lat": -8.502944444, "lon": 122.7737222},
            },
            "dem_files": [
                "DEMNAS_2207-33_v1.0.tif",
                "DEMNAS_2207-34_v1.0.tif",
                "DEMNAS_2207-61_v1.0.tif",
                "DEMNAS_2207-62_v1.0.tif",
            ],
            "padding_km": 10,
            "color_relief": False,
            "contour": True,
            "contour_interval": 100.0,
            "contour_annotation": 300.0,
            "colorbar": True,
        },
        {
            "volcano": {"lon": 125.3667, "lat": 2.3031, "elev": 703, "name": "Ruang"},
            "stations": {
                "VG.RUA3.EHZ.00": {"lat": 2.3196, "lon": 125.3814},
            },
            "dem_files": ["output_hh.tif"],
            "padding_km": 5,
            "hillshade": False,
            "color_relief": False,
            "relief_cmap": "white",
            "contour": True,
            "contour_interval": 30.0,
            "contour_annotation": 300.0,
            "colorbar": True,
            "water_color": "white",
        },
    ]

    plot(_maps, "png")
