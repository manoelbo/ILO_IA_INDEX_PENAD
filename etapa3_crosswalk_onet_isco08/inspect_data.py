import pandas as pd

def inspect_excel(path, skip=0):
    print(f"\n--- Inspecting {path} (skip={skip}) ---")
    try:
        xl = pd.ExcelFile(path)
        for sheet in xl.sheet_names:
            df = pd.read_excel(path, sheet_name=sheet, skiprows=skip, nrows=5)
            print(f"\nSheet: {sheet}")
            print(df.columns.tolist())
            print(df.head())
    except Exception as e:
        print(f"Error reading {path}: {e}")

inspect_excel("etapa3_crosswalk_onet_isco08/data_input/Crosswalk SOC 2010 a 2018.xlsx", skip=6)
inspect_excel("etapa3_crosswalk_onet_isco08/data_input/Crosswalk SOC 2010 ISCO-08.xls", skip=6)
