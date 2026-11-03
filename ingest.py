import os
import glob
import duckdb
import kagglehub

# 1. Cấu hình xác thực Kaggle API
os.environ["KAGGLE_API_TOKEN"] = os.getenv("KAGGLE_API_TOKEN", "")

# 2. Tải bộ dữ liệu cuộc thi từ Kaggle
print("Downloading competition files via kagglehub...")
download_path = kagglehub.competition_download("datathon-2026-round-1")
print("Path to competition files:", download_path)

# 3. Kết nối MotherDuck và khởi tạo database ecommerce_db
MOTHERDUCK_TOKEN = os.getenv("MOTHERDUCK_TOKEN")
con = duckdb.connect(f"md:?token={MOTHERDUCK_TOKEN}")

# Tự động tạo và chọn database ecommerce_db
con.execute("CREATE DATABASE IF NOT EXISTS ecommerce_db;")
con.execute("USE ecommerce_db;")
con.execute("CREATE SCHEMA IF NOT EXISTS bronze;")

# 4. Nạp tự động các file CSV vào tầng Bronze
csv_files = glob.glob(os.path.join(download_path, "*.csv"))

if not csv_files:
    print("⚠️ Không tìm thấy file CSV nào trong thư mục tải về!")
else:
    for file_path in csv_files:
        table_name = os.path.splitext(os.path.basename(file_path))[0]
        print(f"Ingesting {file_path} into bronze.{table_name}...")
        
        con.execute(f"""
            CREATE OR REPLACE TABLE bronze.{table_name} AS 
            SELECT * FROM read_csv_auto('{file_path}');
        """)

print("✅ Kagglehub Ingestion completed successfully!")
con.close()
