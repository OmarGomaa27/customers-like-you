# Customers Like You

**GitHub:** https://github.com/omargomaa27/customers-like-you

Mini-project for customer recommendation and segmentation using the UCI Online Retail II dataset.

The goal is to compress a large customer-product purchase matrix, generate product recommendations, compare PCA and Truncated SVD, and identify meaningful customer segments for marketing.

**Individual project — I performed both the Data Engineer and ML Engineer roles.**

## Success Targets

The project succeeds if it can show, with numbers, that:

1. The compressed representation is much smaller than the dense customer-product matrix.
2. The nightly recommendation job is fast enough to run every night.
3. The recommender beats a best-seller baseline on purchases the model never saw.
4. The customer map produces groups the marketing team can name and campaign against.

## Dataset

The project uses the UCI Online Retail II dataset, containing transactions from December 2009 to December 2011.

The raw dataset contains:

- 1,067,371 transaction rows
- 2 yearly sheets
- Customer, product, quantity, price, date, and country information

The raw dataset is stored locally in:

`data/raw/online_retail_II.xlsx`

The `data/` folder is excluded from Git.

## How to Run

1. Clone the repository and enter the project folder:

   ```bash
   git clone https://github.com/omargomaa27/customers-like-you.git
   cd customers-like-you
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Download `online_retail_II.xlsx` from the [UCI repository](https://archive.ics.uci.edu/dataset/502/online+retail+ii) and place it at:

   `data/raw/online_retail_II.xlsx`

4. Rebuild the cleaned data, train/test split, and sparse customer-product matrix with:

   ```bash
   python build_matrix.py
   ```

   This regenerates:

   - `data/processed/cleaned_retail.csv`
   - `data/processed/train.csv`
   - `data/processed/test_new.csv`
   - `data/processed/customer_product_matrix.npz`
   - `data/processed/customer_map.csv`
   - `data/processed/product_map.csv`

5. Run the notebooks in order for the full analysis:

   | Notebook | Purpose |
   |---|---|
   | `01_data_profile.ipynb` | Profile the raw dataset |
   | `02_data_cleaning.ipynb` | Document and inspect the cleaning process |
   | `03_train_test_matrix.ipynb` | Document the split and sparse matrix construction |
   | `04_svd_model.ipynb` | Train/evaluate SVD, PCA, recommendations, and baseline |
   | `05_customer_segments.ipynb` | Create customer segments and save the segment map |

   Run each notebook from a clean kernel, top to bottom. All random seeds are fixed at `random_state=42`.

`build_matrix.py` is the reproducible one-command path for rebuilding the cleaned dataset and customer-product matrix from the raw Excel file. The notebooks provide the full analysis, explanations, model evaluation, and visualizations.

## Data Cleaning

| Cleaning rule | Rows removed | Rows remaining |
|---|---:|---:|
| Starting dataset | 0 | 1,067,371 |
| Remove cancelled invoices | 19,494 | 1,047,877 |
| Remove non-positive quantities | 3,457 | 1,044,420 |
| Remove non-positive prices | 2,750 | 1,041,670 |
| Remove missing Customer IDs | 236,121 | 805,549 |
| Remove non-product codes | 2,991 | 802,558 |

After cleaning, 802,558 transaction rows remained.

Non-product codes cover postage, carriage, discounts, adjustments, bank charges and test transactions: `POST`, `M`, `D`, `BANK CHARGES`, `C2`, `DOT`, `ADJUST`, `ADJUST2`, `TEST001`, `TEST002`, `23444` (Next Day Carriage) and `23574` (PACKING CHARGE). The last two use ordinary five-digit codes and are identifiable only from their descriptions. `PADS` and `SP1002` were kept because their descriptions identify genuine products.

## Train/Test Split

The final two months of transactions were reserved as the test period.

- Training rows: 684,043
- Test-period rows: 118,515
- Held-out new-product rows: 72,876

Only products that a customer had not previously purchased were kept as held-out test purchases.

## Customer-Product Matrix

A sparse customer-product matrix was built using log-transformed purchase quantities.

- Matrix shape: 5,474 customers × 4,529 products
- Non-zero entries: 417,700
- Sparsity: 98.32%
- Dense memory estimate: 189.15 MB
- Sparse memory: 4.80 MB

The high sparsity supports using Truncated SVD as the main dimensionality-reduction method.

## Truncated SVD

Truncated SVD was selected because it can operate directly on sparse data without centering.

The following values of k were tested:

| k | Fit time | Relative reconstruction error |
|---:|---:|---:|
| 10 | 0.12 s | 0.7562 |
| 20 | 0.22 s | 0.6875 |
| 50 | 0.57 s | 0.5845 |
| 100 | 1.13 s | 0.4961 |
| 200 | 2.39 s | 0.3993 |

A final value of **k = 100** was selected as a balance between reconstruction quality, runtime, and model size.

## Recommendation Results

The recommender uses cosine similarity between product factor vectors.

Evaluation was performed using Hit Rate@10 on held-out purchases.

- SVD Hit Rate@10: 20.60%
- Best-seller baseline Hit Rate@10: 17.28%
- Nightly recommendation runtime: 1.56 seconds for 1,927 customers

The baseline recommends each customer the 10 best sellers they have not already bought, and is measured over the same 1,927 customers the model can score, so the two figures are directly comparable.

The SVD recommender outperformed the best-seller baseline by 3.3 percentage points.

## PCA vs SVD

Both methods were evaluated using k = 100.

| Measure | PCA | Truncated SVD |
|---|---:|---:|
| Fit time | 0.48 s | 1.01 s |
| Peak memory during fit | 17.92 MB | 17.70 MB |
| Stored factors | 7.63 MB | 7.63 MB |
| Explained variance / reconstruction error | 74.81% explained variance | 0.4961 relative error |
| Hit Rate@10 | 20.13% | 20.60% |
| Best-seller baseline | 17.28% | 17.28% |

Fit time and peak memory are measured on the same profiled fit, so the two rows describe one run. Timings vary slightly between runs.

Both methods produced similar recommendation accuracy. Truncated SVD was preferred because it works naturally with sparse customer-product data.

## Customer Segments

Customers were clustered using normalized SVD customer representations.

Cluster numbers from KMeans are arbitrary and can permute between runs, so each segment is named from the highest-volume product in that cluster rather than from its cluster number.

| Cluster | Top product | Segment name | Customers |
|---:|---|---|---:|
| 0 | WHITE HANGING HEART T-LIGHT HOLDER | Decorative Homeware | 831 |
| 1 | MEDIUM CERAMIC TOP STORAGE JAR | Home & Utility | 2,375 |
| 2 | JUMBO BAG RED RETROSPOT | Bags & Storage | 693 |
| 3 | WORLD WAR 2 GLIDERS ASSTD DESIGNS | Novelty & Party | 1,575 |

Normalization was used before clustering so the groups reflected purchase patterns rather than only purchase volume.

The segment map is saved to `figures/customer_segments.png` and contains no customer IDs.

## Repository Structure

```text
customers-like-you/
├── build_matrix.py
├── data/
│   ├── raw/
│   └── processed/
├── figures/
│   └── customer_segments.png
├── notebooks/
│   ├── 01_data_profile.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_train_test_matrix.ipynb
│   ├── 04_svd_model.ipynb
│   └── 05_customer_segments.ipynb
├── README.md
├── requirements.txt
└── .gitignore
```
