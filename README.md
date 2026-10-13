# Customers Like You

Mini-project for customer recommendation and segmentation using the UCI Online Retail II dataset.

The goal is to compress a large customer-product purchase matrix, generate product recommendations, compare PCA and Truncated SVD, and identify meaningful customer segments for marketing.

## Dataset

The project uses the UCI Online Retail II dataset, containing transactions from December 2009 to December 2011.

The raw dataset contains:

- 1,067,371 transaction rows
- 2 yearly sheets
- Customer, product, quantity, price, date, and country information

The raw dataset is stored locally in:

`data/raw/online_retail_II.xlsx`

The `data/` folder is excluded from Git.

## Project Goals

The project evaluates whether dimensionality reduction can:

- Reduce the size of the customer-product representation
- Produce recommendations faster
- Beat a simple best-seller recommendation baseline
- Identify meaningful customer segments for marketing

## Data Cleaning

The following rows were removed:

- Cancelled invoices
- Non-positive quantities
- Non-positive prices
- Missing Customer IDs
- Non-product codes

After cleaning, 802,965 transaction rows remained.

## Train/Test Split

The final two months of transactions were reserved as the test period.

- Training rows: 684,357
- Test-period rows: 118,608
- Held-out new-product rows: 72,924

Only products that a customer had not previously purchased were kept as held-out test purchases.

## Customer-Product Matrix

A sparse customer-product matrix was built using log-transformed purchase quantities.

- Matrix shape: 5,484 customers × 4,537 products
- Non-zero entries: 417,809
- Sparsity: 98.32%
- Dense memory estimate: 189.83 MB
- Sparse memory: 4.80 MB

The high sparsity supports using Truncated SVD as the main dimensionality-reduction method.

## Truncated SVD

Truncated SVD was selected because it can operate directly on sparse data without centering.

The following values of k were tested:

- 10
- 20
- 50
- 100
- 200

A final value of **k = 100** was selected as a balance between reconstruction quality, runtime, and model size.

At k = 100:

- Relative reconstruction error: 0.4961
- Fit time: approximately 0.76 seconds

## Recommendation Results

The recommender uses cosine similarity between product factor vectors.

Evaluation was performed using Hit Rate@10 on held-out purchases.

- SVD Hit Rate@10: 20.26%
- Best-seller baseline Hit Rate@10: 15.54%
- Nightly recommendation runtime: 1.35 seconds for 1,930 customers

The SVD recommender performed better than simply recommending the most popular products.

## PCA vs SVD

Both methods were evaluated using k = 100.

| Measure | PCA | Truncated SVD |
|---|---:|---:|
| Fit time | 0.48 s | 0.76 s |
| Stored factors | 7.65 MB | 7.65 MB |
| Explained variance / reconstruction error | 74.82% explained variance | 0.4961 relative error |
| Hit Rate@10 | 20.21% | 20.26% |
| Best-seller baseline | 15.54% | 15.54% |

Both methods produced similar recommendation accuracy. Truncated SVD was preferred because it works naturally with sparse customer-product data.

## Customer Segments

Customers were clustered using normalized SVD customer representations.

Four customer segments were identified:

- Cluster 0: Home & Utility — 2,419 customers
- Cluster 1: Novelty & Party — 1,532 customers
- Cluster 2: Bags & Storage — 702 customers
- Cluster 3: Decorative Homeware — 831 customers

Normalization was used before clustering so the groups reflected purchase patterns rather than only purchase volume.

## Repository Structure

```text
customers-like-you/
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
│   ├── 01_data_profile.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_train_test_matrix.ipynb
│   ├── 04_svd_model.ipynb
│   └── 05_customer_segments.ipynb
├── README.md
├── requirements.txt
└── .gitignore