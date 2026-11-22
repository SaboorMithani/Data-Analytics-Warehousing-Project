import pandas as pd
import numpy as np
import os
from datetime import datetime

DATA_DIR = os.environ.get("DATA_DIR", "./Data")

def oversample_dataset():
    stats = []
    # 1. Pharmacy Sales (+5,000 rows)
    p1 = os.path.join(DATA_DIR, "05_pharmacy_sales_data.csv")
    if os.path.exists(p1):
        df = pd.read_csv(p1, low_memory=False)
        before = len(df)
        samp = df.sample(n=min(5000, before), replace=True).copy()
        samp["SalesTransactionID"] = [f"SALE-{i:09d}" for i in range(before + 1, before + len(samp) + 1)]
        dt = pd.to_datetime(samp["SalesDate"], errors="coerce").fillna(pd.Timestamp("2024-06-01"))
        samp["SalesDate"] = (dt + pd.to_timedelta(np.random.randint(1, 30, len(samp)), unit="D")).dt.strftime("%m/%d/%Y")
        out = pd.concat([df, samp], ignore_index=True)
        out.to_csv(p1, index=False)
        stats.append({"File": "05_pharmacy_sales_data.csv", "Before": before, "Added": len(samp), "After": len(out)})

    # 2. Hospital Demand (+500 rows)
    p2 = os.path.join(DATA_DIR, "06_hospital_demand_data.csv")
    if os.path.exists(p2):
        df = pd.read_csv(p2, low_memory=False)
        before = len(df)
        samp = df.sample(n=min(500, before), replace=True).copy()
        samp["HospitalDemandRecordID"] = [f"HDEM-{i:08d}" for i in range(before + 1, before + len(samp) + 1)]
        out = pd.concat([df, samp], ignore_index=True)
        out.to_csv(p2, index=False)
        stats.append({"File": "06_hospital_demand_data.csv", "Before": before, "Added": len(samp), "After": len(out)})

    # 3. Warehouse Inventory (+1,000 rows)
    p3 = os.path.join(DATA_DIR, "04_warehouse_data.csv")
    if os.path.exists(p3):
        df = pd.read_csv(p3, low_memory=False)
        before = len(df)
        samp = df.sample(n=min(1000, before), replace=True).copy()
        samp["InventorySnapshotID"] = [f"INV-{i:09d}" for i in range(before + 1, before + len(samp) + 1)]
        out = pd.concat([df, samp], ignore_index=True)
        out.to_csv(p3, index=False)
        stats.append({"File": "04_warehouse_data.csv", "Before": before, "Added": len(samp), "After": len(out)})

    sdf = pd.DataFrame(stats)
    sdf["RunTimestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_p = os.path.join(DATA_DIR, "oversample_stats_log.csv")
    sdf.to_csv(log_p, mode="a", header=not os.path.exists(log_p), index=False)
    print("Oversample Done:\n", sdf.to_string(index=False))

if __name__ == "__main__":
    oversample_dataset()
