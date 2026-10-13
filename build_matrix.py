from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

ROOT = Path(__file__).resolve().parent

RAW_FILE = ROOT / "data" / "raw" / "online_retail_II.xlsx"
PROCESSED_DIR = ROOT / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

CLEANED_FILE = PROCESSED_DIR / "cleaned_retail.csv"
TRAIN_FILE = PROCESSED_DIR / "train.csv"
TEST_FILE = PROCESSED_DIR / "test_new.csv"

MATRIX_FILE = PROCESSED_DIR / "customer_product_matrix.npz"
CUSTOMER_MAP_FILE = PROCESSED_DIR / "customer_map.csv"
PRODUCT_MAP_FILE = PROCESSED_DIR / "product_map.csv"


# --------------------------------------------------
# Cleaning
# --------------------------------------------------

NON_PRODUCT_CODES = [
    "POST",
    "M",
    "D",
    "BANK CHARGES",
    "C2",
    "DOT",
    "ADJUST",
    "ADJUST2",
    "TEST001",
    "TEST002",
    "23444",
    "23574",
]


def load_raw_data():
    print("Loading raw Excel sheets...")

    sheets = pd.read_excel(
        RAW_FILE,
        sheet_name=None,
    )

    df = pd.concat(sheets.values(), ignore_index=True)

    print(f"Raw rows: {len(df):,}")
    return df


def clean_data(df):
    print("\nCleaning data...")

    # Cancelled invoices
    before = len(df)
    df = df[~df["Invoice"].astype(str).str.startswith("C")].copy()
    print(f"Cancelled invoices removed: {before - len(df):,}")

    # Non-positive quantity
    before = len(df)
    df = df[df["Quantity"] > 0].copy()
    print(f"Non-positive quantities removed: {before - len(df):,}")

    # Non-positive price
    before = len(df)
    df = df[df["Price"] > 0].copy()
    print(f"Non-positive prices removed: {before - len(df):,}")

    # Missing Customer ID
    before = len(df)
    df = df[df["Customer ID"].notna()].copy()
    print(f"Missing Customer IDs removed: {before - len(df):,}")

    # Non-product codes
    before = len(df)
    df = df[
        ~df["StockCode"].astype(str).isin(NON_PRODUCT_CODES)
    ].copy()
    print(f"Non-product rows removed: {before - len(df):,}")

    print(f"Cleaned rows: {len(df):,}")

    return df


# --------------------------------------------------
# Train / test split
# --------------------------------------------------

def split_data(df):
    print("\nCreating time-based train/test split...")

    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    max_date = df["InvoiceDate"].max()
    cutoff = max_date - pd.DateOffset(months=2)

    train = df[df["InvoiceDate"] < cutoff].copy()
    test_period = df[df["InvoiceDate"] >= cutoff].copy()

    train_pairs = set(
        zip(
            train["Customer ID"],
            train["StockCode"].astype(str),
        )
    )

    test_period["StockCode"] = test_period["StockCode"].astype(str)

    mask_new_product = [
        (customer_id, stock_code) not in train_pairs
        for customer_id, stock_code in zip(
            test_period["Customer ID"],
            test_period["StockCode"],
        )
    ]

    test_new = test_period.loc[mask_new_product].copy()

    print(f"Cutoff: {cutoff}")
    print(f"Train rows: {len(train):,}")
    print(f"Test-period rows: {len(test_period):,}")
    print(f"Held-out new-product rows: {len(test_new):,}")

    return train, test_new


# --------------------------------------------------
# Customer-product matrix
# --------------------------------------------------

def build_sparse_matrix(train):
    print("\nBuilding sparse customer-product matrix...")

    train = train.copy()
    train["StockCode"] = train["StockCode"].astype(str)

    customers = sorted(train["Customer ID"].unique())
    products = sorted(train["StockCode"].unique())

    customer_to_idx = {
        customer_id: idx
        for idx, customer_id in enumerate(customers)
    }

    product_to_idx = {
        stock_code: idx
        for idx, stock_code in enumerate(products)
    }

    row_indices = train["Customer ID"].map(customer_to_idx).to_numpy()
    col_indices = train["StockCode"].map(product_to_idx).to_numpy()

    values = np.log1p(train["Quantity"].to_numpy())

    matrix = sparse.csr_matrix(
        (
            values,
            (row_indices, col_indices),
        ),
        shape=(len(customers), len(products)),
    )

    customer_map = pd.DataFrame(
        {
            "customer_index": range(len(customers)),
            "Customer ID": customers,
        }
    )

    product_map = pd.DataFrame(
        {
            "product_index": range(len(products)),
            "StockCode": products,
        }
    )

    return matrix, customer_map, product_map


# --------------------------------------------------
# Matrix report
# --------------------------------------------------

def report_matrix(matrix):
    rows, cols = matrix.shape

    total_cells = rows * cols
    nnz = matrix.nnz
    sparsity = 1 - (nnz / total_cells)

    dense_memory_mb = (
        total_cells * np.dtype(np.float64).itemsize
    ) / (1024 ** 2)

    sparse_memory_mb = (
        matrix.data.nbytes
        + matrix.indices.nbytes
        + matrix.indptr.nbytes
    ) / (1024 ** 2)

    print("\nMatrix report")
    print(f"Shape: {rows:,} x {cols:,}")
    print(f"Non-zero entries: {nnz:,}")
    print(f"Sparsity: {sparsity * 100:.2f}%")
    print(f"Dense memory: {dense_memory_mb:.2f} MB")
    print(f"Sparse memory: {sparse_memory_mb:.2f} MB")


# --------------------------------------------------
# Save outputs
# --------------------------------------------------

def save_outputs(
    cleaned,
    train,
    test_new,
    matrix,
    customer_map,
    product_map,
):
    print("\nSaving outputs...")

    cleaned.to_csv(CLEANED_FILE, index=False)
    train.to_csv(TRAIN_FILE, index=False)
    test_new.to_csv(TEST_FILE, index=False)

    sparse.save_npz(MATRIX_FILE, matrix)

    customer_map.to_csv(CUSTOMER_MAP_FILE, index=False)
    product_map.to_csv(PRODUCT_MAP_FILE, index=False)

    print("Saved:")
    print(f"  {CLEANED_FILE}")
    print(f"  {TRAIN_FILE}")
    print(f"  {TEST_FILE}")
    print(f"  {MATRIX_FILE}")
    print(f"  {CUSTOMER_MAP_FILE}")
    print(f"  {PRODUCT_MAP_FILE}")


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    df = load_raw_data()

    cleaned = clean_data(df)

    train, test_new = split_data(cleaned)

    matrix, customer_map, product_map = build_sparse_matrix(train)

    report_matrix(matrix)

    save_outputs(
        cleaned,
        train,
        test_new,
        matrix,
        customer_map,
        product_map,
    )

    print("\nDone.")


if __name__ == "__main__":
    main()