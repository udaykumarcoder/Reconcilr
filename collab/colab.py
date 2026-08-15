# from google.colab import files
# uploaded = files.upload()

# !unzip -o order-reconciliation-pipeline.zip
# %cd order-reconciliation-pipeline

# !pip install -r requirements.txt -q

# with open("data/output/report.md") as f:
#     print(f.read())

#     files.download("data/output/report.md")
# files.download("data/output/reconciled.parquet")


# from google.colab import files
# uploaded = files.upload()
# # select these 5 files when the picker opens:
# # olist_orders_dataset.csv
# # olist_order_items_dataset.csv
# # olist_order_payments_dataset.csv
# # olist_customers_dataset.csv
# # olist_products_dataset.csv


# import shutil, os

# files_needed = [
#     "olist_orders_dataset.csv",
#     "olist_order_items_dataset.csv",
#     "olist_order_payments_dataset.csv",
#     "olist_customers_dataset.csv",
#     "olist_products_dataset.csv",
# ]

# os.makedirs("data/raw", exist_ok=True)
# for f in files_needed:
#     shutil.move(f, f"data/raw/{f}")

# !python pipeline.py --input data/raw --output data/output

# with open("data/output/report.md") as f:
#     print(f.read())