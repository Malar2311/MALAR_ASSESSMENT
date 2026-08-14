# Multi-Source Healthcare Claims Data Harmonization Pipeline

## Overview

This project is a Python-based data engineering pipeline designed to integrate, standardize, clean, validate, and enrich healthcare claims data received from multiple vendor sources.

The system processes data from Vendor A, Vendor B, and Vendor C, converts them into a common schema, performs data quality checks, maps diagnosis codes using a reference dictionary, and generates a final harmonized dataset.

The project also provides a FastAPI backend and a web dashboard for running the pipeline, viewing dataset statistics, monitoring the processing workflow, and downloading the final CSV file.

---

## Problem Statement

Healthcare claims data received from different vendors often has different structures, column names, date formats, diagnosis representations, and data quality issues.

Combining these datasets directly can result in duplicate records, invalid dates, missing patient information, inconsistent diagnosis codes, and unreliable analysis.

This project provides a standardized data pipeline to transform multiple vendor datasets into a single clean, validated, and harmonized healthcare claims dataset.

---

## Objectives

- Integrate healthcare claims data from multiple vendors.
- Standardize vendor-specific schemas.
- Normalize patient and claim identifiers.
- Standardize service dates.
- Normalize diagnosis codes.
- Handle multiple diagnosis codes.
- Select the latest applicable Vendor C records.
- Combine all vendor datasets.
- Remove invalid and incomplete records.
- Remove duplicate records.
- Apply a common service-date range.
- Enrich diagnosis codes using a reference dictionary.
- Validate the final dataset.
- Export the final standardized CSV.
- Provide REST APIs for accessing the processed data.
- Provide a dashboard for monitoring the pipeline.
- Allow users to download the final harmonized dataset.

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
Diagnosis Dictionary Mapping
     |
     v
Dataset Validation
     |
     v
Final Harmonized CSV
     |
     +-------------------+
     |                   |
     v                   v
  FastAPI            Web Dashboard
     |                   |
     +---------+---------+
               |
               v
         Download CSV
```

---

## Data Sources

The project uses three vendor datasets and one diagnosis reference dictionary.

```text
data/
├── source_a_claims.csv
├── source_b_claims.csv
├── source_c_claims.csv
└── dx_dictionary.csv
```

---

## Vendor A Processing

Vendor A data is transformed into the common healthcare claims schema.

Processing includes:

- Reading Vendor A data
- Standardizing column names
- Normalizing patient identifiers
- Converting service dates
- Standardizing diagnosis codes
- Mapping vendor-specific fields
- Creating the standardized Vendor A dataset

Vendor A:

```text
Input rows  : 26,004
Output rows : 71,457
```

---

## Vendor B Processing

Vendor B contains a different structure from Vendor A.

Processing includes:

- Reading Vendor B data
- Standardizing field names
- Converting service dates
- Normalizing identifiers
- Standardizing financial fields
- Mapping vendor fields to the common schema

Vendor B:

```text
Input rows  : 53,891
Output rows : 53,891
```

---

## Vendor C Processing

Vendor C requires additional processing because it contains multiple record versions and multiple diagnosis codes.

### Latest Version Selection

The latest applicable version of Vendor C records is selected.

```text
Input rows                     : 24,186
After latest-version selection : 20,001
```

### Diagnosis Splitting

Multiple diagnosis codes are separated into individual diagnosis records.

```text
Rows after diagnosis splitting : 40,171
```

### Date Conversion

Vendor C dates are converted into a standardized date format.

Example:

```text
11-03-2023
24-02-2022
06-11-2023
```

are converted to standardized dates.

### Final Vendor C Output

```text
Vendor C output rows : 40,171
```

---

## Data Harmonization

After individual vendor processing, all three datasets are combined.

```text
Vendor A : 71,457
Vendor B : 53,891
Vendor C : 40,171
------------------
Combined : 165,519
```

All three vendor datasets are converted into a common standardized schema before combination.

---

## Global Data Cleaning

Global cleaning is performed after combining the three vendor datasets.

### Missing Patient IDs

Records with missing patient identifiers are removed.

```text
Rows removed : 1,127
```

### Invalid or Out-of-Range Dates

The accepted service date range is:

```text
2018-01-01 to 2025-02-28
```

Records outside this range are removed.

```text
Rows removed : 3,226
```

### Duplicate Records

Duplicate records are identified and removed.

```text
Rows removed : 1,462
```

### Final Cleaning Result

```text
Before cleaning : 165,519
Rows removed    : 5,815
After cleaning  : 159,704
```

---

## Diagnosis Dictionary Mapping

The project uses a diagnosis dictionary to add descriptions to standardized diagnosis codes.

The dictionary contains:

```text
dx_code
dx_description
icd_version
```

The standardized diagnosis code is matched against the dictionary and the corresponding description is added to:

```text
DIAGNOSIS_DESC
```

If a diagnosis code is not available in the dictionary, its description is left empty rather than assigning an incorrect value.

---

## Final Dataset Schema

The final harmonized dataset contains 15 columns.

```text
SRC
PATIENT_ID
BIRTH_YEAR
GENDER
ZIP3
CLAIM_ID
SERVICE_DATE
DIAGNOSIS_CODE
PLACE_OF_SERVICE
RENDERING_NPI
REFERRING_NPI
BILLING_NPI
PRIMARY_PLAN_ID
BILLED_AMOUNT
DIAGNOSIS_DESC
```

### Column Description

| Column | Description |
|---|---|
| SRC | Source vendor |
| PATIENT_ID | Standardized patient identifier |
| BIRTH_YEAR | Patient birth year |
| GENDER | Patient gender |
| ZIP3 | Three-digit ZIP code |
| CLAIM_ID | Healthcare claim identifier |
| SERVICE_DATE | Standardized service date |
| DIAGNOSIS_CODE | Standardized diagnosis code |
| PLACE_OF_SERVICE | Healthcare service location |
| RENDERING_NPI | Rendering provider identifier |
| REFERRING_NPI | Referring provider identifier |
| BILLING_NPI | Billing provider identifier |
| PRIMARY_PLAN_ID | Primary insurance plan identifier |
| BILLED_AMOUNT | Amount billed |
| DIAGNOSIS_DESC | Diagnosis description |

---

## Data Validation

The final dataset is validated before export.

Validation checks include:

- Total row count
- Distinct claim count
- Distinct patient count
- Distinct diagnosis code count
- Source-level record counts
- Invalid service dates
- Missing patient IDs
- Duplicate records

---

## Final Dataset Statistics

```text
Total rows              : 159,704
Distinct claims         : 68,205
Distinct patients       : 11,963
Distinct diagnosis codes: 44
```

### Source Counts

```text
Vendor A : 67,531
Vendor B : 52,819
Vendor C : 39,354
```

### Validation Results

```text
Missing patient IDs : 0
Invalid dates       : 0
Duplicate rows      : 0
```

All final validation checks passed successfully.

---

## Output

The final dataset is generated as:

```text
output/final_harmonized.csv
```

Final dataset shape:

```text
159,704 rows
15 columns
```

---

## Technology Stack

### Backend

- Python
- FastAPI
- Uvicorn

### Data Processing

- Pandas
- CSV

### Frontend

- HTML
- CSS
- JavaScript

### Development Tools

- Visual Studio Code
- Git
- GitHub

---

## Project Structure

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
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Installation

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Malar_Assessment
```

### 2. Create Virtual Environment

```powershell
python -m venv venv
```

### 3. Activate Virtual Environment

```powershell
venv\Scripts\activate
```

### 4. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

## Running the Pipeline

Make sure the virtual environment is activated.

Run:

```powershell
python app/pipeline.py
```

The pipeline will:

1. Process Vendor A.
2. Process Vendor B.
3. Process Vendor C.
4. Select the latest Vendor C versions.
5. Split diagnosis codes.
6. Combine all sources.
7. Perform global cleaning.
8. Map diagnosis descriptions.
9. Validate the final dataset.
10. Export the final CSV.

The output will be:

```text
output/final_harmonized.csv
```

---

## Running the FastAPI Backend

Start the backend using:

```powershell
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

---

## FastAPI Documentation

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

## Running the Dashboard

Open the following file using VS Code Live Server:

```text
frontend/index.html
```

Make sure FastAPI is running before opening the dashboard.

The dashboard connects to:

```text
http://127.0.0.1:8000
```

---

## API Endpoints

### Health Check

```http
GET /
```

Checks whether the API is running.

### Dataset Summary

```http
GET /summary
```

Returns:

- Total records
- Distinct claims
- Distinct patients
- Distinct diagnosis codes
- Vendor-wise record counts

### Run Pipeline

```http
POST /run
```

Runs the complete data harmonization pipeline.

### Pipeline Stages

```http
GET /run/{run_id}/stages
```

Returns the processing stages for a pipeline run.

### Validation

```http
GET /run/{run_id}/validate
```

Returns validation results for a completed pipeline run.

### Download Final CSV

```http
GET /download
```

Downloads the final harmonized dataset:

```text
final_harmonized.csv
```

---

## Dashboard Features

The dashboard provides:

### Dataset Summary

Displays:

- Total records
- Claims
- Patients
- Diagnosis codes

### Source Distribution

Displays the number of records from:

- Vendor A
- Vendor B
- Vendor C

### Pipeline Stages

Displays:

```text
✓ Ingestion
✓ Combination
✓ Cleaning
✓ Dictionary Lookup
✓ Validation
✓ Export
```

### Run Pipeline

The user can execute the complete pipeline using:

```text
Run Pipeline
```

### Download CSV

The user can download the final harmonized dataset using:

```text
Download CSV
```

---

## Data Privacy

The input datasets contain healthcare-related claims information.

For privacy and repository management:

- Raw input datasets should not be uploaded to a public GitHub repository.
- Generated output datasets should not be committed unless required.
- Sensitive information should be excluded from public repositories.
- API keys and environment variables must not be committed.

The `.gitignore` file excludes raw datasets, generated outputs, virtual environments, and environment files.

---

## .gitignore

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

## Future Enhancements

Possible future improvements include:

- Database integration
- Cloud deployment
- Automated data ingestion
- Scheduled pipeline execution
- Authentication and authorization
- Advanced data quality reporting
- Interactive analytics
- Error monitoring
- Pipeline logging
- Data lineage tracking
- Docker deployment
- CI/CD integration

---

## Conclusion

This project provides a complete data harmonization workflow for integrating healthcare claims data from multiple vendor sources.

The pipeline handles vendor-specific transformations, schema standardization, data cleaning, diagnosis enrichment, validation, and final dataset generation.

The system also provides a FastAPI backend and web dashboard for interacting with the pipeline.

Final validated dataset:

```text
159,704 records
15 columns
68,205 distinct claims
11,963 distinct patients
44 diagnosis codes
```

All final validation checks passed successfully.

---

## Author

Developed as a Data Engineering Assessment Project.