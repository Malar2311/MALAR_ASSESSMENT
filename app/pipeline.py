from pathlib import Path
import hashlib
import pandas as pd

# ---------------------------------------------------------
# IMPORT VALIDATION
# ---------------------------------------------------------

try:
    from app.validation import validate_dataset
except ModuleNotFoundError:
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
# FINAL COLUMNS
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
# PIPELINE REPORT
# ---------------------------------------------------------

PIPELINE_REPORT = {
    "ingestion": {},
    "combination": {},
    "cleaning": {},
    "dictionary": {},
    "validation": {},
    "export": {},
}


# ---------------------------------------------------------
# CLEANING REPORT
# ---------------------------------------------------------

CLEANING_REPORT = {}


# ---------------------------------------------------------
# NORMALIZE DIAGNOSIS CODE
# ---------------------------------------------------------

def normalize_diagnosis_code(value):

    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    if not value:
        return None

    return value.replace(".", "")


# =========================================================
# VENDOR A
# =========================================================

def process_source_a():

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

    df = df.dropna(
        subset=["DIAGNOSIS_CODE"]
    )

    df["DIAGNOSIS_CODE"] = (
        df["DIAGNOSIS_CODE"]
        .apply(normalize_diagnosis_code)
    )

    df = df.dropna(
        subset=["DIAGNOSIS_CODE"]
    )

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

    df["SERVICE_DATE"] = pd.to_datetime(
        df["service_from_date"],
        format="%Y%m%d",
        errors="coerce",
    )

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
# VENDOR B
# =========================================================

def process_source_b():

    df = pd.read_csv(SOURCE_B)

    print(
        f"Vendor B input rows: {len(df)}"
    )

    df["DIAGNOSIS_CODE"] = (
        df["dx_code"]
        .apply(normalize_diagnosis_code)
    )

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

    df["SERVICE_DATE"] = pd.to_datetime(
        df["svc_date"],
        dayfirst=True,
        errors="coerce",
    )

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
# VENDOR C
# =========================================================

def process_source_c():

    df = pd.read_csv(SOURCE_C)

    print(
        f"Vendor C input rows: {len(df)}"
    )

    # -----------------------------------------------------
    # KEEP LATEST VERSION
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
        "Vendor C rows after latest-version selection:",
        len(df)
    )

    # -----------------------------------------------------
    # SPLIT DIAGNOSIS CODES
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

    df["DIAGNOSIS_CODE"] = (
        df["DIAGNOSIS_CODE"]
        .apply(normalize_diagnosis_code)
    )

    df = df.dropna(
        subset=["DIAGNOSIS_CODE"]
    ).copy()

    # -----------------------------------------------------
    # GENDER
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

    # -----------------------------------------------------
    # STANDARDIZED DATASET
    # -----------------------------------------------------

    result = pd.DataFrame({

        "SRC": "C",

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
# COMBINE SOURCES
# =========================================================

def combine_sources(
    source_a,
    source_b,
    source_c
):

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

    global CLEANING_REPORT

    initial_rows = len(df)

    # -----------------------------------------------------
    # MISSING PATIENT IDS
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

    # -----------------------------------------------------
    # DATE RANGE
    # -----------------------------------------------------

    start_date = pd.Timestamp(
        "2018-01-01"
    )

    end_date = pd.Timestamp(
        "2025-02-28"
    )

    df["SERVICE_DATE"] = pd.to_datetime(
        df["SERVICE_DATE"],
        errors="coerce"
    )

    invalid_date_mask = (
        df["SERVICE_DATE"].isna()
        |
        (
            df["SERVICE_DATE"]
            < start_date
        )
        |
        (
            df["SERVICE_DATE"]
            > end_date
        )
    )

    dropped_invalid_dates = int(
        invalid_date_mask.sum()
    )

    df = df.loc[
        ~invalid_date_mask
    ].copy()

    # -----------------------------------------------------
    # DIAGNOSIS
    # -----------------------------------------------------

    df["DIAGNOSIS_CODE"] = (
        df["DIAGNOSIS_CODE"]
        .apply(normalize_diagnosis_code)
    )

    invalid_diagnosis_mask = (
        df["DIAGNOSIS_CODE"].isna()
    )

    dropped_invalid_diagnosis = int(
        invalid_diagnosis_mask.sum()
    )

    df = df.loc[
        ~invalid_diagnosis_mask
    ].copy()

    # -----------------------------------------------------
    # GENDER
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
    # DUPLICATES
    # -----------------------------------------------------

    duplicate_keys = [
        "SRC",
        "CLAIM_ID",
        "DIAGNOSIS_CODE"
    ]

    duplicate_mask = df.duplicated(
        subset=duplicate_keys,
        keep="first"
    )

    duplicate_by_source = (
        df.loc[duplicate_mask]
        .groupby("SRC")
        .size()
        .to_dict()
    )

    dropped_duplicates = int(
        duplicate_mask.sum()
    )

    df = df.loc[
        ~duplicate_mask
    ].copy()

    # -----------------------------------------------------
    # COLUMN ORDER
    # -----------------------------------------------------

    df = df[
        FINAL_COLUMNS
    ].copy()

    final_rows = len(df)

    # -----------------------------------------------------
    # REPORT
    # -----------------------------------------------------

    CLEANING_REPORT = {

        "initial_rows":
            int(initial_rows),

        "dropped_missing_patient_ids":
            int(dropped_missing_patient),

        "dropped_invalid_dates":
            int(dropped_invalid_dates),

        "dropped_invalid_diagnosis_codes":
            int(dropped_invalid_diagnosis),

        "dropped_duplicate_rows":
            int(dropped_duplicates),

        "final_rows":
            int(final_rows),

        "total_rows_removed":
            int(
                initial_rows - final_rows
            ),

        "date_range": {
            "start":
                "2018-01-01",

            "end":
                "2025-02-28"
        },

        "duplicate_rows_by_source": {
            str(k): int(v)
            for k, v
            in duplicate_by_source.items()
        },

        "final_rows_by_source": {
            str(k): int(v)
            for k, v
            in df.groupby("SRC")
            .size()
            .to_dict()
            .items()
        }
    }

    print(
        "\nRows after global cleaning:",
        final_rows
    )

    print(
        "Total rows removed:",
        initial_rows - final_rows
    )

    return df


# =========================================================
# DIAGNOSIS DICTIONARY
# =========================================================

def add_diagnosis_descriptions(df):

    dictionary = pd.read_csv(
        DX_DICTIONARY
    )

    print(
        "\nDiagnosis dictionary rows:",
        len(dictionary)
    )

    code_column = None
    description_column = None

    for column in dictionary.columns:

        column_lower = (
            column.lower().strip()
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

    if "DIAGNOSIS_DESC" in df.columns:

        df = df.drop(
            columns=["DIAGNOSIS_DESC"]
        )

    df = df.merge(
        dictionary,
        on="DIAGNOSIS_CODE",
        how="left"
    )

    missing_descriptions = int(
        df["DIAGNOSIS_DESC"]
        .isna()
        .sum()
    )

    print(
        "Rows without dictionary description:",
        missing_descriptions
    )

    return df


# =========================================================
# EXPORT
# =========================================================

def export_final_dataset(df):

    df = df[
        FINAL_COLUMNS
    ].copy()

    df.to_csv(
        FINAL_OUTPUT,
        index=False,
        encoding="utf-8"
    )

    print(
        "\nFinal dataset exported:"
    )

    print(
        FINAL_OUTPUT
    )

    print(
        "Rows:",
        len(df)
    )

    return FINAL_OUTPUT


# =========================================================
# FILE HASH
# =========================================================

def get_file_hash():

    if not FINAL_OUTPUT.exists():
        return None

    sha256 = hashlib.sha256()

    with open(
        FINAL_OUTPUT,
        "rb"
    ) as file:

        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b""
        ):

            sha256.update(chunk)

    return sha256.hexdigest()


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    source_a_input = len(
        pd.read_csv(SOURCE_A)
    )

    source_b_input = len(
        pd.read_csv(SOURCE_B)
    )

    source_c_input = len(
        pd.read_csv(SOURCE_C)
    )

    source_a = process_source_a()

    source_b = process_source_b()

    source_c = process_source_c()

    PIPELINE_REPORT["ingestion"] = {

        "input_rows": int(
            source_a_input
            + source_b_input
            + source_c_input
        ),

        "output_rows": int(
            len(source_a)
            + len(source_b)
            + len(source_c)
        ),

        "dropped": 0,

        "reason":
            "Vendor-specific transformation"
    }

    combined = combine_sources(
        source_a,
        source_b,
        source_c
    )

    PIPELINE_REPORT["combination"] = {

        "input_rows": int(
            len(source_a)
            + len(source_b)
            + len(source_c)
        ),

        "output_rows": int(
            len(combined)
        ),

        "dropped": 0,

        "reason":
            "Standardized vendor datasets combined"
    }

    final_data = clean_combined_data(
        combined
    )

    PIPELINE_REPORT["cleaning"] = {

        "input_rows":
            CLEANING_REPORT["initial_rows"],

        "output_rows":
            CLEANING_REPORT["final_rows"],

        "dropped":
            CLEANING_REPORT["total_rows_removed"],

        "reason": (
            "Missing patient IDs: "
            + str(
                CLEANING_REPORT[
                    "dropped_missing_patient_ids"
                ]
            )
            + "; Invalid dates: "
            + str(
                CLEANING_REPORT[
                    "dropped_invalid_dates"
                ]
            )
            + "; Invalid diagnosis codes: "
            + str(
                CLEANING_REPORT[
                    "dropped_invalid_diagnosis_codes"
                ]
            )
            + "; Duplicates: "
            + str(
                CLEANING_REPORT[
                    "dropped_duplicate_rows"
                ]
            )
        )
    }

    dictionary_input = len(
        final_data
    )

    final_data = add_diagnosis_descriptions(
        final_data
    )

    PIPELINE_REPORT["dictionary"] = {

        "input_rows":
            int(dictionary_input),

        "output_rows":
            int(len(final_data)),

        "dropped":
            0,

        "reason":
            "Diagnosis descriptions added using reference dictionary"
    }

    validation_passed = bool(
        validate_dataset(
            final_data
        )
    )

    PIPELINE_REPORT["validation"] = {

        "input_rows":
            int(len(final_data)),

        "output_rows":
            int(len(final_data)),

        "dropped":
            0,

        "reason":
            (
                "All validation checks passed"
                if validation_passed
                else
                "One or more validation checks failed"
            )
    }

    if validation_passed:

        export_final_dataset(
            final_data
        )

        PIPELINE_REPORT["export"] = {

            "input_rows":
                int(len(final_data)),

            "output_rows":
                int(len(final_data)),

            "dropped":
                0,

            "reason":
                "Validated dataset exported successfully"
        }

        print(
            "\nPipeline completed successfully."
        )

    else:

        print(
            "\nPipeline stopped because validation failed."
        )