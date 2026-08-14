import pandas as pd


# ---------------------------------------------------------
# EXPECTED ACCEPTANCE VALUES
# ---------------------------------------------------------

EXPECTED_TOTAL_ROWS = 159704
EXPECTED_DISTINCT_CLAIMS = 68205
EXPECTED_DISTINCT_PATIENTS = 11963
EXPECTED_DISTINCT_DIAGNOSIS_CODES = 44

EXPECTED_SOURCE_COUNTS = {
    "A": 67531,
    "B": 52819,
    "C": 39354,
}


# ---------------------------------------------------------
# VALIDATION FUNCTION
# ---------------------------------------------------------

def validate_dataset(df):
    """
    Validate the final harmonized dataset against
    the required acceptance criteria.
    """

    print("\n" + "=" * 60)
    print("DATASET VALIDATION")
    print("=" * 60)

    all_passed = True

    # -----------------------------------------------------
    # 1. TOTAL ROW COUNT
    # -----------------------------------------------------

    actual_rows = len(df)

    passed = actual_rows == EXPECTED_TOTAL_ROWS

    print(
        f"\nTotal rows: "
        f"{actual_rows} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # -----------------------------------------------------
    # 2. DISTINCT CLAIMS
    # -----------------------------------------------------

    actual_claims = df["CLAIM_ID"].nunique()

    passed = (
        actual_claims ==
        EXPECTED_DISTINCT_CLAIMS
    )

    print(
        f"Distinct claims: "
        f"{actual_claims} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # -----------------------------------------------------
    # 3. DISTINCT PATIENTS
    # -----------------------------------------------------

    actual_patients = df["PATIENT_ID"].nunique()

    passed = (
        actual_patients ==
        EXPECTED_DISTINCT_PATIENTS
    )

    print(
        f"Distinct patients: "
        f"{actual_patients} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # -----------------------------------------------------
    # 4. DISTINCT DIAGNOSIS CODES
    # -----------------------------------------------------

    actual_diagnosis_codes = (
        df["DIAGNOSIS_CODE"].nunique()
    )

    passed = (
        actual_diagnosis_codes ==
        EXPECTED_DISTINCT_DIAGNOSIS_CODES
    )

    print(
        f"Distinct diagnosis codes: "
        f"{actual_diagnosis_codes} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # -----------------------------------------------------
    # 5. SOURCE COUNTS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # 6. DATE RANGE
    # -----------------------------------------------------

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

    invalid_date_count = invalid_dates.sum()

    passed = invalid_date_count == 0

    print(
        f"\nInvalid service dates: "
        f"{invalid_date_count} "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )

    if not passed:
        all_passed = False

    # -----------------------------------------------------
    # 7. MISSING PATIENT IDs
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # 8. DUPLICATE CHECK
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # FINAL RESULT
    # -----------------------------------------------------

    print("\n" + "=" * 60)

    if all_passed:
        print("ALL VALIDATION CHECKS PASSED ✓")
    else:
        print("SOME VALIDATION CHECKS FAILED ✗")

    print("=" * 60)

    return all_passed