import cdsapi
import xarray as xr
import pandas as pd
import glob
import zipfile
import os
import calendar

c = cdsapi.Client()

#months = ["01","02","03","10","11","12"]
months = [["01","02","03"],["10","11","12"]]

variables = [
    "total_precipitation",
    "2m_temperature",
    "2m_dewpoint_temperature",
    "surface_pressure",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind"
]

years = list(range(2024,2026))

times = [f"{h:02d}:00" for h in range(24)]

for y in years:

    os.makedirs(f"{y}", exist_ok=True)

    monthly_dfs = []

    for m in months:

        print(f"{y}-{m[0]}")

        days_in_month = calendar.monthrange(y, int(m[0]))[1]

        days = [f"{d:02d}" for d in range(1, days_in_month + 1)]

        zip_name = f"{y}/era5_{y}_{m[0]}.zip"

        extract_path = f"{y}/era5_{y}_{m[0]}"

        # ======================
        # DESCARGA
        # ======================

        if not os.path.exists(zip_name):

            c.retrieve(
                "reanalysis-era5-single-levels",
                {
                    "product_type": "reanalysis",
                    "variable": variables,
                    "year": str(y),
                    "month": m,
                    "day": days,
                    "time": times,
                    "area": [-27, -66, -26, -65],
                    "format": "netcdf"
                },
                zip_name
            )

        # ======================
        # EXTRAER
        # ======================

        os.makedirs(extract_path, exist_ok=True)

        with zipfile.ZipFile(zip_name, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

        # ======================
        # ABRIR NETCDF
        # ======================

        instant_file = os.path.join(
            extract_path,
            "data_stream-oper_stepType-instant.nc"
        )

        accum_file = os.path.join(
            extract_path,
            "data_stream-oper_stepType-accum.nc"
        )

        ds_inst = xr.open_dataset(instant_file)
        ds_acc = xr.open_dataset(accum_file)

        # merge correcto
        ds = xr.merge([ds_inst, ds_acc])

        # normalizar longitudes
        ds = ds.assign_coords(
            longitude=(((ds.longitude + 180) % 360) - 180)
        ).sortby("longitude")

        # punto tucuman
        point = ds.sel(
            latitude=-26.8083,
            longitude=-65.2176,
            method="nearest"
        )

        df = point.to_dataframe().reset_index()

        monthly_dfs.append(df)

        ds.close()

    # unir meses
    final_df = pd.concat(monthly_dfs)

    final_df.to_parquet(f"era5_{y}.parquet")

    print(final_df.head())