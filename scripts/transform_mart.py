import duckdb
import sqlite3
import pandas as pd
import time
import os
from datetime import datetime

DATA_DIR = os.environ.get("DATA_DIR", "./Data")
STG_DB = os.path.join(DATA_DIR, "staging_ods.db")
MART_DB = os.path.join(DATA_DIR, "pharma_sdi_mart.duckdb")

def build_mart():
    sconn = sqlite3.connect(STG_DB)
    df_med = pd.read_sql("SELECT * FROM stg_master_data", sconn)
    df_sales = pd.read_sql("SELECT * FROM stg_pharmacy_sales", sconn)
    df_hosp = pd.read_sql("SELECT * FROM stg_hospital_demand", sconn)
    df_wh = pd.read_sql("SELECT * FROM stg_warehouse_data", sconn)
    sconn.close()

    con = duckdb.connect(MART_DB)

    con.execute("""
        CREATE OR REPLACE TABLE Dim_Medicine AS
        SELECT ROW_NUMBER() OVER (ORDER BY MedicineID) AS MedicineSK,
               MedicineID, GTIN14, GenericName, FictionalBrandName AS MedName,
               DiseaseCategory, ICD10Category, TherapeuticClass AS MedClass,
               DosageForm, Strength, PackSize, ColdChainFlag,
               UnitManufacturingCostUSD, WholesalePriceUSD, RecommendedRetailPriceUSD
        FROM df_med
    """)

    con.execute("""
        CREATE OR REPLACE TABLE Dim_Pharmacy AS
        SELECT ROW_NUMBER() OVER (ORDER BY PharmacyID, SalesChannel) AS PharmacySK,
               PharmacyID, PharmacyName, PharmacyType, SalesChannel AS Channel,
               PharmacyCity, PharmacyState, SourceWarehouseID
        FROM (SELECT DISTINCT PharmacyID, PharmacyName, PharmacyType, SalesChannel,
              PharmacyCity, PharmacyState, SourceWarehouseID FROM df_sales)
    """)

    con.execute("""
        CREATE OR REPLACE TABLE Dim_Hospital AS
        SELECT ROW_NUMBER() OVER (ORDER BY HospitalID) AS HospitalSK,
               HospitalID, HospitalName, HospitalType, HospitalPharmacyID,
               City, State, TraumaLevel, LicensedBeds
        FROM (SELECT DISTINCT HospitalID, HospitalName, HospitalType, HospitalPharmacyID,
              City, State, TraumaLevel, LicensedBeds FROM df_hosp)
    """)

    con.execute("""
        CREATE OR REPLACE TABLE Dim_Warehouse AS
        SELECT ROW_NUMBER() OVER (ORDER BY WarehouseID, StorageZoneID) AS WarehouseSK,
               WarehouseID, WarehouseName, StorageZoneID, StorageCondition AS TempZone
        FROM (SELECT DISTINCT WarehouseID, WarehouseName, StorageZoneID, StorageCondition FROM df_wh)
    """)

    con.execute("""
        CREATE OR REPLACE TABLE Junk_Dim_TransactionFlags AS
        SELECT ROW_NUMBER() OVER () AS TransactionFlagsSK,
               ReturnFlag, SaleStatus, PaymentMethod, EcommerceDeliveryStatus, PayerType
        FROM (SELECT DISTINCT ReturnFlag, SaleStatus, PaymentMethod, EcommerceDeliveryStatus, PayerType FROM df_sales)
    """)

    con.execute("""
        CREATE OR REPLACE TABLE DimDate AS
        SELECT CAST(strftime(d, '%Y%m%d') AS INTEGER) AS DateKey,
               d AS FullDate, EXTRACT(DAY FROM d) AS Day, EXTRACT(MONTH FROM d) AS Month,
               EXTRACT(QUARTER FROM d) AS Quarter, EXTRACT(YEAR FROM d) AS Year
        FROM (SELECT DISTINCT TRY_CAST(strptime(SalesDate, '%m/%d/%Y') AS DATE) AS d FROM df_sales WHERE SalesDate IS NOT NULL)
        WHERE d IS NOT NULL
    """)

    con.execute("""
        CREATE OR REPLACE TABLE Fact_Sales AS
        SELECT ROW_NUMBER() OVER () AS SalesFactSK,
               CAST(strftime(TRY_CAST(strptime(s.SalesDate, '%m/%d/%Y') AS DATE), '%Y%m%d') AS INTEGER) AS DateKey,
               m.MedicineSK, p.PharmacySK, j.TransactionFlagsSK,
               s.SalesTransactionID, s.QuantitySoldPacks, s.ReturnedQuantityPacks,
               s.GrossSalesAmountUSD, s.DiscountAmountUSD, s.NetSalesAmountUSD,
               s.SalesTaxUSD, s.CostOfGoodsSoldUSD, s.GrossMarginUSD
        FROM df_sales s
        LEFT JOIN Dim_Medicine m ON s.MedicineID = m.MedicineID
        LEFT JOIN Dim_Pharmacy p ON s.PharmacyID = p.PharmacyID AND s.SalesChannel = p.Channel
        LEFT JOIN Junk_Dim_TransactionFlags j
          ON s.ReturnFlag = j.ReturnFlag AND s.SaleStatus = j.SaleStatus
          AND s.PaymentMethod = j.PaymentMethod AND s.EcommerceDeliveryStatus = j.EcommerceDeliveryStatus
          AND s.PayerType = j.PayerType
    """)

    con.execute("""
        CREATE OR REPLACE TABLE Fact_HospitalDemand AS
        SELECT ROW_NUMBER() OVER () AS DemandFactSK,
               CAST(strftime(TRY_CAST(strptime(h.DemandMonth, '%m/%d/%Y') AS DATE), '%Y%m%d') AS INTEGER) AS DateKey,
               m.MedicineSK, hp.HospitalSK, h.HospitalDemandRecordID,
               h.ForecastDemandPacks, h.RequestedQuantityPacks, h.ReceivedQuantityPacks,
               h.ConsumedQuantityPacks, h.WastageQuantityPacks, h.ClosingStockPacks,
               h.UnfulfilledDemandPacks, h.StockoutDays, h.ServiceLevelPct
        FROM df_hosp h
        LEFT JOIN Dim_Medicine m ON h.MedicineID = m.MedicineID
        LEFT JOIN Dim_Hospital hp ON h.HospitalID = hp.HospitalID
    """)

    con.execute("""
        CREATE OR REPLACE TABLE Fact_InventorySnapshot AS
        SELECT ROW_NUMBER() OVER () AS InventoryFactSK,
               CAST(strftime(TRY_CAST(w.SnapshotDate AS DATE), '%Y%m%d') AS INTEGER) AS DateKey,
               m.MedicineSK, wh.WarehouseSK, w.InventorySnapshotID,
               w.ReceivedQuantityPacks, w.ShippedQuantityPacks, w.ExpiredQuantityPacks,
               w.AvailableQuantityPacks, w.ClosingQuantityPacks, w.DaysToExpiry
        FROM df_wh w
        LEFT JOIN Dim_Medicine m ON w.MedicineID = m.MedicineID
        LEFT JOIN Dim_Warehouse wh ON w.WarehouseID = wh.WarehouseID AND w.StorageZoneID = wh.StorageZoneID
    """)

    queries = {
        "Q1_Revenue_Margin_By_Class_Channel": """
            SELECT m.MedClass, p.Channel,
                   ROUND(SUM(f.NetSalesAmountUSD), 2) AS TotalNetSales,
                   ROUND(SUM(f.GrossMarginUSD) / NULLIF(SUM(f.NetSalesAmountUSD),0) * 100, 2) AS GrossMarginPct
            FROM Fact_Sales f
            JOIN Dim_Medicine m ON f.MedicineSK = m.MedicineSK
            JOIN Dim_Pharmacy p ON f.PharmacySK = p.PharmacySK
            GROUP BY m.MedClass, p.Channel ORDER BY TotalNetSales DESC
        """,
        "Q2_Hospital_Unfulfilled_Demand": """
            SELECT h.HospitalName, m.GenericName,
                   SUM(f.UnfulfilledDemandPacks) AS TotalDeficit,
                   ROUND(AVG(f.ServiceLevelPct), 2) AS AvgServiceLevel
            FROM Fact_HospitalDemand f
            JOIN Dim_Hospital h ON f.HospitalSK = h.HospitalSK
            JOIN Dim_Medicine m ON f.MedicineSK = m.MedicineSK
            GROUP BY h.HospitalName, m.GenericName ORDER BY TotalDeficit DESC LIMIT 10
        """,
        "Q3_Warehouse_Near_Expiry_Stock": """
            SELECT w.WarehouseName, w.TempZone,
                   SUM(f.ClosingQuantityPacks) AS NearExpiryPacks
            FROM Fact_InventorySnapshot f
            JOIN Dim_Warehouse w ON f.WarehouseSK = w.WarehouseSK
            WHERE f.DaysToExpiry <= 90
            GROUP BY w.WarehouseName, w.TempZone ORDER BY NearExpiryPacks DESC
        """
    }

    qlogs = []
    for qn, sql in queries.items():
        t0 = time.time()
        err = 0
        try:
            res = con.execute(sql).fetchdf()
            res.to_csv(os.path.join(DATA_DIR, f"result_{qn}.csv"), index=False)
        except Exception:
            err = 1
        ms = round((time.time() - t0) * 1000, 2)
        qlogs.append({"RunTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "QueryName": qn, "ExecutionTimeMs": ms, "ErrorCount": err, "ErrorRatePct": err * 100.0})

    qp = os.path.join(DATA_DIR, "metrics_querying.csv")
    pd.DataFrame(qlogs).to_csv(qp, mode="a", header=not os.path.exists(qp), index=False)
    con.close()
    print("DuckDB Star Schema & Queries Complete!")

if __name__ == "__main__":
    build_mart()
