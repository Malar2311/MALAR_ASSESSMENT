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

EXPECTED_P00042_ROWS = 7
EXPECTED_P00042_DIAGNOSIS_CODES = 7


# =========================================================
# VALIDATION FUNCTION
# =========================================================

def validate_dataset(df):
    """
    Validate the final harmonized dataset against
    the required acceptance criteria.

    Returns:
        bool: True when all checks pass.
    """

    print("\n" + "=" * 60)
    print("DATASET VALIDATION")
    print("=" * 60)

    all_passed = True

    # =====================================================
    # 1. TOTAL ROW COUNT
    # =====================================================

    actual_rows = len(df)

    passed = actual_rows == EXPECTED_TOTAL_ROWS

    print(
        f"\nTotal rows: "
        f"{actual_rows} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # =====================================================
    # 2. DISTINCT CLAIMS
    # =====================================================

    actual_claims = df["CLAIM_ID"].nunique()

    passed = actual_claims == EXPECTED_DISTINCT_CLAIMS

    print(
        f"Distinct claims: "
        f"{actual_claims} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # =====================================================
    # 3. DISTINCT PATIENTS
    # =====================================================

    actual_patients = df["PATIENT_ID"].nunique()

    passed = actual_patients == EXPECTED_DISTINCT_PATIENTS

    print(
        f"Distinct patients: "
        f"{actual_patients} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # =====================================================
    # 4. DISTINCT DIAGNOSIS CODES
    # =====================================================

    actual_diagnosis_codes = (
        df["DIAGNOSIS_CODE"].nunique()
    )

    passed = (
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

    # =====================================================
    # 5. SOURCE COUNTS
    # =====================================================

    actual_source_counts = (
        df.groupby("SRC")
        .size()
        .to_dict()
    )

    print("\nSource counts:")

    for source, expected in EXPECTED_SOURCE_COUNTS.items():

        actual = actual_source_counts.get(
            source,
            0
        )

        passed = actual == expected

        print(
            f"  Source {source}: "
            f"{actual} "
            f"{'✓ PASS' if passed else '✗ FAIL'}"
        )

        if not passed:
            all_passed = False

    # =====================================================
    # 6. P00042 — TOTAL ROWS
    # =====================================================

    patient_00042 = df[
        df["PATIENT_ID"].astype(str).str.strip()
        == "P00042"
    ]

    p00042_rows = len(patient_00042)

    passed = (
        p00042_rows
        == EXPECTED_P00042_ROWS
    )

    print(
        f"\nPatient P00042 - total rows: "
        f"{p00042_rows} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # =====================================================
    # 7. P00042 — DISTINCT DIAGNOSIS CODES
    # =====================================================

    p00042_diagnosis_codes = (
        patient_00042["DIAGNOSIS_CODE"]
        .nunique()
    )

    passed = (
        p00042_diagnosis_codes
        == EXPECTED_P00042_DIAGNOSIS_CODES
    )

    print(
        f"Patient P00042 - distinct diagnosis codes: "
        f"{p00042_diagnosis_codes} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # =====================================================
    # 8. DIAGNOSIS CODE FORMAT
    # =====================================================

    diagnosis_codes = (
        df["DIAGNOSIS_CODE"]
        .astype(str)
        .str.strip()
    )

    invalid_code_format = (
        diagnosis_codes.eq("")
        | diagnosis_codes.str.contains(
            r"\.",
            regex=True,
            na=False
        )
        | diagnosis_codes.ne(
            diagnosis_codes.str.upper()
        )
    )

    invalid_code_count = invalid_code_format.sum()

    passed = invalid_code_count == 0

    print(
        f"Invalid diagnosis code format: "
        f"{invalid_code_count} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # =====================================================
    # 9. DATE RANGE
    # =====================================================

    start_date = pd.Timestamp(
        "2018-01-01"
    )

    end_date = pd.Timestamp(
        "2025-02-28"
    )

    invalid_dates = (
        (df["SERVICE_DATE"] < start_date)
        | (df["SERVICE_DATE"] > end_date)
        | (df["SERVICE_DATE"].isna())
    )

    invalid_date_count = (
        invalid_dates.sum()
    )

    passed = invalid_date_count == 0

    print(
        f"Invalid service dates: "
        f"{invalid_date_count} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # =====================================================
    # 10. MISSING PATIENT IDs
    # =====================================================

    missing_patients = (
        df["PATIENT_ID"].isna()
        | (
            df["PATIENT_ID"]
            .astype(str)
            .str.strip()
            == ""
        )
    )

    missing_patient_count = (
        missing_patients.sum()
    )

    passed = missing_patient_count == 0

    print(
        f"Missing patient IDs: "
        f"{missing_patient_count} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # =====================================================
    # 11. DUPLICATE CHECK
    # =====================================================

    duplicate_keys = [
        "SRC",
        "CLAIM_ID",
        "DIAGNOSIS_CODE"
    ]

    duplicate_count = (
        df.duplicated(
            subset=duplicate_keys
        )
        .sum()
    )

    passed = duplicate_count == 0

    print(
        f"Duplicate rows: "
        f"{duplicate_count} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # =====================================================
    # FINAL RESULT
    # =====================================================

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

    return all_passed