# Multi-Source Healthcare Claims Data Harmonization Pipeline

## Overview

This project is a data engineering pipeline that combines healthcare claims data from three different vendors.

The three vendors provide similar information, but their files have different column names, formats, date formats, and ways of storing diagnosis codes.

The pipeline reads the three source files, converts them into a common format, cleans the data, adds diagnosis descriptions using a dictionary, validates the final dataset, and exports one harmonized CSV file.

The project also includes a FastAPI backend and a simple web dashboard for running the pipeline, viewing results, checking validation, and downloading the final CSV.

---

## Problem Statement

Healthcare claims data from different vendors is often stored in different formats.

For example:

- Vendor A stores multiple diagnosis codes in separate columns.
- Vendor B stores one diagnosis code per row.
- Vendor C stores multiple diagnosis codes in one column.
- Vendor C can contain multiple versions of the same claim.
- Column names are different between vendors.
- Date formats are different.
- Diagnosis codes can contain dots or lowercase letters.
- Some records can have missing patient IDs.
- Duplicate records can exist.

If the files are simply combined without processing, the final dataset can contain duplicates, invalid dates, inconsistent diagnosis codes, and incomplete records.

This project solves this problem by transforming all three sources into one common, clean, and validated dataset.

---

## Objectives

The main objectives are:

- Read claims data from three vendors.
- Understand the different structures used by each vendor.
- Convert each vendor into a common schema.
- Handle multiple diagnosis codes correctly.
- Select the latest Vendor C claim version.
- Normalize diagnosis codes.
- Normalize gender values.
- Convert service dates into proper dates.
- Remove records with missing patient IDs.
- Remove records outside the allowed date range.
- Remove duplicate records.
- Add diagnosis descriptions using the diagnosis dictionary.
- Validate the final dataset.
- Export the final harmonized CSV.
- Provide REST API endpoints.
- Provide a web dashboard for monitoring the pipeline.
- Allow users to download the final dataset.

---

## Architecture

```text
Vendor A CSV
     |
     v
Vendor A Processing
     |
     |
Vendor B CSV
     |
     v
Vendor B Processing
     |
     |
Vendor C CSV
     |
     v
Vendor C Processing
     |
     v
Combine Sources
     |
     v
Global Data Cleaning
     |
     v
Diagnosis Dictionary Lookup
     |
     v
Validation
     |
     v
Final Harmonized CSV
     |
     +------------------+
     |                  |
     v                  v
  FastAPI          Web Dashboard
     |                  |
     +--------+---------+
              |
              v
        Download CSV
```

---

## Input Data

The project uses four input files:

```text
data/
├── source_a_claims.csv
├── source_b_claims.csv
├── source_c_claims.csv
└── dx_dictionary.csv
```

The first three files contain healthcare claims from different vendors.

The fourth file contains diagnosis codes and their descriptions.

The data provided for the assessment is fabricated data.

---

# Vendor Processing

## Vendor A

Vendor A stores multiple diagnosis codes in separate columns.

The diagnosis columns are:

```text
diagnosis_code_1
diagnosis_code_2
diagnosis_code_3
diagnosis_code_4
diagnosis_code_5
diagnosis_code_6
diagnosis_code_7
diagnosis_code_8
```

These columns are converted from columns into rows.

For example:

```text
CLAIM_ID    diagnosis_code_1    diagnosis_code_2    diagnosis_code_3
C001        E11.9                I10                  J18.9
```

becomes:

```text
CLAIM_ID    DIAGNOSIS_CODE
C001        E119
C001        I10
C001        J189
```

Vendor A processing also includes:

- Mapping vendor-specific fields.
- Normalizing diagnosis codes.
- Normalizing gender.
- Converting service dates.
- Creating the common schema.

---

## Vendor B

Vendor B already stores one diagnosis code per row.

Therefore, no diagnosis unpivoting is required.

The pipeline:

- Reads Vendor B.
- Maps Vendor B fields to the common schema.
- Normalizes diagnosis codes.
- Normalizes gender.
- Converts service dates.
- Creates the standardized Vendor B dataset.

---

## Vendor C

Vendor C requires additional processing.

### Latest Version Selection

Vendor C can contain multiple versions of the same claim.

The pipeline sorts the records by claim reference and version and keeps the latest version.

This prevents older versions of the same claim from being included in the final dataset.

### Diagnosis Splitting

Vendor C stores multiple diagnosis codes in one field separated by `|`.

For example:

```text
E119|I10|J189
```

is converted into:

```text
E119
I10
J189
```

Each diagnosis code becomes a separate row.

### Date Conversion

Vendor C uses a different date format.

The pipeline converts the dates into a standard date representation.

---

# Combining the Sources

After each vendor is processed separately, the three standardized datasets are combined.

All three datasets use the same column structure before they are combined.

This makes the final dataset consistent across all vendors.

---

# Global Data Cleaning

The following common cleaning rules are applied after combining the sources.

## 1. Missing Patient IDs

Rows with missing patient identifiers are removed.

The pipeline checks for:

- Null patient IDs.
- Empty patient IDs.
- Missing values represented as strings.

---

## 2. Service Date Range

Only records with service dates between:

```text
2018-01-01
```

and:

```text
2025-02-28
```

are allowed.

Invalid, missing, or out-of-range dates are removed.

---

## 3. Diagnosis Code Normalization

Diagnosis codes are:

- Converted to strings.
- Trimmed.
- Converted to uppercase.
- Converted to the required format by removing dots.

For example:

```text
E11.9
```

becomes:

```text
E119
```

---

## 4. Gender Normalization

Gender values are standardized.

For example:

```text
MALE   -> M
FEMALE -> F
```

---

## 5. Duplicate Removal

The required record grain is:

```text
SRC + CLAIM_ID + DIAGNOSIS_CODE
```

Duplicate records at this grain are removed.

The first occurrence is kept.

---

# Diagnosis Dictionary

The project uses:

```text
dx_dictionary.csv
```

to add diagnosis descriptions.

The diagnosis code in the dictionary is normalized using the same diagnosis normalization logic used for the claims data.

The code is then matched with the harmonized dataset.

The resulting description is stored in:

```text
DIAGNOSIS_DESC
```

If a diagnosis code is not found in the dictionary, its description is left empty rather than assigning an incorrect value.

---

# Final Dataset

The final dataset contains exactly 15 columns:

```text
SRC
PATIENT_ID
BIRTH_YEAR
GENDER
ZIP3
CLAIM_ID
SERVICE_DATE
DIAGNOSIS_CODE
DIAGNOSIS_DESC
PLACE_OF_SERVICE
RENDERING_NPI
REFERRING_NPI
BILLING_NPI
PRIMARY_PLAN_ID
BILLED_AMOUNT
```

## Column Description

| Column | Description |
|---|---|
| SRC | Source vendor |
| PATIENT_ID | Patient identifier |
| BIRTH_YEAR | Patient birth year |
| GENDER | Standardized gender |
| ZIP3 | Three-digit ZIP code |
| CLAIM_ID | Claim identifier |
| SERVICE_DATE | Standardized service date |
| DIAGNOSIS_CODE | Standardized diagnosis code |
| DIAGNOSIS_DESC | Diagnosis description |
| PLACE_OF_SERVICE | Place of service |
| RENDERING_NPI | Rendering provider identifier |
| REFERRING_NPI | Referring provider identifier |
| BILLING_NPI | Billing provider identifier |
| PRIMARY_PLAN_ID | Primary insurance plan |
| BILLED_AMOUNT | Amount billed |

---

# Data Validation

The final dataset is validated before export.

The validation checks include:

- Total rows.
- Distinct claims.
- Distinct patients.
- Distinct diagnosis codes.
- Vendor-wise record counts.
- P00042 total rows.
- P00042 distinct diagnosis codes.
- Diagnosis code format.
- Missing patient IDs.
- Invalid service dates.
- Duplicate records.

---

# Final Validation Results

The successful pipeline run produced the following results:

| Check | Actual | Expected | Result |
|---|---:|---:|---|
| Total rows | 159704 | 159704 | PASS |
| Distinct claims | 68205 | 68205 | PASS |
| Distinct patients | 11963 | 11963 | PASS |
| Distinct diagnosis codes | 44 | 44 | PASS |
| P00042 total rows | 7 | 7 | PASS |
| P00042 diagnosis codes | 7 | 7 | PASS |
| Invalid diagnosis codes | 0 | 0 | PASS |
| Missing patient IDs | 0 | 0 | PASS |
| Invalid service dates | 0 | 0 | PASS |
| Duplicate rows | 0 | 0 | PASS |

Overall result:

```text
all_checks_passed = true
```

---

# Final Dataset Statistics

```text
Total rows                : 159704
Distinct claims           : 68205
Distinct patients         : 11963
Distinct diagnosis codes  : 44
```

## Final Records by Vendor

```text
Vendor A : 67531
Vendor B : 52819
Vendor C : 39354
```

The source counts add up to the final row count:

```text
67531 + 52819 + 39354 = 159704
```

---

# Output

The final dataset is generated as:

```text
output/final_harmonized.csv
```

Final dataset:

```text
159704 rows
15 columns
```

The CSV is exported only after the validation step succeeds.

---

# FastAPI Backend

The project includes a FastAPI backend to interact with the pipeline.

The backend provides endpoints to:

- Check whether the API is running.
- Run the pipeline.
- View pipeline stages.
- View validation results.
- View dataset summary.
- Download the final CSV.

---

# API Endpoints

## 1. Health Check

```http
GET /
```

Checks whether the API is running.

---

## 2. Run Pipeline

```http
POST /run
```

Runs the complete pipeline.

The response contains:

- Run ID.
- Status.
- Start time.
- Completion time.
- Number of rows.
- Output file.
- Pipeline stages.

---

## 3. Pipeline Stages

```http
GET /run/{run_id}/stages
```

Returns the processing stages for a pipeline run.

The stages are:

```text
Ingestion
Combination
Cleaning
Dictionary Lookup
Validation
Export
```

---

## 4. Validation

```http
GET /run/{run_id}/validate
```

Returns the validation checks for the selected run.

Each check contains its actual value, expected value where applicable, and pass/fail status.

---

## 5. Summary

```http
GET /summary
```

Returns:

- Total rows.
- Distinct claims.
- Distinct patients.
- Distinct diagnosis codes.
- Source-wise record counts.

---

## 6. Download

```http
GET /download
```

Downloads:

```text
final_harmonized.csv
```

---

# Dashboard

The project contains a simple web dashboard built using:

- HTML
- CSS
- JavaScript

The dashboard connects to the FastAPI backend.

The dashboard does not use hard-coded final dataset statistics. Values are obtained from the API after a pipeline run.

The dashboard displays:

## Data Cleaning Summary

```text
Initial Records
Missing Patients
Invalid Dates
Invalid Diagnoses
Duplicate Rows
Total Removed
Final Records
```

## Final Records by Vendor

```text
Vendor A
Vendor B
Vendor C
```

## Validation Results

The dashboard displays the acceptance checks returned by:

```http
GET /run/{run_id}/validate
```

## Pipeline Stages

```text
Ingestion
Combination
Cleaning
Dictionary Lookup
Validation
Export
```

## Actions

The dashboard provides:

```text
Run Pipeline
Download CSV
```

---

# Screenshots

The repository contains screenshots showing the working application.

## Pipeline Dashboard

![Pipeline Dashboard](screenshots/run-page.png)

## Validation Results

![Validation Results](screenshots/validation.png)

The screenshots show the pipeline run, cleaning information, final records by vendor, pipeline stages, and validation results.

---

# Technology Stack

## Backend

- Python
- FastAPI
- Uvicorn

## Data Processing

- Pandas
- CSV

## Frontend

- HTML
- CSS
- JavaScript

## Development Tools

- Visual Studio Code
- Git
- GitHub

---

# Project Structure

```text
Malar_Assessment/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── pipeline.py
│   └── validation.py
│
├── data/
│   ├── source_a_claims.csv
│   ├── source_b_claims.csv
│   ├── source_c_claims.csv
│   └── dx_dictionary.csv
│
├── output/
│   └── final_harmonized.csv
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── screenshots/
│   ├── run-page.png
│   └── validation.png
│
├── DESIGN_NOTES.md
├── README.md
├── requirements.txt
└── .gitignore
```

---

# Installation

## 1. Clone the Repository

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Malar_Assessment
```

## 2. Create Virtual Environment

```powershell
python -m venv venv
```

## 3. Activate Virtual Environment

```powershell
venv\Scripts\activate
```

## 4. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

# Running the Pipeline

Make sure the virtual environment is activated.

Run:

```powershell
python app/pipeline.py
```

The pipeline performs the following steps:

```text
1. Process Vendor A
2. Process Vendor B
3. Process Vendor C
4. Select latest Vendor C versions
5. Split diagnosis codes
6. Combine all sources
7. Perform global cleaning
8. Add diagnosis descriptions
9. Validate the dataset
10. Export the final CSV
```

The output is:

```text
output/final_harmonized.csv
```

---

# Running the FastAPI Backend

Start the backend using:

```powershell
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

---

# FastAPI Documentation

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

# Running the Dashboard

Open:

```text
frontend/index.html
```

using VS Code Live Server.

Make sure the FastAPI backend is running first.

The dashboard connects to:

```text
http://127.0.0.1:8000
```

---

# Data Privacy

The assessment data is fabricated.

For repository management:

- Raw datasets should not be committed to a public GitHub repository unless required.
- Generated output files should not be committed unless required.
- API keys must not be committed.
- `.env` files must not be committed.
- Virtual environment files should not be committed.

---

# .gitignore

Recommended `.gitignore`:

```gitignore
venv/
.venv/

__pycache__/
*.py[cod]

.env

data/*.csv
data/*.xlsx

output/*.csv

.vscode/
.idea/

.DS_Store
Thumbs.db
```

---

# Future Improvements

If this pipeline had to process much larger datasets or run in production, I would consider:

- Database storage instead of local CSV files.
- Batch processing.
- Cloud storage.
- Automated data ingestion.
- Scheduled pipeline execution.
- Better logging and monitoring.
- Authentication and authorization.
- Data lineage tracking.
- Automated testing.
- Docker deployment.
- CI/CD.
- More detailed data-quality reports.

---

# Conclusion

This project provides a complete data harmonization workflow for healthcare claims data from three different vendors.

The pipeline handles vendor-specific transformations, diagnosis-code normalization, date conversion, missing data, duplicate records, diagnosis dictionary mapping, validation, and final CSV generation.

A FastAPI backend provides access to the pipeline, while the web dashboard provides a simple way to run and monitor the process.

The final validated dataset contains:

```text
159704 records
15 columns
68205 distinct claims
11963 distinct patients
44 diagnosis codes
```

All required validation checks passed successfully.

---

# Author

Developed as a Data Engineering Internship Assessment Project.