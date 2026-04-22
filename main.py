from volcano_plot import simple_plot


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

    simple_plot(_maps)
