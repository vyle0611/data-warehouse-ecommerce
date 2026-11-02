import os
import duckdb

MOTHERDUCK_TOKEN = os.getenv("MOTHERDUCK_TOKEN")
# Kết nối tới Cloud Lakehouse MotherDuck với DuckDB 1.5.6
con = duckdb.connect(f"md:ecommerce_db?token={MOTHERDUCK_TOKEN}")

con.execute("CREATE SCHEMA IF NOT EXISTS bronze;")

# Danh sách 13 file CSV chính của bộ dữ liệu Thương mại điện tử
tables = [
    "products", "customers", "promotions", "geography", 
    "orders", "order_items", "payments", "shipments", 
    "returns", "reviews", "sales", "inventory", "web_traffic"
]

for table in tables:
    print(f"Ingesting table bronze.{table}...")
    # Nạp dữ liệu thô vào tầng Bronze (Thay URL bên dưới bằng đường dẫn repository/folder chứa dữ liệu của bạn)
    con.execute(f"""
        CREATE OR REPLACE TABLE bronze.{table} AS 
        SELECT * FROM read_csv_auto('https://raw.githubusercontent.com/YOUR_USERNAME/data-warehouse-ecommerce/main/dataset/{table}.csv');
    """)

print("Ingestion completed successfully!")
con.close()
