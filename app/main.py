from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import pandas as pd
import uuid
from datetime import datetime

from app.pipeline import (
    process_source_a,
    process_source_b,
    process_source_c,
    combine_sources,
    clean_combined_data,
    add_diagnosis_descriptions,
    export_final_dataset,
)

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

FINAL_OUTPUT = OUTPUT_DIR / "final_harmonized.csv"

OUTPUT_DIR.mkdir(exist_ok=True)


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
        "application": "Multi-Source Data Harmonization Pipeline",
        "status": "running",
        "version": "1.0.0"
    }


# =========================================================
# SUMMARY
# =========================================================

@app.get("/summary")
def get_summary():

    if not FINAL_OUTPUT.exists():
        raise HTTPException(
            status_code=404,
            detail="Final harmonized dataset has not been generated yet."
        )

    try:
        df = pd.read_csv(FINAL_OUTPUT)

        source_counts = (
            df.groupby("SRC")
            .size()
            .to_dict()
        )

        return {
            "total_rows": int(len(df)),

            "distinct_claims": int(
                df["CLAIM_ID"].nunique()
            ),

            "distinct_patients": int(
                df["PATIENT_ID"].nunique()
            ),

            "distinct_diagnosis_codes": int(
                df["DIAGNOSIS_CODE"].nunique()
            ),

            "source_counts": {
                str(key): int(value)
                for key, value in source_counts.items()
            }
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# RUN PIPELINE
# =========================================================

@app.post("/run")
def run_pipeline():

    run_id = str(uuid.uuid4())

    started_at = datetime.now()

    stages = []

    try:

        # =================================================
        # STAGE 1 — INGESTION / STANDARDIZATION
        # =================================================

        stages.append({
            "stage": "ingestion",
            "status": "running"
        })

        source_a = process_source_a()

        source_b = process_source_b()

        source_c = process_source_c()

        stages[-1]["status"] = "completed"


        # =================================================
        # STAGE 2 — COMBINATION
        # =================================================

        stages.append({
            "stage": "combination",
            "status": "running"
        })

        combined = combine_sources(
            source_a,
            source_b,
            source_c
        )

        stages[-1]["status"] = "completed"


        # =================================================
        # STAGE 3 — GLOBAL CLEANING
        # =================================================

        stages.append({
            "stage": "cleaning",
            "status": "running"
        })

        final_data = clean_combined_data(
            combined
        )

        stages[-1]["status"] = "completed"


        # =================================================
        # STAGE 4 — DIAGNOSIS DICTIONARY
        # =================================================

        stages.append({
            "stage": "dictionary_lookup",
            "status": "running"
        })

        final_data = add_diagnosis_descriptions(
            final_data
        )

        stages[-1]["status"] = "completed"


        # =================================================
        # STAGE 5 — VALIDATION
        # =================================================

        stages.append({
            "stage": "validation",
            "status": "running"
        })

        validation_passed = validate_dataset(
            final_data
        )

        if validation_passed:

            stages[-1]["status"] = "completed"

        else:

            stages[-1]["status"] = "failed"

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

        output_file = export_final_dataset(
            final_data
        )

        stages[-1]["status"] = "completed"


        # =================================================
        # SAVE RUN INFORMATION
        # =================================================

        completed_at = datetime.now()

        runs[run_id] = {

            "run_id": run_id,

            "status": "completed",

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

            "run_id": run_id,

            "status": "failed",

            "started_at":
                started_at.isoformat(),

            "stages":
                stages
        }

        raise


    except Exception as e:

        runs[run_id] = {

            "run_id": run_id,

            "status": "failed",

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
def get_run_stages(run_id: str):

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
# GET VALIDATION RESULT
# =========================================================

@app.get("/run/{run_id}/validate")
def get_validation(run_id: str):

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

            "validation":
                None
        }


    if not FINAL_OUTPUT.exists():

        raise HTTPException(
            status_code=404,
            detail="Final dataset not found."
        )


    try:

        df = pd.read_csv(
            FINAL_OUTPUT
        )


        # -------------------------------------------------
        # BASIC COUNTS
        # -------------------------------------------------

        total_rows = len(df)

        distinct_claims = (
            df["CLAIM_ID"]
            .nunique()
        )

        distinct_patients = (
            df["PATIENT_ID"]
            .nunique()
        )

        distinct_diagnosis_codes = (
            df["DIAGNOSIS_CODE"]
            .nunique()
        )


        # -------------------------------------------------
        # DUPLICATES
        # -------------------------------------------------

        duplicate_count = (
            df.duplicated(
                subset=[
                    "SRC",
                    "CLAIM_ID",
                    "DIAGNOSIS_CODE"
                ]
            )
            .sum()
        )


        # -------------------------------------------------
        # MISSING PATIENT IDs
        # -------------------------------------------------

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

        missing_patient_count = (
            missing_patients.sum()
        )


        # -------------------------------------------------
        # INVALID DATES
        # -------------------------------------------------

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

        invalid_date_count = (
            invalid_dates.sum()
        )


        # -------------------------------------------------
        # SOURCE COUNTS
        # -------------------------------------------------

        source_counts = (
            df.groupby("SRC")
            .size()
            .to_dict()
        )


        # -------------------------------------------------
        # RETURN VALIDATION RESULT
        # -------------------------------------------------

        return {

            "run_id":
                run_id,

            "status":
                "validated",

            "validation": {

                "total_rows":
                    int(total_rows),

                "distinct_claims":
                    int(distinct_claims),

                "distinct_patients":
                    int(distinct_patients),

                "distinct_diagnosis_codes":
                    int(distinct_diagnosis_codes),

                "source_counts": {
                    str(key): int(value)
                    for key, value
                    in source_counts.items()
                },

                "missing_patient_ids":
                    int(
                        missing_patient_count
                    ),

                "invalid_service_dates":
                    int(
                        invalid_date_count
                    ),

                "duplicate_rows":
                    int(
                        duplicate_count
                    )
            }
        }


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )