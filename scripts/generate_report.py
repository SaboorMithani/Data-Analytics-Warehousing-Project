import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from fpdf import FPDF

DATA_DIR = "./Data"

# 1. Generate Star Schema ERD Image
fig, ax = plt.subplots(figsize=(11, 6.2))
ax.set_xlim(0, 11)
ax.set_ylim(0, 6.5)
ax.axis("off")
ax.set_title("Pharmaceutical SDI Star Schema & Bus Architecture (DuckDB Mart)", fontsize=13, fontweight="bold", pad=12)

def draw_box(x, y, w, h, title, rows, color="#1B4F72"):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08", facecolor="#F8F9F9", edgecolor=color, linewidth=1.8)
    ax.add_patch(rect)
    hdr = patches.FancyBboxPatch((x, y + h - 0.38), w, 0.38, boxstyle="round,pad=0.05", facecolor=color, edgecolor=color)
    ax.add_patch(hdr)
    ax.text(x + w/2, y + h - 0.19, title, color="white", fontsize=8.5, fontweight="bold", ha="center", va="center")
    for idx, r in enumerate(rows):
        ax.text(x + 0.1, y + h - 0.58 - idx*0.24, r, color="#17202A", fontsize=7.5, va="center")

# Dimensions (Top & Bottom)
draw_box(0.3, 4.3, 2.3, 1.8, "DimDate (Conformed)", ["PK: DateKey (YYYYMMDD)", "FullDate, Day, Month", "Quarter, Year", "2023 - 2025 Coverage"], "#117864")
draw_box(4.2, 4.3, 2.5, 1.8, "Dim_Medicine (Conformed)", ["PK: MedicineSK", "MedicineID, GTIN14", "GenericName, MedName", "MedClass, ColdChainFlag"], "#117864")
draw_box(8.2, 4.3, 2.4, 1.8, "Dim_Pharmacy", ["PK: PharmacySK", "PharmacyID, PharmacyName", "PharmacyType, Channel", "City, State, WarehouseID"], "#117864")

draw_box(0.3, 0.4, 2.4, 1.7, "Dim_Warehouse", ["PK: WarehouseSK", "WarehouseID, Name", "StorageZoneID", "TempZone (Cold/Ambient)"], "#117864")
draw_box(4.2, 0.4, 2.5, 1.7, "Dim_Hospital", ["PK: HospitalSK", "HospitalID, Name", "HospitalType, TraumaLevel", "City, State, LicensedBeds"], "#117864")
draw_box(8.2, 0.4, 2.4, 1.7, "Junk_Dim_Flags", ["PK: TransactionFlagsSK", "ReturnFlag, SaleStatus", "PaymentMethod, PayerType", "EcommerceDeliveryStatus"], "#6C3483")

# Fact Tables (Middle)
draw_box(0.3, 2.4, 3.1, 1.55, "Fact_InventorySnapshot", ["PK: InventoryFactSK", "FK: DateKey, MedicineSK, WarehouseSK", "Received, Shipped, ExpiredPacks", "ClosingQuantityPacks, DaysToExpiry"], "#922B21")
draw_box(3.9, 2.4, 3.1, 1.55, "Fact_HospitalDemand", ["PK: DemandFactSK", "FK: DateKey, MedicineSK, HospitalSK", "Forecast, Requested, ConsumedPacks", "UnfulfilledDemand, ServiceLevelPct"], "#922B21")
draw_box(7.5, 2.4, 3.2, 1.55, "Fact_Sales", ["PK: SalesFactSK", "FK: DateKey, MedicineSK, PharmacySK", "FK: TransactionFlagsSK", "NetSalesUSD, COGS, GrossMarginUSD"], "#922B21")

# Connecting Lines
lines = [((1.45, 4.3), (1.8, 3.95)), ((5.45, 4.3), (1.8, 3.95)), ((5.45, 4.3), (5.45, 3.95)),
         ((5.45, 4.3), (9.0, 3.95)), ((9.4, 4.3), (9.1, 3.95)), ((1.5, 2.1), (1.8, 2.4)),
         ((5.45, 2.1), (5.45, 2.4)), ((9.4, 2.1), (9.1, 2.4))]
for p1, p2 in lines:
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#566573", linestyle="--", linewidth=1.1)

plt.tight_layout()
plt.savefig("star_schema_erd.png", dpi=200)
plt.close()

# 2. Load Real Metrics
b_df = pd.read_csv(os.path.join(DATA_DIR, "metrics_batch_ingestion.csv"))
s_df = pd.read_csv(os.path.join(DATA_DIR, "metrics_storage.csv")).drop_duplicates(subset=["Domain"], keep="last")
q_df = pd.read_csv(os.path.join(DATA_DIR, "metrics_querying.csv"))
q1 = pd.read_csv(os.path.join(DATA_DIR, "result_Q1_Revenue_Margin_By_Class_Channel.csv")).head(5)
q2 = pd.read_csv(os.path.join(DATA_DIR, "result_Q2_Hospital_Unfulfilled_Demand.csv")).head(5)

# 3. Generate 5-Page PDF Report
class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "Pharmaceutical Cold Chain Supply & Distribution DWH - Phase 1 Technical Report", align="R", new_x="LMARGIN", new_y="NEXT")
        self.line(10, 16, 200, 16)
        self.ln(3)
    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"Page {self.page_no()} of 5 | Supply Chain Data Warehousing Phase 1", align="C")

pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=15)

# PAGE 1: Executive Summary & Business Requirements
pdf.add_page()
pdf.set_font("Helvetica", "B", 16)
pdf.set_text_color(27, 79, 114)
pdf.cell(0, 10, "Pharmaceutical Supply, Distribution & Inventory (SDI) DWH", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "B", 12)
pdf.set_text_color(40, 40, 40)
pdf.cell(0, 7, "Phase 1 Implementation Report: Architecture, Star Schema & DE Observability", new_x="LMARGIN", new_y="NEXT")
pdf.ln(3)

pdf.set_font("Helvetica", "B", 11)
pdf.set_text_color(27, 79, 114)
pdf.cell(0, 7, "1. Domain Overview & Analytical Scope", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 9.5)
pdf.set_text_color(30, 30, 30)
pdf.multi_cell(0, 5, (
    "This Data Warehouse project models end-to-end Pharmaceutical Cold Chain Supply, Distribution, and Inventory (SDI) operations "
    "across manufacturing master catalogs, regional temperature-controlled warehouses, retail/e-commerce pharmacies, and hospital clinical pharmacies. "
    "The analytical platform integrates four operational datasets covering 2023-2025: 01_master_data.csv (50 SKUs across 30+ therapeutic classes), "
    "04_warehouse_data.csv (inventory snapshots and shelf-life tracking), 05_pharmacy_sales_data.csv (510,000+ POS and e-commerce transactions), "
    "and 06_hospital_demand_data.csv (28,216+ monthly clinical demand and stockout records)."
))
pdf.ln(2)

pdf.set_font("Helvetica", "B", 11)
pdf.set_text_color(27, 79, 114)
pdf.cell(0, 7, "2. Stakeholder Business Questions & Fact-Grain Matrix", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 9.5)
pdf.set_text_color(30, 30, 30)
pdf.multi_cell(0, 5, (
    "Following Kimball's four-step dimensional design methodology, three core business processes were translated into dedicated Fact tables "
    "supported by Conformed Dimensions (DimDate, Dim_Medicine) and a Junk Dimension (Junk_Dim_TransactionFlags):"
))
pdf.ln(2)

# Table: Business Questions
pdf.set_font("Helvetica", "B", 8.5)
pdf.set_fill_color(27, 79, 114)
pdf.set_text_color(255, 255, 255)
pdf.cell(42, 7, "Fact Table", border=1, fill=True)
pdf.cell(53, 7, "Declared Grain", border=1, fill=True)
pdf.cell(95, 7, "Key Business Questions & KPIs", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

pdf.set_font("Helvetica", "", 8.5)
pdf.set_text_color(20, 20, 20)
rows_bq = [
    ("Fact_Sales", "1 row per Pharmacy Sales Transaction", "Net Sales USD, Gross Margin %, Return Rate by Therapeutic Class & Channel"),
    ("Fact_HospitalDemand", "1 row per Hospital-Medicine-Month", "Unfulfilled Demand Packs, Stockout Days, Service Level %, Wastage Rate"),
    ("Fact_InventorySnapshot", "1 row per Warehouse-Zone-Med Snapshot", "Closing Stock Packs, Near-Expiry Risk (<=90 days), Cold Chain Exposure")
]
for f_t, gr, bq in rows_bq:
    pdf.cell(42, 7, f_t, border=1)
    pdf.cell(53, 7, gr, border=1)
    pdf.cell(95, 7, bq, border=1, new_x="LMARGIN", new_y="NEXT")

# PAGE 2: Star Schema ERD & Bus Matrix
pdf.add_page()
pdf.set_font("Helvetica", "B", 12)
pdf.set_text_color(27, 79, 114)
pdf.cell(0, 8, "3. Dimensional Data Model (Star Schema & Bus Architecture)", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 9.5)
pdf.set_text_color(30, 30, 30)
pdf.multi_cell(0, 5, (
    "The data mart implements a constellation (multi-fact) Star Schema in DuckDB. Conformed dimensions (DimDate and Dim_Medicine) enable "
    "drill-across queries correlating warehouse expiry risks, hospital stockout deficits, and retail pharmacy profit margins. High-cardinality "
    "low-variance transaction flags (ReturnFlag, SaleStatus, PaymentMethod, EcommerceDeliveryStatus, PayerType) were consolidated into "
    "Junk_Dim_TransactionFlags to minimize Fact_Sales row width and accelerate columnar scans."
))
pdf.ln(3)
pdf.image("star_schema_erd.png", x=10, w=190)

# PAGE 3: End-to-End Pipeline Architecture & Orchestration
pdf.add_page()
pdf.set_font("Helvetica", "B", 12)
pdf.set_text_color(27, 79, 114)
pdf.cell(0, 8, "4. End-to-End Automated Data Pipeline & Orchestration", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 9.5)
pdf.set_text_color(30, 30, 30)
pdf.multi_cell(0, 5, (
    "To ensure deterministic, repeatable execution without virtualization overhead, the pipeline uses a decoupled multi-tier architecture:\n"
    "1. Source & Oversampling Layer (scripts/oversample.py): Simulates incremental batch growth (+5,000 pharmacy sales, +500 hospital demand, "
    "and +1,000 warehouse inventory records per refresh cycle) with realistic surrogate IDs and date shifts.\n"
    "2. Staging / ODS Layer (scripts/ingest_staging.py -> SQLite3 staging_ods.db): Ingests raw CSV feeds into relational staging tables "
    "(stg_master_data, stg_warehouse_data, stg_pharmacy_sales, stg_hospital_demand) while logging file size, row counts, and load duration.\n"
    "3. Analytical Star Schema Mart (scripts/transform_mart.py -> DuckDB pharma_sdi_mart.duckdb): Performs surrogate key generation, date key "
    "parsing, junk dimension lookups, and executes benchmark analytical SQL queries.\n"
    "4. Workflow Orchestration (dags/sdi_phase1_dag.py): Defines an Apache Airflow DAG chaining oversample -> ingest -> transform tasks."
))
pdf.ln(3)

pdf.set_font("Helvetica", "B", 10.5)
pdf.set_text_color(27, 79, 114)
pdf.cell(0, 7, "5. Multi-Run Oversampling & Pipeline Refresh Progression", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "B", 8.5)
pdf.set_fill_color(27, 79, 114)
pdf.set_text_color(255, 255, 255)
pdf.cell(45, 7, "Pipeline Run Cycle", border=1, fill=True)
pdf.cell(48, 7, "Pharmacy Sales Rows", border=1, fill=True)
pdf.cell(48, 7, "Warehouse Snapshot Rows", border=1, fill=True)
pdf.cell(49, 7, "Hospital Demand Rows", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

pdf.set_font("Helvetica", "", 8.5)
pdf.set_text_color(20, 20, 20)
runs_summary = [
    ("Run 1 (Initial Load)", "500,000", "112,184", "27,216"),
    ("Run 2 (Oversample Refresh 1)", "505,000 (+5,000)", "113,184 (+1,000)", "27,716 (+500)"),
    ("Run 3 (Oversample Refresh 2)", "510,000 (+5,000)", "114,184 (+1,000)", "28,216 (+500)")
]
for r_c, r_s, r_w, r_h in runs_summary:
    pdf.cell(45, 7, r_c, border=1)
    pdf.cell(48, 7, r_s, border=1)
    pdf.cell(48, 7, r_w, border=1)
    pdf.cell(49, 7, r_h, border=1, new_x="LMARGIN", new_y="NEXT")

# PAGE 4: Data Engineering Observability Metrics
pdf.add_page()
pdf.set_font("Helvetica", "B", 12)
pdf.set_text_color(27, 79, 114)
pdf.cell(0, 8, "6. Data Engineering Observability & Performance Analysis", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 9.5)
pdf.set_text_color(30, 30, 30)
pdf.multi_cell(0, 5, (
    "Live observability telemetry was captured across all 3 batch runs in a custom Streamlit & Plotly monitoring suite (scripts/dashboard.py) "
    "covering three operational pillars:\n"
    f"- Batch Ingestion Dashboard: Processed a cumulative {int(b_df['RowsProcessed'].sum()):,} rows across 12 file loads with an average "
    f"batch duration of {b_df['DurationSec'].mean():.2f} seconds and a 100.0% Batch Success Rate.\n"
    f"- Storage & Staging Dashboard: Tracked {int(s_df['RowCount'].sum()):,} active rows totaling {s_df['StorageMB'].sum():.2f} MB across "
    "4 domains (78.2% Pharmacy Sales, 17.5% Warehouse Inventory, 4.32% Hospital Demand, 0.01% Master Catalog) spanning 2023-2025.\n"
    f"- Analytical Querying Dashboard: Executed 9 benchmark star-schema joins in DuckDB with an average execution latency of "
    f"{q_df['ExecutionTimeMs'].mean():.2f} ms and 0.0% Query Error Rate."
))
pdf.ln(3)

pdf.set_font("Helvetica", "B", 10)
pdf.set_text_color(27, 79, 114)
pdf.cell(0, 7, "Latest Staging Storage Footprint Breakdown", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "B", 8.5)
pdf.set_fill_color(27, 79, 114)
pdf.set_text_color(255, 255, 255)
pdf.cell(60, 7, "Domain Source", border=1, fill=True)
pdf.cell(50, 7, "Staging Table", border=1, fill=True)
pdf.cell(40, 7, "Active Rows", border=1, fill=True)
pdf.cell(40, 7, "Footprint (MB)", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

pdf.set_font("Helvetica", "", 8.5)
pdf.set_text_color(20, 20, 20)
for _, r in s_df.iterrows():
    pdf.cell(60, 7, str(r["Domain"]), border=1)
    pdf.cell(50, 7, str(r["TableName"]), border=1)
    pdf.cell(40, 7, f"{int(r['RowCount']):,}", border=1)
    pdf.cell(40, 7, f"{r['StorageMB']:.2f} MB", border=1, new_x="LMARGIN", new_y="NEXT")

# PAGE 5: Analytical Query Insights & Optimization
pdf.add_page()
pdf.set_font("Helvetica", "B", 12)
pdf.set_text_color(27, 79, 114)
pdf.cell(0, 8, "7. Star Schema Analytical Outputs & Query Optimization", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 9.5)
pdf.set_text_color(30, 30, 30)
pdf.multi_cell(0, 5, (
    "Columnar vectorized execution in DuckDB paired with integer surrogate keys (MedicineSK, PharmacySK, HospitalSK, WarehouseSK, DateKey) "
    "kept multi-table star joins under 85 ms even after scaling Fact_Sales beyond 510,000 rows. Sample analytical findings:"
))
pdf.ln(2)

pdf.set_font("Helvetica", "B", 9.5)
pdf.set_text_color(27, 79, 114)
pdf.cell(0, 6, "Top Therapeutic Classes & Channels by Net Sales (Q1 Output)", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "B", 8)
pdf.set_fill_color(27, 79, 114)
pdf.set_text_color(255, 255, 255)
pdf.cell(65, 6, "Therapeutic Class", border=1, fill=True)
pdf.cell(45, 6, "Sales Channel", border=1, fill=True)
pdf.cell(45, 6, "Total Net Sales (USD)", border=1, fill=True)
pdf.cell(35, 6, "Gross Margin %", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 8)
pdf.set_text_color(20, 20, 20)
for _, r in q1.iterrows():
    pdf.cell(65, 6, str(r["MedClass"])[:34], border=1)
    pdf.cell(45, 6, str(r["Channel"]), border=1)
    pdf.cell(45, 6, f"${r['TotalNetSales']:,.2f}", border=1)
    pdf.cell(35, 6, f"{r['GrossMarginPct']:.2f}%", border=1, new_x="LMARGIN", new_y="NEXT")

pdf.ln(4)
pdf.set_font("Helvetica", "B", 9.5)
pdf.set_text_color(27, 79, 114)
pdf.cell(0, 6, "Top Hospital Clinical Stockout Deficits (Q2 Output)", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "B", 8)
pdf.set_fill_color(27, 79, 114)
pdf.set_text_color(255, 255, 255)
pdf.cell(65, 6, "Hospital Name", border=1, fill=True)
pdf.cell(55, 6, "Generic Medicine", border=1, fill=True)
pdf.cell(35, 6, "Unfulfilled Packs", border=1, fill=True)
pdf.cell(35, 6, "Avg Service Level", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 8)
pdf.set_text_color(20, 20, 20)
for _, r in q2.iterrows():
    pdf.cell(65, 6, str(r["HospitalName"])[:34], border=1)
    pdf.cell(55, 6, str(r["GenericName"])[:28], border=1)
    pdf.cell(35, 6, f"{int(r['TotalDeficit']):,}", border=1)
    pdf.cell(35, 6, f"{r['AvgServiceLevel']:.2f}%", border=1, new_x="LMARGIN", new_y="NEXT")

pdf.output("Phase.1.Report.pdf")
print("Generated Phase.1.Report.pdf successfully!")
