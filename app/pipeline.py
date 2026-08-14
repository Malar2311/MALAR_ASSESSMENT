from pathlib import Path
import pandas as pd
from validation import validate_dataset


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)
FINAL_OUTPUT = OUTPUT_DIR / "final_harmonized.csv"


# ---------------------------------------------------------
# INPUT FILES
# ---------------------------------------------------------

SOURCE_A = DATA_DIR / "source_a_claims.csv"
SOURCE_B = DATA_DIR / "source_b_claims.csv"
SOURCE_C = DATA_DIR / "source_c_claims.csv"
DX_DICTIONARY = DATA_DIR / "dx_dictionary.csv"


# ---------------------------------------------------------
# FINAL OUTPUT COLUMNS
# ---------------------------------------------------------

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





# ---------------------------------------------------------
# DIAGNOSIS CODE NORMALIZATION
# ---------------------------------------------------------

def normalize_diagnosis_code(value):
    """
    Convert a diagnosis code into the required standard format.

    Rules:
    - Missing values become None
    - Convert to string
    - Remove leading/trailing whitespace
    - Convert to uppercase
    - Remove decimal points
    """
    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    if not value:
        return None

    return value.replace(".", "")



# ---------------------------------------------------------
# VENDOR A TRANSFORMATION
# ---------------------------------------------------------

def process_source_a():
    """
    Read and standardize Vendor A claims.

    Vendor A stores diagnosis codes in eight separate columns.
    We convert those columns into individual diagnosis rows.
    """

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

    # Convert the eight diagnosis columns into rows
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

    # Remove empty diagnosis values
    df = df.dropna(subset=["DIAGNOSIS_CODE"])

    # Normalize diagnosis codes
    df["DIAGNOSIS_CODE"] = df["DIAGNOSIS_CODE"].apply(
        normalize_diagnosis_code
    )

    # Remove empty codes after normalization
    df = df.dropna(subset=["DIAGNOSIS_CODE"])

    # Normalize gender
    df["GENDER"] = (
        df["patient_gender"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["GENDER"] = df["GENDER"].replace({
        "MALE": "M",
        "FEMALE": "F",
    })

    # Convert service date
    df["SERVICE_DATE"] = pd.to_datetime(
        df["service_from_date"],
        format="%Y%m%d",
        errors="coerce",
    )

    # Build the standardized output
    result = pd.DataFrame({
        "SRC": "A",
        "PATIENT_ID": df["patient_id"],
        "BIRTH_YEAR": df["patient_birth_year"],
        "GENDER": df["GENDER"],
        "ZIP3": df["patient_zip3"],
        "CLAIM_ID": df["claim_id"],
        "SERVICE_DATE": df["SERVICE_DATE"],
        "DIAGNOSIS_CODE": df["DIAGNOSIS_CODE"],
        "DIAGNOSIS_DESC": None,
        "PLACE_OF_SERVICE": df["place_of_svc_cd"],
        "RENDERING_NPI": df["provider_rendering_id"],
        "REFERRING_NPI": df["provider_referring_id"],
        "BILLING_NPI": df["provider_billing_id"],
        "PRIMARY_PLAN_ID": df["primary_plan_id"],
        "BILLED_AMOUNT": df["bill_amt"],
    })

    print(f"Vendor A output rows: {len(result)}")

    return result















    
# ---------------------------------------------------------
# VENDOR B TRANSFORMATION
# ---------------------------------------------------------

def process_source_b():
    """
    Read and standardize Vendor B claims.

    Vendor B already stores one diagnosis code per row,
    so no diagnosis-column unpivoting is required.
    """

    df = pd.read_csv(SOURCE_B)

    print(f"Vendor B input rows: {len(df)}")

    # Normalize diagnosis code
    df["DIAGNOSIS_CODE"] = df["dx_code"].apply(
        normalize_diagnosis_code
    )

    # Normalize gender
    df["GENDER"] = (
        df["gender"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["GENDER"] = df["GENDER"].replace({
        "MALE": "M",
        "FEMALE": "F",
    })

    # Convert service date
    df["SERVICE_DATE"] = pd.to_datetime(
        df["svc_date"],
        dayfirst=True,
        errors="coerce",
    )

    # Build standardized output
    result = pd.DataFrame({
        "SRC": "B",
        "PATIENT_ID": df["member_id"],
        "BIRTH_YEAR": df["birth_yr"],
        "GENDER": df["GENDER"],
        "ZIP3": df["zip3"],
        "CLAIM_ID": df["encounter_id"],
        "SERVICE_DATE": df["SERVICE_DATE"],
        "DIAGNOSIS_CODE": df["DIAGNOSIS_CODE"],
        "DIAGNOSIS_DESC": None,
        "PLACE_OF_SERVICE": df["pos_code"],
        "RENDERING_NPI": df["rendering_npi"],
        "REFERRING_NPI": df["referring_npi"],
        "BILLING_NPI": df["billing_npi"],
        "PRIMARY_PLAN_ID": df["payer_primary"],
        "BILLED_AMOUNT": df["billed_amount"],
    })

    print(f"Vendor B output rows: {len(result)}")

    return result











# ---------------------------------------------------------
# VENDOR C TRANSFORMATION
# ---------------------------------------------------------

def process_source_c():
    """
    Read and standardize Vendor C claims.

    Vendor C:
    - Can contain multiple versions of the same claim.
    - Keeps the highest/latest version.
    - Stores multiple diagnosis codes in one column separated by '|'.
    - Uses different column names from Vendors A and B.
    """

    # -----------------------------------------------------
    # READ SOURCE C
    # -----------------------------------------------------

    df = pd.read_csv(SOURCE_C)

    print(f"Vendor C input rows: {len(df)}")

    # -----------------------------------------------------
    # KEEP LATEST VERSION OF EACH CLAIM
    # -----------------------------------------------------

    df["version"] = pd.to_numeric(
        df["version"],
        errors="coerce"
    )

    df = df.sort_values(
        ["claim_ref", "version"]
    )

    df = df.drop_duplicates(
        subset=["claim_ref"],
        keep="last"
    ).copy()

    print(
        f"Vendor C rows after latest-version selection: "
        f"{len(df)}"
    )

    # -----------------------------------------------------
    # SPLIT MULTIPLE DIAGNOSIS CODES
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

    # Convert each diagnosis code into its own row
    df = df.explode(
        "DIAGNOSIS_CODE"
    ).copy()

    # -----------------------------------------------------
    # NORMALIZE DIAGNOSIS CODE
    # -----------------------------------------------------

    df["DIAGNOSIS_CODE"] = (
        df["DIAGNOSIS_CODE"]
        .apply(normalize_diagnosis_code)
    )

    # Remove empty diagnosis codes
    df = df.dropna(
        subset=["DIAGNOSIS_CODE"]
    ).copy()

    print(
        f"Vendor C rows after diagnosis splitting: "
        f"{len(df)}"
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
        "FEMALE": "F"
    })

    # -----------------------------------------------------
    # CONVERT SERVICE DATE
    # -----------------------------------------------------


    df["SERVICE_DATE"] = pd.to_datetime(
        df["date_of_service"],
        format="%d-%m-%Y",
        errors="coerce"
    )

    print(
        "Vendor C invalid dates:",
        df["SERVICE_DATE"].isna().sum()
    )

    print(
        "Vendor C date range:",
        df["SERVICE_DATE"].min(),
        "to",
        df["SERVICE_DATE"].max()
    )

    # -----------------------------------------------------
    # BUILD STANDARDIZED OUTPUT
    # -----------------------------------------------------

    result = pd.DataFrame({
        "SRC": "C",

        "PATIENT_ID": df["pt_ref"],

        "BIRTH_YEAR": df["yob"],

        "GENDER": df["GENDER"],

        "ZIP3": df["zip_3"],

        "CLAIM_ID": (
            df["claim_ref"].astype(str)
            + "_"
            + df["seq"].astype(str)
        ),
        
        "SERVICE_DATE": df["SERVICE_DATE"],

        "DIAGNOSIS_CODE": df["DIAGNOSIS_CODE"],

        # Description will be added later
        # using dx_dictionary.csv
        "DIAGNOSIS_DESC": None,

        "PLACE_OF_SERVICE": df["service_place"],

        "RENDERING_NPI": df["npi_rendering"],

        "REFERRING_NPI": df["npi_referring"],

        "BILLING_NPI": df["npi_billing"],

        "PRIMARY_PLAN_ID": df["plan_1"],

        "BILLED_AMOUNT": df["amount_billed"],
    })

    print(
        f"Vendor C output rows: "
        f"{len(result)}"
    )

    return result















# ---------------------------------------------------------
# COMBINE ALL SOURCES
# ---------------------------------------------------------

def combine_sources(source_a, source_b, source_c):
    """
    Combine the three standardized vendor datasets.
    """

    combined = pd.concat(
        [source_a, source_b, source_c],
        ignore_index=True
    )

    print(f"Combined rows before cleaning: {len(combined)}")

    return combined






# ---------------------------------------------------------
# GLOBAL CLEANING
# ---------------------------------------------------------

def clean_combined_data(df):
    """
    Apply common cleaning rules to all three vendors.

    Rules:
    1. Remove rows with missing patient IDs.
    2. Keep service dates from 2018-01-01 through 2025-02-28.
    3. Normalize diagnosis codes.
    4. Normalize gender values.
    5. Remove duplicate rows at:
       SRC + CLAIM_ID + DIAGNOSIS_CODE
    6. Keep the required final column order.
    """

    initial_rows = len(df)

    # -----------------------------------------------------
    # 1. REMOVE MISSING PATIENT IDs
    # -----------------------------------------------------

    df["PATIENT_ID"] = (
        df["PATIENT_ID"]
        .astype("string")
        .str.strip()
    )

    missing_patient_mask = (
        df["PATIENT_ID"].isna()
        | (df["PATIENT_ID"] == "")
        | (df["PATIENT_ID"].str.lower() == "nan")
    )

    dropped_missing_patient = missing_patient_mask.sum()

    df = df.loc[
        ~missing_patient_mask
    ].copy()

    print(
        f"Dropped missing patient rows: "
        f"{dropped_missing_patient}"
    )

    # -----------------------------------------------------
    # 2. SERVICE DATE RANGE
    # -----------------------------------------------------

    start_date = pd.Timestamp(
        "2018-01-01"
    )

    end_date = pd.Timestamp(
        "2025-02-28"
    )

    invalid_date_mask = (
        df["SERVICE_DATE"].isna()
        | (df["SERVICE_DATE"] < start_date)
        | (df["SERVICE_DATE"] > end_date)
    )

    dropped_invalid_dates = invalid_date_mask.sum()

    df = df.loc[
        ~invalid_date_mask
    ].copy()

    print(
        f"Dropped invalid/out-of-range dates: "
        f"{dropped_invalid_dates}"
    )

    # -----------------------------------------------------
    # 3. NORMALIZE DIAGNOSIS CODES
    # -----------------------------------------------------

    df["DIAGNOSIS_CODE"] = (
        df["DIAGNOSIS_CODE"]
        .apply(normalize_diagnosis_code)
    )

    df = df.dropna(
        subset=["DIAGNOSIS_CODE"]
    ).copy()

    # -----------------------------------------------------
    # 4. NORMALIZE GENDER
    # -----------------------------------------------------

    df["GENDER"] = (
        df["GENDER"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    df["GENDER"] = df["GENDER"].replace({
        "MALE": "M",
        "FEMALE": "F"
    })

    # -----------------------------------------------------
    # 5. CHECK DUPLICATES
    # -----------------------------------------------------

    duplicate_keys = [
        "SRC",
        "CLAIM_ID",
        "DIAGNOSIS_CODE"
    ]

    # Create the duplicate mask FIRST
    duplicate_check = df.duplicated(
        subset=duplicate_keys,
        keep="first"
    )

    print(
        "\nDuplicate rows by source BEFORE removal:"
    )

    duplicate_by_source = (
        df.loc[duplicate_check]
        .groupby("SRC")
        .size()
    )

    print(duplicate_by_source)

    # Count duplicates
    dropped_duplicates = duplicate_check.sum()

    # Remove duplicates
    df = df.loc[
        ~duplicate_check
    ].copy()

    print(
        f"Dropped duplicate rows: "
        f"{dropped_duplicates}"
    )

    # -----------------------------------------------------
    # 6. FINAL COLUMN ORDER
    # -----------------------------------------------------

    df = df[FINAL_COLUMNS].copy()

    # -----------------------------------------------------
    # FINAL COUNTS
    # -----------------------------------------------------

    print(
        f"Rows after global cleaning: "
        f"{len(df)}"
    )

    print(
        f"Total rows removed: "
        f"{initial_rows - len(df)}"
    )

    # -----------------------------------------------------
    # ROW COUNTS BY SOURCE
    # -----------------------------------------------------

    print(
        "\nRows by source after cleaning:"
    )

    print(
        df.groupby("SRC").size()
    )

    # -----------------------------------------------------
    # DATE RANGE BY SOURCE
    # -----------------------------------------------------

    print(
        "\nDate range by source:"
    )

    print(
        df.groupby("SRC")["SERVICE_DATE"]
        .agg(["min", "max"])
    )

    return df








# ---------------------------------------------------------
# DIAGNOSIS DICTIONARY LOOKUP
# ---------------------------------------------------------

def add_diagnosis_descriptions(df):
    """
    Add diagnosis descriptions using the diagnosis dictionary.
    """

    dictionary = pd.read_csv(DX_DICTIONARY)

    print("\nDiagnosis dictionary rows:", len(dictionary))

    print("Diagnosis dictionary columns:")
    print(dictionary.columns.tolist())

    # -----------------------------------------------------
    # IDENTIFY DICTIONARY COLUMNS
    # -----------------------------------------------------

    code_column = None
    description_column = None

    for column in dictionary.columns:
        column_lower = column.lower().strip()

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
            "Could not identify diagnosis-code column "
            "in dx_dictionary.csv"
        )

    if description_column is None:
        raise ValueError(
            "Could not identify description column "
            "in dx_dictionary.csv"
        )

    print(
        f"Dictionary code column: {code_column}"
    )

    print(
        f"Dictionary description column: "
        f"{description_column}"
    )

    # -----------------------------------------------------
    # NORMALIZE DICTIONARY CODES
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

    # Keep only required columns
    dictionary = dictionary[
        [
            "DIAGNOSIS_CODE",
            "DIAGNOSIS_DESC"
        ]
    ].drop_duplicates(
        subset=["DIAGNOSIS_CODE"]
    )

    # -----------------------------------------------------
    # REMOVE OLD DESCRIPTION COLUMN
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
    # REPORT MISSING DICTIONARY CODES
    # -----------------------------------------------------

    missing_descriptions = (
        df["DIAGNOSIS_DESC"].isna()
    )

    print(
        "Rows without dictionary description:",
        missing_descriptions.sum()
    )

    print(
        "Distinct codes without description:"
    )

    print(
        df.loc[missing_descriptions,
               "DIAGNOSIS_CODE"]
        .drop_duplicates()
        .tolist()
    )

    return df



# ---------------------------------------------------------
# EXPORT FINAL DATASET
# ---------------------------------------------------------

def export_final_dataset(df):
    """
    Export the final validated harmonized dataset as CSV.
    """

    # Ensure exact required column order
    df = df[FINAL_COLUMNS].copy()

    df.to_csv(
        FINAL_OUTPUT,
        index=False,
        encoding="utf-8"
    )

    print("\n" + "=" * 60)
    print("FINAL DATASET EXPORTED")
    print("=" * 60)

    print(f"File: {FINAL_OUTPUT}")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    return FINAL_OUTPUT






# ---------------------------------------------------------
# MAIN PIPELINE EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":

    # -----------------------------------------------------
    # STEP 1: PROCESS SOURCES
    # -----------------------------------------------------

    source_a = process_source_a()

    source_b = process_source_b()

    source_c = process_source_c()

    # -----------------------------------------------------
    # STEP 2: COMBINE SOURCES
    # -----------------------------------------------------

    combined = combine_sources(
        source_a,
        source_b,
        source_c
    )

    # -----------------------------------------------------
    # STEP 3: GLOBAL CLEANING
    # -----------------------------------------------------

    final_data = clean_combined_data(
        combined
    )

    # -----------------------------------------------------
    # STEP 4: ADD DIAGNOSIS DESCRIPTIONS
    # -----------------------------------------------------

    final_data = add_diagnosis_descriptions(
        final_data
    )

    # -----------------------------------------------------
    # STEP 5: VALIDATE
    # -----------------------------------------------------

    validation_passed = validate_dataset(
        final_data
    )

    # -----------------------------------------------------
    # STEP 6: EXPORT ONLY IF VALIDATION PASSES
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

    print("\nFinal shape:")
    print(final_data.shape)

    print("\nFinal columns:")
    print(final_data.columns.tolist())