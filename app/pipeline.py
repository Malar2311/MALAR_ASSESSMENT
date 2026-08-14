from pathlib import Path
import pandas as pd


# =========================================================
# VALIDATION IMPORT
# =========================================================

try:
    from app.validation import validate_dataset
except ModuleNotFoundError:
    from validation import validate_dataset


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)

FINAL_OUTPUT = OUTPUT_DIR / "final_harmonized.csv"


# =========================================================
# INPUT FILES
# =========================================================

SOURCE_A = DATA_DIR / "source_a_claims.csv"
SOURCE_B = DATA_DIR / "source_b_claims.csv"
SOURCE_C = DATA_DIR / "source_c_claims.csv"

DX_DICTIONARY = DATA_DIR / "dx_dictionary.csv"


# =========================================================
# FINAL COLUMN ORDER
# =========================================================

FINAL_COLUMNS = [
    "SRC",
    "PATIENT_ID",
    "BIRTH_YEAR",
    "GENDER",
    "ZIP3",
    "CLAIM_ID",
    "SERVICE_DATE",
    "DIAGNOSIS_CODE",
    "DIAGNOSIS_DESC",
    "PLACE_OF_SERVICE",
    "RENDERING_NPI",
    "REFERRING_NPI",
    "BILLING_NPI",
    "PRIMARY_PLAN_ID",
    "BILLED_AMOUNT",
]


# =========================================================
# CLEANING REPORT
# =========================================================

CLEANING_REPORT = {}


# =========================================================
# DIAGNOSIS CODE NORMALIZATION
# =========================================================

def normalize_diagnosis_code(value):
    """
    Normalize diagnosis codes.

    Rules:
    - Missing values become None
    - Convert to string
    - Remove leading/trailing spaces
    - Convert to uppercase
    - Remove decimal points
    """

    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    if not value:
        return None

    return value.replace(".", "")


# =========================================================
# VENDOR A TRANSFORMATION
# =========================================================

def process_source_a():
    """
    Process Vendor A.

    Vendor A stores diagnosis codes in eight separate
    diagnosis columns. These are converted into rows.
    """

    if not SOURCE_A.exists():
        raise FileNotFoundError(
            f"Vendor A file not found: {SOURCE_A}"
        )

    df = pd.read_csv(SOURCE_A)

    print(f"Vendor A input rows: {len(df)}")

    diagnosis_columns = [
        "diagnosis_code_1",
        "diagnosis_code_2",
        "diagnosis_code_3",
        "diagnosis_code_4",
        "diagnosis_code_5",
        "diagnosis_code_6",
        "diagnosis_code_7",
        "diagnosis_code_8",
    ]

    # -----------------------------------------------------
    # MELT DIAGNOSIS COLUMNS
    # -----------------------------------------------------

    df = df.melt(
        id_vars=[
            "patient_id",
            "claim_id",
            "patient_birth_year",
            "patient_gender",
            "patient_zip3",
            "service_from_date",
            "place_of_svc_cd",
            "provider_rendering_id",
            "provider_referring_id",
            "provider_billing_id",
            "primary_plan_id",
            "bill_amt",
        ],
        value_vars=diagnosis_columns,
        var_name="diagnosis_position",
        value_name="DIAGNOSIS_CODE",
    )

    # -----------------------------------------------------
    # REMOVE EMPTY DIAGNOSIS VALUES
    # -----------------------------------------------------

    df = df.dropna(
        subset=["DIAGNOSIS_CODE"]
    ).copy()

    # -----------------------------------------------------
    # NORMALIZE DIAGNOSIS
    # -----------------------------------------------------

    df["DIAGNOSIS_CODE"] = (
        df["DIAGNOSIS_CODE"]
        .apply(normalize_diagnosis_code)
    )

    df = df.dropna(
        subset=["DIAGNOSIS_CODE"]
    ).copy()

    # -----------------------------------------------------
    # NORMALIZE GENDER
    # -----------------------------------------------------

    df["GENDER"] = (
        df["patient_gender"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    df["GENDER"] = df["GENDER"].replace({
        "MALE": "M",
        "FEMALE": "F",
    })

    # -----------------------------------------------------
    # SERVICE DATE
    # -----------------------------------------------------

    df["SERVICE_DATE"] = pd.to_datetime(
        df["service_from_date"],
        format="%Y%m%d",
        errors="coerce",
    )

    # -----------------------------------------------------
    # STANDARDIZED OUTPUT
    # -----------------------------------------------------

    result = pd.DataFrame({
        "SRC": "A",

        "PATIENT_ID":
            df["patient_id"],

        "BIRTH_YEAR":
            df["patient_birth_year"],

        "GENDER":
            df["GENDER"],

        "ZIP3":
            df["patient_zip3"],

        "CLAIM_ID":
            df["claim_id"],

        "SERVICE_DATE":
            df["SERVICE_DATE"],

        "DIAGNOSIS_CODE":
            df["DIAGNOSIS_CODE"],

        "DIAGNOSIS_DESC":
            None,

        "PLACE_OF_SERVICE":
            df["place_of_svc_cd"],

        "RENDERING_NPI":
            df["provider_rendering_id"],

        "REFERRING_NPI":
            df["provider_referring_id"],

        "BILLING_NPI":
            df["provider_billing_id"],

        "PRIMARY_PLAN_ID":
            df["primary_plan_id"],

        "BILLED_AMOUNT":
            df["bill_amt"],
    })

    print(
        f"Vendor A output rows: {len(result)}"
    )

    return result


# =========================================================
# VENDOR B TRANSFORMATION
# =========================================================

def process_source_b():
    """
    Process Vendor B.

    Vendor B already has one diagnosis code per row.
    """

    if not SOURCE_B.exists():
        raise FileNotFoundError(
            f"Vendor B file not found: {SOURCE_B}"
        )

    df = pd.read_csv(SOURCE_B)

    print(
        f"Vendor B input rows: {len(df)}"
    )

    # -----------------------------------------------------
    # NORMALIZE DIAGNOSIS
    # -----------------------------------------------------

    df["DIAGNOSIS_CODE"] = (
        df["dx_code"]
        .apply(normalize_diagnosis_code)
    )

    # -----------------------------------------------------
    # NORMALIZE GENDER
    # -----------------------------------------------------

    df["GENDER"] = (
        df["gender"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    df["GENDER"] = df["GENDER"].replace({
        "MALE": "M",
        "FEMALE": "F",
    })

    # -----------------------------------------------------
    # SERVICE DATE
    # -----------------------------------------------------

    df["SERVICE_DATE"] = pd.to_datetime(
        df["svc_date"],
        dayfirst=True,
        errors="coerce",
    )

    # -----------------------------------------------------
    # STANDARDIZED OUTPUT
    # -----------------------------------------------------

    result = pd.DataFrame({
        "SRC": "B",

        "PATIENT_ID":
            df["member_id"],

        "BIRTH_YEAR":
            df["birth_yr"],

        "GENDER":
            df["GENDER"],

        "ZIP3":
            df["zip3"],

        "CLAIM_ID":
            df["encounter_id"],

        "SERVICE_DATE":
            df["SERVICE_DATE"],

        "DIAGNOSIS_CODE":
            df["DIAGNOSIS_CODE"],

        "DIAGNOSIS_DESC":
            None,

        "PLACE_OF_SERVICE":
            df["pos_code"],

        "RENDERING_NPI":
            df["rendering_npi"],

        "REFERRING_NPI":
            df["referring_npi"],

        "BILLING_NPI":
            df["billing_npi"],

        "PRIMARY_PLAN_ID":
            df["payer_primary"],

        "BILLED_AMOUNT":
            df["billed_amount"],
    })

    print(
        f"Vendor B output rows: {len(result)}"
    )

    return result


# =========================================================
# VENDOR C TRANSFORMATION
# =========================================================

def process_source_c():
    """
    Process Vendor C.

    Vendor C:
    - Contains multiple versions of claims.
    - Latest version is retained.
    - Multiple diagnosis codes are separated by '|'.
    - Diagnosis codes are exploded into separate rows.
    """

    if not SOURCE_C.exists():
        raise FileNotFoundError(
            f"Vendor C file not found: {SOURCE_C}"
        )

    df = pd.read_csv(SOURCE_C)

    print(
        f"Vendor C input rows: {len(df)}"
    )

    # -----------------------------------------------------
    # VERSION
    # -----------------------------------------------------

    df["version"] = pd.to_numeric(
        df["version"],
        errors="coerce"
    )

    # -----------------------------------------------------
    # KEEP LATEST VERSION
    # -----------------------------------------------------

    df = df.sort_values(
        ["claim_ref", "version"]
    )

    df = df.drop_duplicates(
        subset=["claim_ref"],
        keep="last"
    ).copy()

    print(
        "Vendor C rows after latest-version "
        f"selection: {len(df)}"
    )

    # -----------------------------------------------------
    # DIAGNOSIS SPLITTING
    # -----------------------------------------------------

    df["diagnosis_codes"] = (
        df["diagnosis_codes"]
        .fillna("")
        .astype(str)
    )

    df["DIAGNOSIS_CODE"] = (
        df["diagnosis_codes"]
        .str.split("|")
    )

    df = df.explode(
        "DIAGNOSIS_CODE"
    ).copy()

    # -----------------------------------------------------
    # NORMALIZE DIAGNOSIS
    # -----------------------------------------------------

    df["DIAGNOSIS_CODE"] = (
        df["DIAGNOSIS_CODE"]
        .apply(normalize_diagnosis_code)
    )

    df = df.dropna(
        subset=["DIAGNOSIS_CODE"]
    ).copy()

    print(
        "Vendor C rows after diagnosis "
        f"splitting: {len(df)}"
    )

    # -----------------------------------------------------
    # NORMALIZE GENDER
    # -----------------------------------------------------

    df["GENDER"] = (
        df["sex"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    df["GENDER"] = df["GENDER"].replace({
        "MALE": "M",
        "FEMALE": "F",
    })

    # -----------------------------------------------------
    # SERVICE DATE
    # -----------------------------------------------------

    df["SERVICE_DATE"] = pd.to_datetime(
        df["date_of_service"],
        format="%d-%m-%Y",
        errors="coerce"
    )

    print(
        "Vendor C invalid dates:",
        int(df["SERVICE_DATE"].isna().sum())
    )

    print(
        "Vendor C date range:",
        df["SERVICE_DATE"].min(),
        "to",
        df["SERVICE_DATE"].max()
    )

    # -----------------------------------------------------
    # STANDARDIZED OUTPUT
    # -----------------------------------------------------

    result = pd.DataFrame({

        "SRC":
            "C",

        "PATIENT_ID":
            df["pt_ref"],

        "BIRTH_YEAR":
            df["yob"],

        "GENDER":
            df["GENDER"],

        "ZIP3":
            df["zip_3"],

        "CLAIM_ID":
            (
                df["claim_ref"].astype(str)
                + "_"
                + df["seq"].astype(str)
            ),

        "SERVICE_DATE":
            df["SERVICE_DATE"],

        "DIAGNOSIS_CODE":
            df["DIAGNOSIS_CODE"],

        "DIAGNOSIS_DESC":
            None,

        "PLACE_OF_SERVICE":
            df["service_place"],

        "RENDERING_NPI":
            df["npi_rendering"],

        "REFERRING_NPI":
            df["npi_referring"],

        "BILLING_NPI":
            df["npi_billing"],

        "PRIMARY_PLAN_ID":
            df["plan_1"],

        "BILLED_AMOUNT":
            df["amount_billed"],
    })

    print(
        f"Vendor C output rows: {len(result)}"
    )

    return result


# =========================================================
# COMBINE ALL SOURCES
# =========================================================

def combine_sources(
    source_a,
    source_b,
    source_c
):
    """
    Combine all standardized vendor datasets.
    """

    combined = pd.concat(
        [
            source_a,
            source_b,
            source_c
        ],
        ignore_index=True
    )

    print(
        f"Combined rows before cleaning: "
        f"{len(combined)}"
    )

    return combined


# =========================================================
# GLOBAL CLEANING
# =========================================================

def clean_combined_data(df):
    """
    Apply common cleaning rules.

    Rules:
    1. Remove missing patient IDs.
    2. Keep service dates between
       2018-01-01 and 2025-02-28.
    3. Normalize diagnosis codes.
    4. Normalize gender.
    5. Remove duplicate
       SRC + CLAIM_ID + DIAGNOSIS_CODE.
    6. Preserve required final columns.
    """

    global CLEANING_REPORT

    initial_rows = len(df)

    # -----------------------------------------------------
    # 1. PATIENT ID
    # -----------------------------------------------------

    df["PATIENT_ID"] = (
        df["PATIENT_ID"]
        .astype("string")
        .str.strip()
    )

    missing_patient_mask = (
        df["PATIENT_ID"].isna()
        |
        (df["PATIENT_ID"] == "")
        |
        (
            df["PATIENT_ID"]
            .str.lower()
            == "nan"
        )
    )

    dropped_missing_patient = int(
        missing_patient_mask.sum()
    )

    df = df.loc[
        ~missing_patient_mask
    ].copy()

    print(
        "Dropped missing patient rows:",
        dropped_missing_patient
    )

    # -----------------------------------------------------
    # 2. SERVICE DATE
    # -----------------------------------------------------

    start_date = pd.Timestamp(
        "2018-01-01"
    )

    end_date = pd.Timestamp(
        "2025-02-28"
    )

    # Make sure dates are datetime
    df["SERVICE_DATE"] = pd.to_datetime(
        df["SERVICE_DATE"],
        errors="coerce"
    )

    invalid_date_mask = (
        df["SERVICE_DATE"].isna()
        |
        (df["SERVICE_DATE"] < start_date)
        |
        (df["SERVICE_DATE"] > end_date)
    )

    dropped_invalid_dates = int(
        invalid_date_mask.sum()
    )

    df = df.loc[
        ~invalid_date_mask
    ].copy()

    print(
        "Dropped invalid/out-of-range dates:",
        dropped_invalid_dates
    )

    # -----------------------------------------------------
    # 3. DIAGNOSIS CODE
    # -----------------------------------------------------

    df["DIAGNOSIS_CODE"] = (
        df["DIAGNOSIS_CODE"]
        .apply(normalize_diagnosis_code)
    )

    missing_diagnosis_codes = int(
        df["DIAGNOSIS_CODE"]
        .isna()
        .sum()
    )

    df = df.dropna(
        subset=["DIAGNOSIS_CODE"]
    ).copy()

    # -----------------------------------------------------
    # 4. GENDER
    # -----------------------------------------------------

    df["GENDER"] = (
        df["GENDER"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    df["GENDER"] = df["GENDER"].replace({
        "MALE": "M",
        "FEMALE": "F",
    })

    # -----------------------------------------------------
    # 5. DUPLICATES
    # -----------------------------------------------------

    duplicate_keys = [
        "SRC",
        "CLAIM_ID",
        "DIAGNOSIS_CODE"
    ]

    duplicate_check = df.duplicated(
        subset=duplicate_keys,
        keep="first"
    )

    print(
        "\nDuplicate rows by source "
        "BEFORE removal:"
    )

    duplicate_by_source = (
        df.loc[duplicate_check]
        .groupby("SRC")
        .size()
    )

    print(duplicate_by_source)

    dropped_duplicates = int(
        duplicate_check.sum()
    )

    df = df.loc[
        ~duplicate_check
    ].copy()

    print(
        "Dropped duplicate rows:",
        dropped_duplicates
    )

    # -----------------------------------------------------
    # 6. FINAL COLUMN ORDER
    # -----------------------------------------------------

    df = df[FINAL_COLUMNS].copy()

    # -----------------------------------------------------
    # CLEANING REPORT
    # -----------------------------------------------------

    final_rows = len(df)

    total_removed = (
        initial_rows - final_rows
    )

    CLEANING_REPORT = {

        "initial_rows":
            int(initial_rows),

        "dropped_missing_patient_ids":
            dropped_missing_patient,

        "dropped_invalid_dates":
            dropped_invalid_dates,

        "dropped_invalid_diagnosis_codes":
            missing_diagnosis_codes,

        "dropped_duplicate_rows":
            dropped_duplicates,

        "final_rows":
            int(final_rows),

        "total_rows_removed":
            int(total_removed),

        "date_range": {
            "start":
                "2018-01-01",

            "end":
                "2025-02-28"
        },

        "duplicate_rows_by_source": {
            str(key): int(value)
            for key, value
            in duplicate_by_source
            .to_dict()
            .items()
        },

        "final_rows_by_source": {
            str(key): int(value)
            for key, value
            in df.groupby("SRC")
            .size()
            .to_dict()
            .items()
        }
    }

    # -----------------------------------------------------
    # FINAL COUNTS
    # -----------------------------------------------------

    print(
        "Rows after global cleaning:",
        final_rows
    )

    print(
        "Total rows removed:",
        total_removed
    )

    print(
        "\nRows by source after cleaning:"
    )

    print(
        df.groupby("SRC").size()
    )

    print(
        "\nDate range by source:"
    )

    print(
        df.groupby("SRC")["SERVICE_DATE"]
        .agg(["min", "max"])
    )

    return df


# =========================================================
# DIAGNOSIS DICTIONARY LOOKUP
# =========================================================

def add_diagnosis_descriptions(df):
    """
    Add diagnosis descriptions using dx_dictionary.csv.
    """

    if not DX_DICTIONARY.exists():
        raise FileNotFoundError(
            f"Diagnosis dictionary not found: "
            f"{DX_DICTIONARY}"
        )

    dictionary = pd.read_csv(
        DX_DICTIONARY
    )

    print(
        "\nDiagnosis dictionary rows:",
        len(dictionary)
    )

    print(
        "Diagnosis dictionary columns:"
    )

    print(
        dictionary.columns.tolist()
    )

    # -----------------------------------------------------
    # IDENTIFY COLUMNS
    # -----------------------------------------------------

    code_column = None
    description_column = None

    for column in dictionary.columns:

        column_lower = (
            column.lower()
            .strip()
        )

        if column_lower in [
            "diagnosis_code",
            "dx_code",
            "code",
            "icd_code",
            "dx"
        ]:
            code_column = column

        if column_lower in [
            "diagnosis_desc",
            "diagnosis_description",
            "dx_description",
            "desc",
            "diagnosis"
        ]:
            description_column = column

    if code_column is None:

        raise ValueError(
            "Could not identify diagnosis-code "
            "column in dx_dictionary.csv"
        )

    if description_column is None:

        raise ValueError(
            "Could not identify description "
            "column in dx_dictionary.csv"
        )

    print(
        "Dictionary code column:",
        code_column
    )

    print(
        "Dictionary description column:",
        description_column
    )

    # -----------------------------------------------------
    # NORMALIZE DICTIONARY
    # -----------------------------------------------------

    dictionary["DIAGNOSIS_CODE"] = (
        dictionary[code_column]
        .apply(normalize_diagnosis_code)
    )

    dictionary["DIAGNOSIS_DESC"] = (
        dictionary[description_column]
        .astype("string")
        .str.strip()
    )

    dictionary = dictionary[
        [
            "DIAGNOSIS_CODE",
            "DIAGNOSIS_DESC"
        ]
    ].drop_duplicates(
        subset=["DIAGNOSIS_CODE"]
    )

    # -----------------------------------------------------
    # REMOVE OLD DESCRIPTION
    # -----------------------------------------------------

    if "DIAGNOSIS_DESC" in df.columns:

        df = df.drop(
            columns=["DIAGNOSIS_DESC"]
        )

    # -----------------------------------------------------
    # LEFT JOIN
    # -----------------------------------------------------

    df = df.merge(
        dictionary,
        on="DIAGNOSIS_CODE",
        how="left"
    )

    # -----------------------------------------------------
    # MISSING DESCRIPTIONS
    # -----------------------------------------------------

    missing_descriptions = (
        df["DIAGNOSIS_DESC"]
        .isna()
    )

    print(
        "Rows without dictionary description:",
        int(missing_descriptions.sum())
    )

    print(
        "Distinct codes without description:"
    )

    print(
        df.loc[
            missing_descriptions,
            "DIAGNOSIS_CODE"
        ]
        .drop_duplicates()
        .tolist()
    )

    # -----------------------------------------------------
    # FINAL COLUMN ORDER
    # -----------------------------------------------------

    df = df[FINAL_COLUMNS].copy()

    return df


# =========================================================
# EXPORT FINAL DATASET
# =========================================================

def export_final_dataset(df):
    """
    Export final harmonized dataset as CSV.
    """

    df = df[FINAL_COLUMNS].copy()

    df.to_csv(
        FINAL_OUTPUT,
        index=False,
        encoding="utf-8"
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "FINAL DATASET EXPORTED"
    )

    print(
        "=" * 60
    )

    print(
        f"File: {FINAL_OUTPUT}"
    )

    print(
        f"Rows: {len(df)}"
    )

    print(
        f"Columns: {len(df.columns)}"
    )

    print(
        "\nFinal shape:"
    )

    print(
        df.shape
    )

    print(
        "\nFinal columns:"
    )

    print(
        df.columns.tolist()
    )

    return FINAL_OUTPUT


# =========================================================
# MAIN PIPELINE EXECUTION
# =========================================================

if __name__ == "__main__":

    print(
        "\n" + "=" * 60
    )

    print(
        "MULTI-SOURCE DATA HARMONIZATION PIPELINE"
    )

    print(
        "=" * 60
    )

    # -----------------------------------------------------
    # STEP 1 — PROCESS VENDORS
    # -----------------------------------------------------

    source_a = process_source_a()

    source_b = process_source_b()

    source_c = process_source_c()

    # -----------------------------------------------------
    # STEP 2 — COMBINE
    # -----------------------------------------------------

    combined = combine_sources(
        source_a,
        source_b,
        source_c
    )

    # -----------------------------------------------------
    # STEP 3 — CLEAN
    # -----------------------------------------------------

    final_data = clean_combined_data(
        combined
    )

    # -----------------------------------------------------
    # STEP 4 — DIAGNOSIS DICTIONARY
    # -----------------------------------------------------

    final_data = add_diagnosis_descriptions(
        final_data
    )

    # -----------------------------------------------------
    # STEP 5 — VALIDATION
    # -----------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "RUNNING VALIDATION"
    )

    print(
        "=" * 60
    )

    validation_passed = bool(
        validate_dataset(final_data)
    )

    # -----------------------------------------------------
    # STEP 6 — EXPORT
    # -----------------------------------------------------

    if validation_passed:

        export_final_dataset(
            final_data
        )

    else:

        print(
            "\nFinal dataset was NOT exported "
            "because validation failed."
        )

    # -----------------------------------------------------
    # FINAL INFORMATION
    # -----------------------------------------------------

    print(
        "\nPipeline execution completed."
    )