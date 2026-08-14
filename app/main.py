from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from pathlib import Path
from datetime import datetime
import uuid

import pandas as pd

import app.pipeline as pipeline
from app.validation import validate_dataset


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Multi-Source Data Harmonization Pipeline",
    description=(
        "API for harmonizing healthcare claims data "
        "from multiple vendor sources."
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
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = BASE_DIR / "output"

FINAL_OUTPUT = (
    OUTPUT_DIR / "final_harmonized.csv"
)

OUTPUT_DIR.mkdir(
    exist_ok=True
)


# =========================================================
# PIPELINE RUN STORAGE
# =========================================================

runs = {}


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "application":
            "Multi-Source Data Harmonization Pipeline",

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
            detail=(
                "Final harmonized dataset "
                "has not been generated yet."
            )
        )

    try:

        df = pd.read_csv(
            FINAL_OUTPUT
        )

        source_counts = (
            df.groupby("SRC")
            .size()
            .to_dict()
        )

        return {

            "total_rows":
                int(len(df)),

            "distinct_claims":
                int(
                    df["CLAIM_ID"].nunique()
                ),

            "distinct_patients":
                int(
                    df["PATIENT_ID"].nunique()
                ),

            "distinct_diagnosis_codes":
                int(
                    df["DIAGNOSIS_CODE"].nunique()
                ),

            "source_counts": {

                str(key):
                    int(value)

                for key, value
                in source_counts.items()
            }
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# DOWNLOAD FINAL CSV
# =========================================================

@app.get("/download")
def download_final_csv():

    if not FINAL_OUTPUT.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "Final harmonized dataset "
                "not found."
            )
        )

    return FileResponse(
        path=FINAL_OUTPUT,
        media_type="text/csv",
        filename="final_harmonized.csv"
    )


# =========================================================
# RUN PIPELINE
# =========================================================

@app.post("/run")
def run_pipeline():

    run_id = str(
        uuid.uuid4()
    )

    started_at = datetime.now()

    stages = []

    try:

        # =================================================
        # STAGE 1 — INGESTION
        # =================================================

        stages.append({
            "stage": "ingestion",
            "status": "running"
        })

        source_a = (
            pipeline.process_source_a()
        )

        source_b = (
            pipeline.process_source_b()
        )

        source_c = (
            pipeline.process_source_c()
        )

        stages[-1]["status"] = (
            "completed"
        )


        # =================================================
        # STAGE 2 — COMBINATION
        # =================================================

        stages.append({
            "stage": "combination",
            "status": "running"
        })

        combined = (
            pipeline.combine_sources(
                source_a,
                source_b,
                source_c
            )
        )

        stages[-1]["status"] = (
            "completed"
        )


        # =================================================
        # STAGE 3 — GLOBAL CLEANING
        # =================================================

        stages.append({
            "stage": "cleaning",
            "status": "running"
        })

        final_data = (
            pipeline.clean_combined_data(
                combined
            )
        )

        stages[-1]["status"] = (
            "completed"
        )


        # =================================================
        # STAGE 4 — DIAGNOSIS DICTIONARY
        # =================================================

        stages.append({
            "stage": "dictionary_lookup",
            "status": "running"
        })

        final_data = (
            pipeline.add_diagnosis_descriptions(
                final_data
            )
        )

        stages[-1]["status"] = (
            "completed"
        )


        # =================================================
        # STAGE 5 — VALIDATION
        # =================================================

        stages.append({
            "stage": "validation",
            "status": "running"
        })

        validation_passed = bool(
            validate_dataset(
                final_data
            )
        )

        if validation_passed:

            stages[-1]["status"] = (
                "completed"
            )

        else:

            stages[-1]["status"] = (
                "failed"
            )

            raise HTTPException(
                status_code=422,
                detail=(
                    "Dataset validation failed. "
                    "Final CSV was not exported."
                )
            )


        # =================================================
        # STAGE 6 — EXPORT
        # =================================================

        stages.append({
            "stage": "export",
            "status": "running"
        })

        output_file = (
            pipeline.export_final_dataset(
                final_data
            )
        )

        stages[-1]["status"] = (
            "completed"
        )


        # =================================================
        # STORE RUN
        # =================================================

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
                stages
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
                stages
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

            "error":
                str(e)
        }

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# GET PIPELINE STAGES
# =========================================================

@app.get("/run/{run_id}/stages")
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
            runs[run_id]["status"],

        "stages":
            runs[run_id]["stages"]
    }


# =========================================================
# GET PIPELINE QUALITY REPORT
# =========================================================

@app.get("/run/{run_id}/report")
def get_pipeline_report(
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
                runs[run_id]["status"],

            "pipeline_report":
                None
        }


    # -----------------------------------------------------
    # IMPORTANT:
    # Access the variable through the pipeline module.
    # This avoids stale imported values.
    # -----------------------------------------------------

    cleaning_report = (
        pipeline.CLEANING_REPORT
    )


    if not cleaning_report:

        raise HTTPException(
            status_code=404,
            detail=(
                "Cleaning report is not available."
            )
        )


    return {

        "run_id":
            run_id,

        "status":
            "completed",

        "pipeline_report":
            cleaning_report
    }


# =========================================================
# GET VALIDATION RESULT
# =========================================================

@app.get("/run/{run_id}/validate")
def get_validation(
    run_id: str
):

    # =====================================================
    # CHECK RUN ID
    # =====================================================

    if run_id not in runs:

        raise HTTPException(
            status_code=404,
            detail="Run ID not found."
        )


    # =====================================================
    # CHECK RUN STATUS
    # =====================================================

    if runs[run_id]["status"] != "completed":

        return {

            "run_id":
                run_id,

            "status":
                runs[run_id]["status"],

            "validation":
                None
        }


    # =====================================================
    # CHECK OUTPUT FILE
    # =====================================================

    if not FINAL_OUTPUT.exists():

        raise HTTPException(
            status_code=404,
            detail="Final dataset not found."
        )


    try:

        # =================================================
        # LOAD FINAL DATASET
        # =================================================

        df = pd.read_csv(
            FINAL_OUTPUT
        )


        # =================================================
        # BASIC COUNTS
        # =================================================

        total_rows = int(
            len(df)
        )

        distinct_claims = int(
            df["CLAIM_ID"].nunique()
        )

        distinct_patients = int(
            df["PATIENT_ID"].nunique()
        )

        distinct_diagnosis_codes = int(
            df["DIAGNOSIS_CODE"].nunique()
        )


        # =================================================
        # SOURCE COUNTS
        # =================================================

        source_counts = (
            df.groupby("SRC")
            .size()
            .to_dict()
        )

        source_counts = {

            str(key):
                int(value)

            for key, value
            in source_counts.items()
        }


        # =================================================
        # EXPECTED SOURCE COUNTS
        # =================================================

        expected_source_counts = {

            "A":
                67531,

            "B":
                52819,

            "C":
                39354
        }


        source_counts_passed = bool(
            source_counts
            == expected_source_counts
        )


        # =================================================
        # P00042 CHECKS
        # =================================================

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


        # =================================================
        # DIAGNOSIS CODE FORMAT
        # =================================================

        diagnosis_codes = (
            df["DIAGNOSIS_CODE"]
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


        # =================================================
        # DUPLICATES
        # =================================================

        duplicate_count = int(
            df.duplicated(
                subset=[
                    "SRC",
                    "CLAIM_ID",
                    "DIAGNOSIS_CODE"
                ]
            ).sum()
        )

        duplicate_check_passed = bool(
            duplicate_count == 0
        )


        # =================================================
        # MISSING PATIENT IDs
        # =================================================

        missing_patients = (

            df["PATIENT_ID"].isna()

            |

            (
                df["PATIENT_ID"]
                .astype(str)
                .str.strip()
                == ""
            )
        )

        missing_patient_count = int(
            missing_patients.sum()
        )

        missing_patient_check_passed = bool(
            missing_patient_count == 0
        )


        # =================================================
        # INVALID DATES
        # =================================================

        start_date = pd.Timestamp(
            "2018-01-01"
        )

        end_date = pd.Timestamp(
            "2025-02-28"
        )

        service_dates = pd.to_datetime(
            df["SERVICE_DATE"],
            errors="coerce"
        )

        invalid_dates = (

            service_dates.isna()

            |

            (service_dates < start_date)

            |

            (service_dates > end_date)
        )

        invalid_date_count = int(
            invalid_dates.sum()
        )

        date_check_passed = bool(
            invalid_date_count == 0
        )


        # =================================================
        # EXPECTED VALUE CHECKS
        # =================================================

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


        # =================================================
        # OVERALL VALIDATION
        # =================================================

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
                date_check_passed,
                missing_patient_check_passed,
                duplicate_check_passed
            ])
        )


        # =================================================
        # RETURN VALIDATION
        # =================================================

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
                        missing_patient_check_passed
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
                        date_check_passed
                },

                "duplicate_rows": {

                    "count":
                        duplicate_count,

                    "passed":
                        duplicate_check_passed
                },

                "all_checks_passed":
                    all_checks_passed
            }
        }


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )