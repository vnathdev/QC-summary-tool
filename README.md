# 🏙️ Quality Check Dashboard

A multi-city Streamlit dashboard for analysing ticket quality check results.

**Supported cities:** Agra · Lucknow · Mathura · Prayagraj

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
streamlit run app.py
```

The dashboard opens at **http://localhost:8501**

---

## 📂 Expected File Formats

| City       | Format        | Key QC Column(s)                            |
|------------|---------------|---------------------------------------------|
| Agra       | `.csv` / `.xlsx` | `Quality (1st L)`, `Quality of QC (2nd L)` |
| Lucknow    | `.xlsx`       | `Quality (L1)`, `Quality (L2)`              |
| Mathura    | `.xlsx`       | `Status.1` (ok / wrong)                     |
| Prayagraj  | `.xlsx`       | `Review Status`                              |

---

## 📊 Dashboard Features

- **Overview tab** — side-by-side city comparison, combined failure reasons, complaint type breakdown
- **Per-city tabs** — L1/L2 QC pies, failure reasons, zone breakdown, monthly trend, agent performance table
- **Raw data viewer** — expandable table in each city tab

---

## 🗂️ Project Structure

```
qc_dashboard/
├── app.py            # Main Streamlit application
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

---

## ➕ Adding a New City

1. Write a `parse_<city>(file) -> pd.DataFrame` function in `app.py`
   that maps your columns to the standard schema below.
2. Add the city name to the `CITIES` list.
3. Register the parser in the `PARSERS` dict.

**Standard schema columns:**

| Column           | Description                              |
|------------------|------------------------------------------|
| `city`           | City name string                         |
| `ticket_id`      | Unique complaint / issue ID              |
| `qc_l1`          | L1 QC result: Correct / Incorrect / Pending / WIP / Not Feasible |
| `qc_l2`          | L2 QC result (same values, or None)      |
| `fail_reason_l1` | Reason for Incorrect at L1               |
| `fail_reason_l2` | Reason for Incorrect at L2               |
| `reviewer`       | Surveyor / agent / QC officer name       |
| `zone`           | Zone name or number                      |
| `ward`           | Ward name or number                      |
| `complaint_type` | Primary complaint category               |
| `complaint_subtype` | Sub-category (optional)               |
| `sla_status`     | "Within SLA" / "Beyond SLA" / ""         |
| `reg_date`       | Complaint registration date (datetime)   |
| `res_date`       | Resolution date (datetime)               |
