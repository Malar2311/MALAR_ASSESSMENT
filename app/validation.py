import pandas as pd


# =========================================================
# EXPECTED ACCEPTANCE VALUES
# =========================================================

EXPECTED_TOTAL_ROWS = 159704

EXPECTED_DISTINCT_CLAIMS = 68205

EXPECTED_DISTINCT_PATIENTS = 11963

EXPECTED_DISTINCT_DIAGNOSIS_CODES = 44

EXPECTED_SOURCE_COUNTS = {
    "A": 67531,
    "B": 52819,
    "C": 39354,
}


# =========================================================
# VALIDATION
# =========================================================

def validate_dataset(df):

    print("\n" + "=" * 60)
    print("DATASET VALIDATION")
    print("=" * 60)

    all_passed = True

    # -----------------------------------------------------
    # TOTAL ROWS
    # -----------------------------------------------------

    actual_rows = int(
        len(df)
    )

    passed = bool(
        actual_rows
        == EXPECTED_TOTAL_ROWS
    )

    print(
        f"\nTotal rows: "
        f"{actual_rows} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # -----------------------------------------------------
    # CLAIMS
    # -----------------------------------------------------

    actual_claims = int(
        df[
            "CLAIM_ID"
        ].nunique()
    )

    passed = bool(
        actual_claims
        == EXPECTED_DISTINCT_CLAIMS
    )

    print(
        f"Distinct claims: "
        f"{actual_claims} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # -----------------------------------------------------
    # PATIENTS
    # -----------------------------------------------------

    actual_patients = int(
        df[
            "PATIENT_ID"
        ].nunique()
    )

    passed = bool(
        actual_patients
        == EXPECTED_DISTINCT_PATIENTS
    )

    print(
        f"Distinct patients: "
        f"{actual_patients} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # -----------------------------------------------------
    # DIAGNOSIS CODES
    # -----------------------------------------------------

    actual_diagnosis_codes = int(
        df[
            "DIAGNOSIS_CODE"
        ].nunique()
    )

    passed = bool(
        actual_diagnosis_codes
        == EXPECTED_DISTINCT_DIAGNOSIS_CODES
    )

    print(
        f"Distinct diagnosis codes: "
        f"{actual_diagnosis_codes} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # -----------------------------------------------------
    # SOURCE COUNTS
    # -----------------------------------------------------

    actual_source_counts = {
        str(key): int(value)
        for key, value
        in df.groupby("SRC")
        .size()
        .to_dict()
        .items()
    }

    print("\nSource counts:")

    for source, expected in (
        EXPECTED_SOURCE_COUNTS.items()
    ):

        actual = int(
            actual_source_counts.get(
                source,
                0
            )
        )

        passed = bool(
            actual == expected
        )

        print(
            f"  Source {source}: "
            f"{actual} "
            f"{'✓ PASS' if passed else '✗ FAIL'}"
        )

        if not passed:
            all_passed = False

    # -----------------------------------------------------
    # DATES
    # -----------------------------------------------------

    start_date = pd.Timestamp(
        "2018-01-01"
    )

    end_date = pd.Timestamp(
        "2025-02-28"
    )

    service_dates = pd.to_datetime(
        df[
            "SERVICE_DATE"
        ],
        errors="coerce"
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

    passed = bool(
        invalid_date_count == 0
    )

    print(
        f"\nInvalid service dates: "
        f"{invalid_date_count} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # -----------------------------------------------------
    # MISSING PATIENTS
    # -----------------------------------------------------

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

    passed = bool(
        missing_patient_count == 0
    )

    print(
        f"Missing patient IDs: "
        f"{missing_patient_count} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # -----------------------------------------------------
    # DUPLICATES
    # -----------------------------------------------------

    duplicate_count = int(
        df.duplicated(
            subset=[
                "SRC",
                "CLAIM_ID",
                "DIAGNOSIS_CODE"
            ]
        ).sum()
    )

    passed = bool(
        duplicate_count == 0
    )

    print(
        f"Duplicate rows: "
        f"{duplicate_count} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # -----------------------------------------------------
    # FINAL
    # -----------------------------------------------------

    print("\n" + "=" * 60)

    if all_passed:

        print(
            "ALL VALIDATION CHECKS PASSED ✓"
        )

    else:

        print(
            "SOME VALIDATION CHECKS FAILED ✗"
        )

    print("=" * 60)

    return bool(all_passed)