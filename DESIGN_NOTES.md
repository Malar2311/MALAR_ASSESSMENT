# Design Notes

## Multi-Source Healthcare Claims Data Harmonization Pipeline

This document explains what I built, the problems I found in the data, why I made the main design choices, what went wrong during development, what I was unsure about, and what I would improve in a larger production system.

---

# 1. What I Built

I built a data harmonization pipeline that takes claims data from three different vendors and produces one standardized dataset.

The pipeline has separate processing steps for each vendor because the three input files are structured differently.

The overall flow is:

```text
Vendor A
   |
   v
Vendor A Processing
   |
Vendor B
   |
   v
Vendor B Processing
   |
Vendor C
   |
   v
Vendor C Processing
   |
   v
Combine Sources
   |
   v
Global Cleaning
   |
   v
Diagnosis Dictionary Lookup
   |
   v
Validation
   |
   v
Final CSV
```

I also built a small FastAPI backend and a web dashboard around the pipeline.

The API allows the user to:

- Run the pipeline.
- View the pipeline stages.
- Check validation results.
- View the final dataset summary.
- Download the final CSV.

The dashboard shows the results returned by the API.

---

# 2. What Problem It Solves

The main problem is that the three vendors provide the same general type of healthcare claims information but use different structures.

The differences I had to handle included:

- Different column names.
- Different date formats.
- Different diagnosis-code formats.
- Different ways of storing multiple diagnosis codes.
- Multiple versions of records in Vendor C.
- Missing patient identifiers.
- Invalid or out-of-range service dates.
- Duplicate records.

Simply concatenating the three CSV files would not produce a reliable dataset.

For example, Vendor A stores diagnosis codes in eight separate columns.

Vendor C stores several diagnosis codes in one field separated by `|`.

Vendor B already has one diagnosis code per row.

Therefore, the data had to be transformed before the sources could be combined.

The final pipeline creates one consistent record structure where the required grain is:

```text
SRC + CLAIM_ID + DIAGNOSIS_CODE
```

This makes the final dataset easier to validate and use for further analysis.

---

# 3. Why I Did It This Way

## Separate Vendor Processing

I decided to process each vendor separately before combining them.

I did this because the differences between the sources are vendor-specific.

For example:

- Vendor A needs diagnosis columns to be unpivoted.
- Vendor B does not need diagnosis splitting.
- Vendor C needs version selection and diagnosis splitting.

If I tried to handle all of these differences in one large cleaning function, the code would be harder to understand and maintain.

So I used:

```text
process_source_a()
process_source_b()
process_source_c()
```

Each function converts its source into the same common schema.

---

## Vendor A Diagnosis Transformation

Vendor A has multiple diagnosis columns.

I used `pandas.melt()` to convert the diagnosis columns into rows.

I chose this because the final dataset needs one row per diagnosis at the required grain.

For example:

```text
Claim C001
Diagnosis 1 = E119
Diagnosis 2 = I10
Diagnosis 3 = J189
```

becomes:

```text
C001 E119
C001 I10
C001 J189
```

This also makes Vendor A consistent with Vendor B and Vendor C after their own transformations.

---

## Vendor C Latest Version

Vendor C can contain multiple versions of the same claim.

I used the version field to select the latest version.

The process is:

```text
Sort by claim reference
        |
        v
Sort by version
        |
        v
Keep the latest version
```

I chose this because keeping all versions would result in older and newer versions of the same claim being treated as separate records.

The assessment specifically indicates that Vendor C contains multiple versions, so I treated the highest version as the applicable record.

---

## Vendor C Diagnosis Splitting

Vendor C stores multiple diagnosis codes in one field separated by `|`.

I split this field and used `explode()`.

For example:

```text
E119|I10|J189
```

becomes:

```text
E119
I10
J189
```

This was necessary to maintain the required one-row-per-diagnosis structure.

---

## Diagnosis Normalization

I created one reusable function:

```text
normalize_diagnosis_code()
```

It:

1. Handles missing values.
2. Converts the value to a string.
3. Removes surrounding whitespace.
4. Converts the value to uppercase.
5. Removes decimal points.

For example:

```text
 e11.9
```

becomes:

```text
E119
```

I used the same normalization logic for both the claims data and the diagnosis dictionary.

This avoids a situation where a code in the claims data and the same code in the dictionary have different formatting.

---

## Global Cleaning After Combination

I chose to perform common cleaning after vendor-specific transformations.

The reason is that some problems can only be identified reliably after all vendors use the same schema.

The common cleaning steps are:

```text
Remove missing patient IDs
        |
        v
Remove invalid/out-of-range dates
        |
        v
Normalize diagnosis codes
        |
        v
Normalize gender
        |
        v
Remove duplicates
```

This separates vendor-specific logic from rules that apply to every vendor.

---

## Order of Cleaning

I deliberately perform vendor transformations first and common cleaning afterward.

This is important because the row structure changes during ingestion.

For example, Vendor A produces additional rows when multiple diagnosis columns are converted into individual diagnosis rows.

Vendor C also produces additional rows when multiple diagnosis codes are exploded.

Therefore, checking duplicates before those transformations could give the wrong result.

After all vendors have been converted into the common structure, I can apply the common duplicate rule consistently.

---

## Missing Patient IDs

I remove records with missing patient identifiers.

I also handle empty strings and string representations of missing values.

I chose to remove these rows because the assessment explicitly requires rows without a patient identifier to be dropped.

Keeping them would also make patient-level analysis unreliable.

---

## Service Date Filtering

I convert service dates into proper date values and then apply the required date range:

```text
2018-01-01 to 2025-02-28
```

I chose to convert the dates before filtering because comparing different vendor date strings directly could produce incorrect results.

Using actual date values makes the comparison consistent.

---

## Duplicate Definition

I used:

```text
SRC
CLAIM_ID
DIAGNOSIS_CODE
```

as the duplicate key.

I chose this because the assessment defines the required grain as one row per source, claim, and diagnosis code.

Two rows with the same values at this grain represent duplicates for the purpose of the final output.

---

## Diagnosis Dictionary

I used a left join when adding diagnosis descriptions.

I chose a left join because the claim record should not disappear just because its diagnosis code is missing from the dictionary.

If a code is not present in the dictionary, I leave:

```text
DIAGNOSIS_DESC
```

empty.

I did not invent descriptions because assigning an incorrect diagnosis description would be worse than leaving it blank.

---

## Validation

I kept validation as a separate step instead of mixing it into the cleaning logic.

This makes it easier to understand the difference between:

```text
Cleaning
```

and:

```text
Checking whether the final result is correct
```

The validation checks include the required acceptance conditions.

The final successful run produced:

```text
Total rows: 159704
Distinct claims: 68205
Distinct patients: 11963
Distinct diagnosis codes: 44
```

The P00042 checks also passed:

```text
P00042 rows: 7
P00042 diagnosis codes: 7
```

The remaining quality checks also passed:

```text
Invalid diagnosis codes: 0
Missing patient IDs: 0
Invalid service dates: 0
Duplicate rows: 0
```

---

# 4. What Went Wrong Along the Way

The first version of the pipeline did not pass all the checks immediately.

There were several issues during development.

## API Validation Error

One of the API validation responses initially produced a FastAPI serialization error involving a NumPy boolean value.

The problem was that Pandas operations can return NumPy data types such as:

```text
numpy.bool_
```

FastAPI expects values that can be safely converted into JSON.

I fixed this by explicitly converting values to normal Python types.

For example:

```python
bool(...)
```

for boolean values and:

```python
int(...)
```

for numeric values.

After this change, the validation endpoint returned valid JSON.

---

## PowerShell File Comparison

I also tried to compare two CSV files using:

```text
fc /b output\final_harmonized_run1.csv output\final_harmonized.csv
```

in PowerShell.

PowerShell interpreted `fc` differently from the Windows command-line file comparison utility.

This caused a PowerShell parameter error.

This was a tooling issue rather than a pipeline problem.

It reminded me that commands can behave differently depending on the shell being used.

---

## Cleaning Report Issue

During dashboard development, I had an error caused by a cleaning-report function requiring a `run_id` argument.

The error was:

```text
get_cleaning_report() missing 1 required positional argument: 'run_id'
```

The issue came from having the API function and the cleaning-report data flow coupled incorrectly.

I corrected the pipeline/API interaction so that the cleaning information is associated with the pipeline run correctly.

---

## Dashboard Initially Showed Blank Values

The dashboard initially displayed `-` instead of the actual values.

The reason was that the frontend was not yet correctly retrieving all the information from the API.

I changed the dashboard to retrieve values from the backend instead of manually putting the dataset values into the HTML.

This is important because the dashboard should show the result of the current pipeline run rather than fixed numbers.

---

## Validation Endpoint

I also tested the validation endpoint separately after running the pipeline.

The successful validation response returned:

```text
all_checks_passed: true
```

This confirmed that the final dataset met the required acceptance checks.

---

# 5. What I Was Not Sure About

There were a few areas where I had to make assumptions based on the data and assessment instructions.

## Vendor C Version

The main assumption was that the highest version represents the latest applicable version.

I used the version field and kept the highest version for each claim reference.

If the vendor had provided a separate field such as:

```text
is_current
```

or an explicit effective timestamp, I would prefer to use that instead.

---

## Missing Diagnosis Descriptions

Not every diagnosis code necessarily appears in the dictionary.

I decided to keep the claim record and leave the description empty if no dictionary match exists.

I chose this because removing the claim would change the source data unnecessarily.

---

## Duplicate Records

I interpreted the assessment's grain as:

```text
SRC + CLAIM_ID + DIAGNOSIS_CODE
```

and used that as the duplicate definition.

If the business rules had defined duplicates differently, I would change this key.

---

## Claim Identifier Construction for Vendor C

Vendor C has both:

```text
claim_ref
```

and:

```text
seq
```

I combined them to create the standardized claim ID:

```text
claim_ref + "_" + seq
```

This preserves the sequence information and helps distinguish records that otherwise share the same claim reference.

If the vendor had provided a clearly defined unique claim identifier, I would use that instead.

---

# 6. What I Would Do Differently

The current solution works for the supplied assessment data, but I would make several improvements for a production system.

## Automated Tests

I would add unit tests for:

- Diagnosis normalization.
- Date conversion.
- Vendor A transformation.
- Vendor B transformation.
- Vendor C version selection.
- Diagnosis splitting.
- Duplicate removal.
- Dictionary mapping.
- Validation rules.

This would make changes safer.

---

## Better Logging

The current pipeline prints useful information to the console.

For production, I would use Python's logging framework.

I would record:

```text
Run ID
Stage
Input rows
Output rows
Dropped rows
Reason for drops
Execution time
Errors
```

This would make troubleshooting easier.

---

## Detailed Row-Level Error Tracking

Instead of only counting removed records, I would store a data-quality report showing why each rejected row was removed.

For example:

```text
Row ID | Reason
-------|-------------------------
001    | Missing patient ID
002    | Invalid service date
003    | Invalid diagnosis code
004    | Duplicate record
```

This would make the pipeline easier to audit.

---

## Configuration

The date range and input/output paths are currently defined in the code.

In a production system, I would move configurable values into a configuration file or environment variables.

For example:

```text
START_DATE
END_DATE
INPUT_DIRECTORY
OUTPUT_DIRECTORY
```

This would avoid changing the Python code when configuration changes.

---

## Larger Data Volumes

The current implementation uses Pandas and CSV files.

For a dataset hundreds of times larger, I would consider:

- Database storage.
- Parquet files.
- Chunked processing.
- Distributed processing.
- Cloud object storage.

This would reduce memory usage and improve scalability.

---

## API Run Storage

The current API stores run information in memory.

That means the run information can be lost when the FastAPI server restarts.

For a production system, I would store run metadata in a database.

---

## Dashboard Improvements

The current dashboard focuses on the requirements of the assessment.

For a production dashboard, I would add:

- Historical runs.
- Processing time.
- Detailed cleaning reasons.
- Error messages.
- Data-quality charts.
- Downloadable validation reports.
- Search and filtering.

---

# Final Result

The final successful run produced:

```text
Total rows               : 159704
Distinct claims          : 68205
Distinct patients        : 11963
Distinct diagnosis codes : 44

Vendor A                 : 67531
Vendor B                 : 52819
Vendor C                 : 39354

P00042 rows              : 7
P00042 diagnosis codes   : 7

Missing patient IDs      : 0
Invalid dates            : 0
Duplicate rows           : 0
Invalid diagnosis codes  : 0

Overall validation       : PASS
```

The final output is:

```text
output/final_harmonized.csv
```

---

# Summary

The main design decision was to separate vendor-specific transformations from common cleaning rules.

This made the pipeline easier to understand because each vendor's unusual structure is handled before the data reaches the common cleaning stage.

The final pipeline is:

```text
Read
  |
Transform
  |
Standardize
  |
Combine
  |
Clean
  |
Enrich
  |
Validate
  |
Export
```

The result is one consistent healthcare claims dataset that satisfies the required validation checks.

I also built a FastAPI API and dashboard so that the pipeline can be run and inspected without manually running every processing step.