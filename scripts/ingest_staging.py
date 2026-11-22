import pandas as pd
import sqlite3
import time
import os
from datetime import datetime

DATA_DIR = os.environ.get("DATA_DIR", "./Data")
STG_DB = os.path.join(DATA_DIR, "staging_ods.db")

FILES = {
    "01_master_data.csv": "stg_master_data",
    "04_warehouse_data.csv": "stg_warehouse_data",
    "05_pharmacy_sales_data.csv": "stg_pharmacy_sales",
    "06_hospital_demand_data.csv": "stg_hospital_demand"
}

def run_ingestion():
    conn = sqlite3.connect(STG_DB)
    batch_logs, storage_logs = [], []

    for fn, tbl in FILES.items():
        fp = os.path.join(DATA_DIR, fn)
        if not os.path.exists(fp):
            continue
        t0 = time.time()
        status, rows = "Success", 0
        try:
            df = pd.read_csv(fp, low_memory=False)
            rows = len(df)
            df.to_sql(tbl, conn, if_exists="replace", index=False, chunksize=10000)
        except Exception as e:
            status = f"Failed: {str(e)[:40]}"

        dur = round(time.time() - t0, 3)
        mb = round(os.path.getsize(fp) / (1024 * 1024), 2)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        batch_logs.append({"RunTime": ts, "SourceFile": fn, "TargetTable": tbl, "DurationSec": dur, "RowsProcessed": rows, "Status": status, "SuccessRatePct": 100.0 if status == "Success" else 0.0})
        storage_logs.append({"RunTime": ts, "Domain": fn.replace(".csv", ""), "TableName": tbl, "RowCount": rows, "StorageMB": mb, "DateCoverage": "2023-01-01 to 2025-12-31"})

    conn.close()
    for name, logs in [("metrics_batch_ingestion.csv", batch_logs), ("metrics_storage.csv", storage_logs)]:
        lp = os.path.join(DATA_DIR, name)
        pd.DataFrame(logs).to_csv(lp, mode="a", header=not os.path.exists(lp), index=False)
    print("Staging Ingestion Complete!")

if __name__ == "__main__":
    run_ingestion()
