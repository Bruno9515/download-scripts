import cdsapi
import calendar
from pathlib import Path
import xarray as xr
import pandas as pd
import glob

c = cdsapi.Client()

parametros = [
    {
        #"model": "bom",
        #"months" : ["01","02","03","10","11","12"],
        #"years": [2007,2008,2009,2010,2020,2021,2022,2023,2024,2025]#2007,2008,2009
        "model" : "cma",
        "months" : ["01","02","03","10","11","12"],
        "years" : list(range(2007, 2026))},
    {
        "model" : "cptec",
        "months" : ["01","02","03","10","11","12"],
        "years" : list(range(2008, 2021))},
    {
        "model" : "dwd",
        "months" : ["01","02","03","10","11","12"],
        "years" : list(range(2020, 2027))},
    {
        "model" : "eccc",
        "months" : ["01","02","03","10","11","12"],
        "years" : list(range(2007, 2027))},
    {
        "model" : "ecmwf",
        "months" : ["01","02","03","10","11","12"],
        "years" : list(range(2006, 2027))},
    {
        "model" : "imd",
        "months" : ["01","02","03","10","11","12"],
        "years" : list(range(2020, 2027))},
    {
        "model" : "jma",
        "months" : ["01","02","03","10","11","12"],
        "years" : list(range(2006, 2027))},
    {
        "model" : "kma",
        "months" : ["01","02","03","10","11","12"],
        "years" : list(range(2007, 2027))},
    {
        "model" : "mf",
        "months" : ["01","02","03","10","11","12"],
        "years" : list(range(2007, 2027))},
    {
        "model" : "ncep",
        "months" : ["01","02","03","10","11","12"],
        "years" : list(range(2007, 2027))},
    {
        "model" : "ncmrwf",
        "months" : ["01","02","03","10","11","12"],
        "years" : list(range(2017, 2026))},
    {
        "model" : "ukmo",
        "months" : ["01","02","03","10","11","12"],
        "years" : list(range(2006, 2027))
    }
]

variables = [
    "total_precipitation",
    "2m_temperature",
    "2m_dewpoint_temperature",
    "surface_pressure",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind"
]

for p in parametros:

    model = p["model"]

    for y in p["years"]:

        for month in p["months"]:
            days_in_month = calendar.monthrange(
                y,
                int(month)
            )[1]

            days = [
                f"{d:02d}"
                for d in range(1, days_in_month + 1)
            ]
            outdir = Path(model) / str(y)
            outdir.mkdir(
                parents=True,
                exist_ok=True
            )

            grib_file = outdir / f"{y}{month}.grib"

            print(f"Downloading {grib_file}")

            try:

                c.retrieve(
                    "tigge-forecasts",
                    {                        
                        "origin": "bom",
                        "year": y,
                        "month": month,
                        "day": days,                        
                        "grid": "0.5/0.5",
                        "time": "00:00:00",
                        "level_type": "single_level",
                        "number": "0",
                        "variable": [
                            "10_m_u_component_of_wind",
                            "10_m_v_component_of_wind",
                            "surface_pressure",
                            "total_precipitation"
                        ],
                        "forecast_type": "control_forecast",
                        "leadtime_hour": [
                            "6",
                            "12",
                            "18",
                            "24"
                        ],
                        "data_format": "grib",
                        "area": [-26.5, -65.5, -27.0, -64.8]
                        
                    },
                    str(grib_file)
                )

            except Exception as e:

                print(f"ERROR downloading {grib_file}")
                print(e)

# ==========================================
# PROCESAMIENTO
# ==========================================


lat = -26.8083
lon = 360 - 65.2176  # conversión a 0–360

for p in parametros:

    model = p["model"]

    for y in p["years"]:

        print(f"\nProcessing {model} {y}")

        files = sorted(
            glob.glob(f"{model}/{y}/*.grib")
        )

        monthly_dfs = []

        for file in files:

            print(f"Opening {file}")

            try:

                # abrir GRIB
                ds = xr.open_dataset(
                    file,
                    engine="cfgrib"
                )

                # normalizar longitudes igual ERA5
                ds = ds.assign_coords(
                    longitude=(
                        ((ds.longitude + 180) % 360) - 180
                    )
                ).sortby("longitude")

                # seleccionar mismo punto ERA5
                point = ds.sel(
                    latitude=-26.8083,
                    longitude=-65.2176,
                    method="nearest"
                )

                # dataframe
                df = point.to_dataframe().reset_index()

                # guardar info extra
                df["model"] = model

                monthly_dfs.append(df)

                ds.close()

            except Exception as e:

                print(f"ERROR processing {file}")
                print(e)

        # unir meses
        if len(monthly_dfs) > 0:

            final_df = pd.concat(
                monthly_dfs,
                ignore_index=True
            )

            outfile = f"{model}_{y}.parquet"

            final_df.to_parquet(outfile)

            print(f"Saved {outfile}")

            print(final_df.head())