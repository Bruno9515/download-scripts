import pandas as pd
from pathlib import Path

# Carpeta donde están los archivos parquet
carpeta = Path(".")

# Buscar todos los archivos .parquet
archivos_parquet = carpeta.glob("*.parquet")

for archivo in archivos_parquet:
    try:
        # Leer parquet
        df = pd.read_parquet(archivo)

        # Crear nombre del csv
        salida_csv = archivo.with_suffix(".csv")

        # Guardar csv
        df.to_csv(salida_csv, index=False)

        print(f"Convertido: {archivo} -> {salida_csv}")

    except Exception as e:
        print(f"Error con {archivo}: {e}")