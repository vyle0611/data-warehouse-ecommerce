import os
import duckdb

MOTHERDUCK_TOKEN = os.getenv("MOTHERDUCK_TOKEN")

# 1. Kết nối tới MotherDuck
con = duckdb.connect(f"md:?token={MOTHERDUCK_TOKEN}")

# 2. Chuyển sang sử dụng database eccomerce_db đã tạo sẵn
con.execute("USE eccomerce_db;")
con.execute("CREATE SCHEMA IF NOT EXISTS bronze;")

# 3. Nạp dữ liệu từ thư mục local dataset/
tables = [
    "products", "customers", "promotions", "geography", 
    "orders", "order_items", "payments", "shipments", 
    "returns", "reviews", "sales", "inventory", "web_traffic"
]

for table in tables:
    file_path = f"dataset/{table}.csv"
    print(f"Ingesting {file_path} into bronze.{table}...")
    
    if os.path.exists(file_path):
        con.execute(f"""
            CREATE OR REPLACE TABLE bronze.{table} AS 
            SELECT * FROM read_csv_auto('{file_path}');
        """)
    else:
        print(f"⚠️ Cảnh báo: Không tìm thấy file {file_path}")

print("✅ Ingestion completed successfully!")
con.close()
