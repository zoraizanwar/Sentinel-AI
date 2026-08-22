# Sentinel AI — Dataset Documentation & Inspection Report

## 1. Dataset Overview

- **Dataset Name**: Credit Card Transactions Fraud Detection Dataset
- **Author / Generator**: Kartik Shenoy (Sparkov Data Generation Simulator)
- **Primary Source**: [Kaggle Dataset Repository](https://www.kaggle.com/datasets/kartik2112/fraud-detection)
- **License**: CC0: Public Domain (Open for commercial, academic, and portfolio use)
- **Domain**: Simulated Legitimate & Fraudulent Credit Card Transactions across US merchant networks and cardholders.

---

## 2. Actual Inspected Files & Verified Dimensions

Data inspection was executed directly on the physical CSV files stored in `data/raw/` with zero fabricated values.

| Dataset File | File Size (Bytes) | Exact Row Count | Exact Column Count | Target Column | Fraud Count (Class = 1) | Legitimate Count (Class = 0) | Fraud Percentage | Class Imbalance Ratio |
|---|---|---|---|---|---|---|---|---|
| **`data/raw/fraudTrain.csv`** | 351,238,196 (~351 MB) | **1,296,675** | **23** | `is_fraud` | **7,506** | **1,289,169** | **0.578865%** | **171.75:1** (~1 in 173) |
| **`data/raw/fraudTest.csv`** | 150,354,339 (~150 MB) | **555,719** | **23** | `is_fraud` | **2,145** | **553,574** | **0.385986%** | **258.08:1** (~1 in 259) |
| **Combined Total** | 501,592,535 (~501 MB) | **1,852,394** | **23** | `is_fraud` | **9,651** | **1,842,743** | **0.521001%** | **190.94:1** |

*Note on Imbalance Ratio*: The ingestion engine dynamically computes `imbalance_ratio = round(legitimate_count / fraud_count, 2)` for any uploaded file or partition.

---

## 3. Schema & Data Type Breakdown

All 23 columns present identically in both `fraudTrain.csv` and `fraudTest.csv`:

| Column Name | Physical Data Type | Logical Type | Unique Values (`fraudTrain`) | Null Count | Description |
|---|---|---|---|---|---|
| `Unnamed: 0` | `int64` | Row Index | 1,296,675 | 0 | Sequential index from original dataset export. |
| `trans_date_trans_time` | `object / str` | Timestamp | 1,274,791 | 0 | Format: `YYYY-MM-DD HH:MM:SS`. |
| `cc_num` | `int64` | Credit Card ID | 983 | 0 | Masked cardholder account number. |
| `merchant` | `object / str` | Categorical | 693 | 0 | Merchant business entity name (e.g. `fraud_Rippin, Kub and Mann`). |
| `category` | `object / str` | Categorical | 14 | 0 | Merchant category (e.g., `grocery_pos`, `shopping_net`, `gas_transport`). |
| `amt` | `float64` | Continuous Amount | 52,928 | 0 | Transaction monetary value in USD ($1.00 to $28,948.90). |
| `first` | `object / str` | Text (PII) | 352 | 0 | Cardholder first name. |
| `last` | `object / str` | Text (PII) | 481 | 0 | Cardholder last name. |
| `gender` | `object / str` | Categorical | 2 (`M`, `F`) | 0 | Cardholder gender. |
| `street` | `object / str` | Text (PII) | 983 | 0 | Cardholder street address. |
| `city` | `object / str` | Categorical | 894 | 0 | Cardholder city. |
| `state` | `object / str` | Categorical | 51 (US States + DC) | 0 | Cardholder state. |
| `zip` | `int64` | Geographic Code | 970 | 0 | Cardholder ZIP / postal code. |
| `lat` | `float64` | Geographic Coord | 968 | 0 | Cardholder residential latitude. |
| `long` | `float64` | Geographic Coord | 969 | 0 | Cardholder residential longitude. |
| `city_pop` | `int64` | Numerical | 879 | 0 | Population of cardholder's city (23 to 2,906,700). |
| `job` | `object / str` | Categorical | 494 | 0 | Cardholder profession. |
| `dob` | `object / str` | Date (DOB) | 968 | 0 | Cardholder date of birth (`YYYY-MM-DD`). |
| `trans_num` | `object / str` | Unique ID | 1,296,675 | 0 | Hexadecimal transaction identifier string. |
| `unix_time` | `int64` | Epoch Timestamp | 1,274,823 | 0 | Seconds since Unix epoch. |
| `merch_lat` | `float64` | Geographic Coord | 1,247,805 | 0 | Merchant terminal latitude. |
| `merch_long` | `float64` | Geographic Coord | 1,275,745 | 0 | Merchant terminal longitude. |
| `is_fraud` | `int64` | **Target Label** | 2 (`0`, `1`) | 0 | Ground truth fraud label (0 = Legit, 1 = Fraud). |

---

## 4. Train vs. Test Split Relationship & Chronological Integrity

| Evaluation Dimension | `fraudTrain.csv` | `fraudTest.csv` | Analysis & Conclusion |
|---|---|---|---|
| **Earliest Transaction** | `2019-01-01 00:00:18` | `2020-06-21 12:14:25` | **Strict Chronological Sequence**: Test begins exactly 48 seconds after Train concludes. |
| **Latest Transaction** | `2020-06-21 12:13:37` | `2020-12-31 23:59:34` | Zero temporal overlap. |
| **Cardholder (`cc_num`) Overlap** | 983 unique accounts | 924 unique accounts | **908 accounts overlap** between train and test (92.4%), representing repeated real-world cardholder activity over time. |
| **Merchant Overlap** | 693 unique merchants | 693 unique merchants | 100% merchant ecosystem overlap. |
| **Transaction ID (`trans_num`) Overlap** | 1,296,675 unique IDs | 555,719 unique IDs | **0 duplicate transactions**. |

---

## 5. Comprehensive Leakage Analysis & Feature Categorization

To ensure production-grade statistical rigor, every column has been audited against **Target Leakage**, **Identifier Memorization**, and **Future-Information Contamination**:

| Column | Leakage / Risk Assessment | Pipeline Treatment |
|---|---|---|
| `Unnamed: 0` | Arbitrary row index | **EXCLUDE from ML**. Dropped immediately. |
| `trans_num` | Unique 32-character transaction hash (1-to-1 cardinality) | **EXCLUDE from ML**. Retained strictly as transaction metadata / query key. |
| `cc_num` | High-cardinality account number. Direct inclusion causes tree memorization. | **EXCLUDE as raw numeric**. Never passed to ML models. |
| `first`, `last`, `street` | PII names and addresses. | **EXCLUDE from ML**. Retained strictly as investigator display metadata. |
| `dob` | Static birthdate string. | **TRANSFORM**: Converted to derived feature `customer_age_years` (relative to transaction timestamp). |
| `trans_date_trans_time` / `unix_time` | Absolute epoch timestamps. Raw inclusion causes temporal overfit. | **TRANSFORM**: Extracted cyclical domain features: `hour_of_day` (0-23), `day_of_week` (0-6), and `is_night_hours` (00:00 - 06:00). |
| `amt` | Core monetary signal ($1.00 to $28,948.90). | **INCLUDE & SCALE**: Key predictive feature. Log-transformed continuous feature. |
| `category`, `gender`, `state`, `job` | Low-to-medium cardinality business categories. | **INCLUDE with One-Hot encoding** (fitted on train split only). |
| `lat`, `long`, `merch_lat`, `merch_long` | Separate customer and merchant coordinate pairs. | **TRANSFORM**: Computed derived **Haversine Distance** ($\text{km}$) between cardholder and merchant terminal. |
| `city_pop` | Numerical regional population. | **INCLUDE & SCALE**: Indicator for rural vs. metropolitan fraud vectors. |
