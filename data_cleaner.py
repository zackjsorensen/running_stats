import pandas as pd
import os
from pathlib import Path
import ast

def extract(dir_name: str):
    base_path = Path(dir_name)
    files = list(base_path.rglob("*.csv"))

    all_rows = []

    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                try:
                    row = ast.literal_eval(line.strip())
                    all_rows.append(row)
                except Exception as e:
                    print(f"Error parsing line in {file}: {e}")

    print(f"Loaded {len(files)} CSV files with {len(all_rows)} total rows.")
    # print(all_rows)



extract("2021_csvs")