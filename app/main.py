from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from pathlib import Path
from datetime import datetime
import uuid
import pandas as pd

from app.pipeline import (
    process_source_a,
    process_source_b,
    process_source_c,
    combine_sources,
    clean_combined_data,
    add_diagnosis_descriptions,
    export_final_dataset,
    CLEANING_REPORT,
)

from app import pipeline

from app.validation import validate_dataset


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="Multi-Source Healthcare Claims Data Harmonization Pipeline",
    description=(
        "Pipeline for processing and harmonizing "
        "healthcare claims data from multiple vendors."
    ),
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(
    __file__
).resolve().parent.parent

OUTPUT_DIR = BASE_DIR / "output"

FINAL_OUTPUT = (
    OUTPUT_DIR /
    "final_harmonized.csv"
)

OUTPUT_DIR.mkdir(
    exist_ok=True
)


# =========================================================
# RUN STORAGE
# =========================================================

runs = {}

last_output_hash = None


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {

        "application":
            "Multi-Source Healthcare Claims Data Harmonization Pipeline",

        "status":
            "running",

        "version":
            "1.0.0"
    }


# =========================================================
# SUMMARY
# =========================================================

@app.get("/summary")
def get_summary():

    if not FINAL_OUTPUT.exists():

        raise HTTPException(
            status_code=404,
            detail=
                "Final harmonized dataset "
                "has not been generated yet."
        )

    try:

        df = pd.read_csv(
            FINAL_OUTPUT
        )

        source_summary = {}

        for source in sorted(
            df["SRC"]
            .dropna()
            .unique()
        ):

            source_df = df[
                df["SRC"] == source
            ]

            source_summary[
                str(source)
            ] = {

                "rows":
                    int(len(source_df)),

                "distinct_claims":
                    int(
                        source_df[
                            "CLAIM_ID"
                        ].nunique()
                    ),

                "distinct_patients":
                    int(
                        source_df[
                            "PATIENT_ID"
                        ].nunique()
                    )
            }

        return {

            "total_rows":
                int(len(df)),

            "distinct_claims":
                int(
                    df[
                        "CLAIM_ID"
                    ].nunique()
                ),

            "distinct_patients":
                int(
                    df[
                        "PATIENT_ID"
                    ].nunique()
                ),

            "distinct_diagnosis_codes":
                int(
                    df[
                        "DIAGNOSIS_CODE"
                    ].nunique()
                ),

            "source_counts":
                {
                    str(key): int(value)
                    for key, value
                    in df.groupby("SRC")
                    .size()
                    .to_dict()
                    .items()
                },

            "source_summary":
                source_summary
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# DOWNLOAD
# =========================================================

@app.get("/download")
def download_final_csv():

    if not FINAL_OUTPUT.exists():

        raise HTTPException(
            status_code=404,
            detail=
                "Final harmonized dataset "
                "not found."
        )

    return FileResponse(

        path=FINAL_OUTPUT,

        media_type="text/csv",

        filename=
            "final_harmonized.csv"
    )


# =========================================================
# RUN PIPELINE
# =========================================================

@app.post("/run")
def run_pipeline():

    global last_output_hash

    run_id = str(
        uuid.uuid4()
    )

    started_at = datetime.now()

    stages = []

    try:

        # -------------------------------------------------
        # RESET REPORT
        # -------------------------------------------------

        pipeline.PIPELINE_REPORT.clear()

        pipeline.PIPELINE_REPORT.update({

            "ingestion": {},
            "combination": {},
            "cleaning": {},
            "dictionary": {},
            "validation": {},
            "export": {}
        })

        pipeline.CLEANING_REPORT.clear()

        # -------------------------------------------------
        # STAGE 1
        # -------------------------------------------------

        stages.append({
            "stage":
                "ingestion",

            "status":
                "running"
        })

        source_a_input = len(
            pd.read_csv(
                pipeline.SOURCE_A
            )
        )

        source_b_input = len(
            pd.read_csv(
                pipeline.SOURCE_B
            )
        )

        source_c_input = len(
            pd.read_csv(
                pipeline.SOURCE_C
            )
        )

        source_a = process_source_a()

        source_b = process_source_b()

        source_c = process_source_c()

        ingestion_input = (
            source_a_input
            + source_b_input
            + source_c_input
        )

        ingestion_output = (
            len(source_a)
            + len(source_b)
            + len(source_c)
        )

        pipeline.PIPELINE_REPORT[
            "ingestion"
        ] = {

            "input_rows":
                int(ingestion_input),

            "output_rows":
                int(ingestion_output),

            "dropped":
                0,

            "reason":
                "Vendor-specific transformation and diagnosis expansion"
        }

        stages[-1]["status"] = "completed"

        # -------------------------------------------------
        # STAGE 2
        # -------------------------------------------------

        stages.append({
            "stage":
                "combination",

            "status":
                "running"
        })

        combined = combine_sources(
            source_a,
            source_b,
            source_c
        )

        pipeline.PIPELINE_REPORT[
            "combination"
        ] = {

            "input_rows":
                int(ingestion_output),

            "output_rows":
                int(len(combined)),

            "dropped":
                0,

            "reason":
                "Standardized vendor datasets combined"
        }

        stages[-1]["status"] = "completed"

        # -------------------------------------------------
        # STAGE 3
        # -------------------------------------------------

        stages.append({
            "stage":
                "cleaning",

            "status":
                "running"
        })

        final_data = clean_combined_data(
            combined
        )

        cleaning = pipeline.CLEANING_REPORT

        pipeline.PIPELINE_REPORT[
            "cleaning"
        ] = {

            "input_rows":
                int(
                    cleaning[
                        "initial_rows"
                    ]
                ),

            "output_rows":
                int(
                    cleaning[
                        "final_rows"
                    ]
                ),

            "dropped":
                int(
                    cleaning[
                        "total_rows_removed"
                    ]
                ),

            "reason": (
                "Missing patient IDs: "
                + str(
                    cleaning[
                        "dropped_missing_patient_ids"
                    ]
                )
                + "; Invalid dates: "
                + str(
                    cleaning[
                        "dropped_invalid_dates"
                    ]
                )
                + "; Invalid diagnosis codes: "
                + str(
                    cleaning[
                        "dropped_invalid_diagnosis_codes"
                    ]
                )
                + "; Duplicates: "
                + str(
                    cleaning[
                        "dropped_duplicate_rows"
                    ]
                )
            )
        }

        stages[-1]["status"] = "completed"

        # -------------------------------------------------
        # STAGE 4
        # -------------------------------------------------

        stages.append({
            "stage":
                "dictionary_lookup",

            "status":
                "running"
        })

        dictionary_input = len(
            final_data
        )

        final_data = add_diagnosis_descriptions(
            final_data
        )

        pipeline.PIPELINE_REPORT[
            "dictionary"
        ] = {

            "input_rows":
                int(dictionary_input),

            "output_rows":
                int(len(final_data)),

            "dropped":
                0,

            "reason":
                "Diagnosis descriptions added using reference dictionary"
        }

        stages[-1]["status"] = "completed"

        # -------------------------------------------------
        # STAGE 5
        # -------------------------------------------------

        stages.append({
            "stage":
                "validation",

            "status":
                "running"
        })

        validation_passed = bool(
            validate_dataset(
                final_data
            )
        )

        pipeline.PIPELINE_REPORT[
            "validation"
        ] = {

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

        if not validation_passed:

            stages[-1]["status"] = "failed"

            raise HTTPException(
                status_code=422,
                detail=
                    "Dataset validation failed."
            )

        stages[-1]["status"] = "completed"

        # -------------------------------------------------
        # STAGE 6
        # -------------------------------------------------

        stages.append({
            "stage":
                "export",

            "status":
                "running"
        })

        output_file = export_final_dataset(
            final_data
        )

        current_hash = (
            pipeline.get_file_hash()
        )

        identical_to_previous = False

        if (
            last_output_hash is not None
            and current_hash == last_output_hash
        ):

            identical_to_previous = True

        last_output_hash = current_hash

        pipeline.PIPELINE_REPORT[
            "export"
        ] = {

            "input_rows":
                int(len(final_data)),

            "output_rows":
                int(len(final_data)),

            "dropped":
                0,

            "reason":
                "Validated dataset exported successfully",

            "file_hash":
                current_hash
        }

        stages[-1]["status"] = "completed"

        # -------------------------------------------------
        # STORE RUN
        # -------------------------------------------------

        completed_at = datetime.now()

        runs[run_id] = {

            "run_id":
                run_id,

            "status":
                "completed",

            "started_at":
                started_at.isoformat(),

            "completed_at":
                completed_at.isoformat(),

            "rows":
                int(len(final_data)),

            "output_file":
                str(output_file),

            "stages":
                stages,

            "pipeline_report":
                pipeline.PIPELINE_REPORT.copy(),

            "reproducibility":
                {

                    "current_file_hash":
                        current_hash,

                    "identical_to_previous_run":
                        identical_to_previous
                }
        }

        return runs[run_id]

    except HTTPException:

        runs[run_id] = {

            "run_id":
                run_id,

            "status":
                "failed",

            "started_at":
                started_at.isoformat(),

            "stages":
                stages,

            "pipeline_report":
                pipeline.PIPELINE_REPORT.copy()
        }

        raise

    except Exception as e:

        runs[run_id] = {

            "run_id":
                run_id,

            "status":
                "failed",

            "started_at":
                started_at.isoformat(),

            "stages":
                stages,

            "pipeline_report":
                pipeline.PIPELINE_REPORT.copy(),

            "error":
                str(e)
        }

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# STAGES
# =========================================================

@app.get(
    "/run/{run_id}/stages"
)
def get_run_stages(
    run_id: str
):

    if run_id not in runs:

        raise HTTPException(
            status_code=404,
            detail="Run ID not found."
        )

    return {

        "run_id":
            run_id,

        "status":
            runs[run_id][
                "status"
            ],

        "stages":
            runs[run_id][
                "stages"
            ],

        "pipeline_report":
            runs[run_id][
                "pipeline_report"
            ]
    }


# =========================================================
# VALIDATION
# =========================================================

@app.get(
    "/run/{run_id}/validate"
)
def get_validation(
    run_id: str
):

    if run_id not in runs:

        raise HTTPException(
            status_code=404,
            detail="Run ID not found."
        )

    if runs[run_id]["status"] != "completed":

        return {

            "run_id":
                run_id,

            "status":
                runs[run_id][
                    "status"
                ],

            "validation":
                None
        }

    if not FINAL_OUTPUT.exists():

        raise HTTPException(
            status_code=404,
            detail=
                "Final dataset not found."
        )

    try:

        df = pd.read_csv(
            FINAL_OUTPUT
        )

        total_rows = int(
            len(df)
        )

        distinct_claims = int(
            df[
                "CLAIM_ID"
            ].nunique()
        )

        distinct_patients = int(
            df[
                "PATIENT_ID"
            ].nunique()
        )

        distinct_diagnosis_codes = int(
            df[
                "DIAGNOSIS_CODE"
            ].nunique()
        )

        source_counts = {
            str(k): int(v)
            for k, v
            in df.groupby("SRC")
            .size()
            .to_dict()
            .items()
        }

        expected_source_counts = {
            "A": 67531,
            "B": 52819,
            "C": 39354
        }

        source_counts_passed = bool(
            source_counts
            == expected_source_counts
        )

        # -------------------------------------------------
        # P00042
        # -------------------------------------------------

        patient_00042 = df[
            df["PATIENT_ID"]
            .astype(str)
            .str.strip()
            == "P00042"
        ]

        p00042_rows = int(
            len(patient_00042)
        )

        p00042_diagnosis_codes = int(
            patient_00042[
                "DIAGNOSIS_CODE"
            ].nunique()
        )

        p00042_rows_passed = bool(
            p00042_rows == 7
        )

        p00042_diagnosis_passed = bool(
            p00042_diagnosis_codes == 7
        )

        # -------------------------------------------------
        # DIAGNOSIS FORMAT
        # -------------------------------------------------

        diagnosis_codes = (
            df[
                "DIAGNOSIS_CODE"
            ]
            .astype(str)
            .str.strip()
        )

        invalid_code_format = (
            diagnosis_codes.eq("")
            |
            diagnosis_codes.str.contains(
                r"\.",
                regex=True,
                na=False
            )
            |
            diagnosis_codes.ne(
                diagnosis_codes.str.upper()
            )
        )

        invalid_code_count = int(
            invalid_code_format.sum()
        )

        diagnosis_format_passed = bool(
            invalid_code_count == 0
        )

        # -------------------------------------------------
        # MISSING PATIENT
        # -------------------------------------------------

        missing_patients = (
            df[
                "PATIENT_ID"
            ].isna()
            |
            (
                df[
                    "PATIENT_ID"
                ]
                .astype(str)
                .str.strip()
                == ""
            )
        )

        missing_patient_count = int(
            missing_patients.sum()
        )

        missing_patient_passed = bool(
            missing_patient_count == 0
        )

        # -------------------------------------------------
        # DATES
        # -------------------------------------------------

        service_dates = pd.to_datetime(
            df[
                "SERVICE_DATE"
            ],
            errors="coerce"
        )

        start_date = pd.Timestamp(
            "2018-01-01"
        )

        end_date = pd.Timestamp(
            "2025-02-28"
        )

        invalid_dates = (
            service_dates.isna()
            |
            (
                service_dates
                < start_date
            )
            |
            (
                service_dates
                > end_date
            )
        )

        invalid_date_count = int(
            invalid_dates.sum()
        )

        date_passed = bool(
            invalid_date_count == 0
        )

        # -------------------------------------------------
        # DUPLICATES
        # -------------------------------------------------

        duplicate_count = int(
            df.duplicated(
                subset=[
                    "SRC",
                    "CLAIM_ID",
                    "DIAGNOSIS_CODE"
                ]
            ).sum()
        )

        duplicate_passed = bool(
            duplicate_count == 0
        )

        # -------------------------------------------------
        # EXPECTED COUNTS
        # -------------------------------------------------

        total_rows_passed = bool(
            total_rows == 159704
        )

        claims_passed = bool(
            distinct_claims == 68205
        )

        patients_passed = bool(
            distinct_patients == 11963
        )

        diagnosis_count_passed = bool(
            distinct_diagnosis_codes == 44
        )

        all_checks_passed = bool(
            all([
                total_rows_passed,
                claims_passed,
                patients_passed,
                diagnosis_count_passed,
                source_counts_passed,
                p00042_rows_passed,
                p00042_diagnosis_passed,
                diagnosis_format_passed,
                missing_patient_passed,
                date_passed,
                duplicate_passed
            ])
        )

        return {

            "run_id":
                run_id,

            "status":
                "validated",

            "validation": {

                "total_rows": {
                    "actual":
                        total_rows,
                    "expected":
                        159704,
                    "passed":
                        total_rows_passed
                },

                "distinct_claims": {
                    "actual":
                        distinct_claims,
                    "expected":
                        68205,
                    "passed":
                        claims_passed
                },

                "distinct_patients": {
                    "actual":
                        distinct_patients,
                    "expected":
                        11963,
                    "passed":
                        patients_passed
                },

                "distinct_diagnosis_codes": {
                    "actual":
                        distinct_diagnosis_codes,
                    "expected":
                        44,
                    "passed":
                        diagnosis_count_passed
                },

                "source_counts": {
                    "actual":
                        source_counts,

                    "expected":
                        expected_source_counts,

                    "passed":
                        source_counts_passed
                },

                "p00042": {

                    "total_rows":
                        p00042_rows,

                    "expected_rows":
                        7,

                    "rows_passed":
                        p00042_rows_passed,

                    "distinct_diagnosis_codes":
                        p00042_diagnosis_codes,

                    "expected_diagnosis_codes":
                        7,

                    "diagnosis_codes_passed":
                        p00042_diagnosis_passed
                },

                "diagnosis_code_format": {

                    "invalid_code_count":
                        invalid_code_count,

                    "passed":
                        diagnosis_format_passed
                },

                "missing_patient_ids": {

                    "count":
                        missing_patient_count,

                    "passed":
                        missing_patient_passed
                },

                "invalid_service_dates": {

                    "count":
                        invalid_date_count,

                    "allowed_range": {

                        "start":
                            "2018-01-01",

                        "end":
                            "2025-02-28"
                    },

                    "passed":
                        date_passed
                },

                "duplicate_rows": {

                    "count":
                        duplicate_count,

                    "passed":
                        duplicate_passed
                },

                "reproducibility":
                    runs[run_id].get(
                        "reproducibility",
                        {}
                    ),

                "all_checks_passed":
                    all_checks_passed
            }
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )