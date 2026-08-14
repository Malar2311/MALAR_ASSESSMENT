const API_URL = "http://127.0.0.1:8000";


// =========================================================
// API STATUS
// =========================================================

async function checkAPI() {

    const statusText =
        document.getElementById("statusText");

    const statusDot =
        document.getElementById("statusDot");

    try {

        const response = await fetch(
            `${API_URL}/`
        );

        if (!response.ok) {
            throw new Error("API unavailable");
        }

        statusText.textContent =
            "API Connected";

        statusDot.classList.add(
            "online"
        );

    } catch (error) {

        statusText.textContent =
            "API Offline";

        statusDot.classList.remove(
            "online"
        );
    }
}


// =========================================================
// LOAD SUMMARY
// =========================================================

async function loadSummary() {

    try {

        const response = await fetch(
            `${API_URL}/summary`
        );

        if (!response.ok) {
            return;
        }

        const data =
            await response.json();

        document.getElementById(
            "totalRows"
        ).textContent =
            Number(
                data.total_rows
            ).toLocaleString();

        document.getElementById(
            "claims"
        ).textContent =
            Number(
                data.distinct_claims
            ).toLocaleString();

        document.getElementById(
            "patients"
        ).textContent =
            Number(
                data.distinct_patients
            ).toLocaleString();

        document.getElementById(
            "diagnosisCodes"
        ).textContent =
            Number(
                data.distinct_diagnosis_codes
            ).toLocaleString();


        const sourceCounts =
            data.source_counts || {};

        const total =
            Number(
                data.total_rows
            );


        updateSource(
            "A",
            sourceCounts["A"] || 0,
            total
        );

        updateSource(
            "B",
            sourceCounts["B"] || 0,
            total
        );

        updateSource(
            "C",
            sourceCounts["C"] || 0,
            total
        );


    } catch (error) {

        console.error(
            "Summary error:",
            error
        );
    }
}


// =========================================================
// SOURCE DISPLAY
// =========================================================

function updateSource(
    source,
    value,
    total
) {

    const numberElement =
        document.getElementById(
            `source${source}`
        );

    const barElement =
        document.getElementById(
            `bar${source}`
        );

    numberElement.textContent =
        Number(
            value
        ).toLocaleString();

    let percentage = 0;

    if (total > 0) {

        percentage =
            (
                Number(value)
                / Number(total)
            ) * 100;
    }

    barElement.style.width =
        `${percentage}%`;
}


// =========================================================
// RUN PIPELINE
// =========================================================

async function runPipeline() {

    const button =
        document.getElementById(
            "runButton"
        );

    button.disabled = true;

    button.textContent =
        "Running...";


    try {

        const response = await fetch(
            `${API_URL}/run`,
            {
                method: "POST"
            }
        );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Pipeline failed"
            );
        }


        // -------------------------------------------------
        // DISPLAY RESULT
        // -------------------------------------------------

        displayRunResult(
            data
        );


        // -------------------------------------------------
        // STAGES
        // -------------------------------------------------

        displayStages(
            data.stages
        );


        // -------------------------------------------------
        // STAGE REPORT
        // -------------------------------------------------

        displayStageReport(
            data.pipeline_report
        );


        // -------------------------------------------------
        // SUMMARY
        // -------------------------------------------------

        await loadSummary();


        // -------------------------------------------------
        // VALIDATION
        // -------------------------------------------------

        await loadValidation(
            data.run_id
        );


        // -------------------------------------------------
        // REPRODUCIBILITY
        // -------------------------------------------------

        displayReproducibility(
            data.reproducibility
        );


    } catch (error) {

        alert(
            error.message
        );

        console.error(
            error
        );

    } finally {

        button.disabled = false;

        button.textContent =
            "Run Pipeline";
    }
}


// =========================================================
// DISPLAY RUN RESULT
// =========================================================

function displayRunResult(
    data
) {

    const panel =
        document.getElementById(
            "resultPanel"
        );

    const result =
        document.getElementById(
            "runResult"
        );

    panel.classList.remove(
        "hidden"
    );

    result.innerHTML = `

        <div class="run-grid">

            <div>
                <strong>Run ID</strong>
                <span>
                    ${data.run_id}
                </span>
            </div>

            <div>
                <strong>Status</strong>
                <span>
                    ${data.status}
                </span>
            </div>

            <div>
                <strong>Rows</strong>
                <span>
                    ${Number(
                        data.rows
                    ).toLocaleString()}
                </span>
            </div>

            <div>
                <strong>Started</strong>
                <span>
                    ${data.started_at}
                </span>
            </div>

            <div>
                <strong>Completed</strong>
                <span>
                    ${data.completed_at}
                </span>
            </div>

        </div>
    `;
}


// =========================================================
// PIPELINE STAGES
// =========================================================

function displayStages(
    stages
) {

    const container =
        document.getElementById(
            "pipelineStages"
        );

    const stageNames = {

        ingestion:
            "Ingestion",

        combination:
            "Combination",

        cleaning:
            "Cleaning",

        dictionary_lookup:
            "Dictionary Lookup",

        validation:
            "Validation",

        export:
            "Export"
    };


    container.innerHTML = "";


    stages.forEach(
        stage => {

            const item =
                document.createElement(
                    "div"
                );

            item.className =
                "pipeline-item";


            const icon =
                stage.status === "completed"
                    ? "✓"
                    : "✗";


            item.innerHTML = `

                <span class="stage-icon ${
                    stage.status === "completed"
                        ? "completed"
                        : "failed"
                }">

                    ${icon}

                </span>

                <span>
                    ${
                        stageNames[
                            stage.stage
                        ] ||
                        stage.stage
                    }
                </span>

            `;

            container.appendChild(
                item
            );
        }
    );
}


// =========================================================
// STAGE REPORT
// =========================================================

function displayStageReport(
    report
) {

    const body =
        document.getElementById(
            "stageReportBody"
        );


    body.innerHTML = "";


    if (!report) {

        body.innerHTML = `

            <tr>

                <td colspan="5">
                    No stage report available.
                </td>

            </tr>

        `;

        return;
    }


    const stages = [

        [
            "ingestion",
            "Ingestion"
        ],

        [
            "combination",
            "Combination"
        ],

        [
            "cleaning",
            "Cleaning"
        ],

        [
            "dictionary",
            "Dictionary Lookup"
        ],

        [
            "validation",
            "Validation"
        ],

        [
            "export",
            "Export"
        ]

    ];


    stages.forEach(
        ([key, name]) => {

            const stage =
                report[key];


            if (!stage) {
                return;
            }


            const row =
                document.createElement(
                    "tr"
                );


            row.innerHTML = `

                <td>
                    <strong>
                        ${name}
                    </strong>
                </td>

                <td>
                    ${Number(
                        stage.input_rows
                    ).toLocaleString()}
                </td>

                <td>
                    ${Number(
                        stage.output_rows
                    ).toLocaleString()}
                </td>

                <td>
                    ${Number(
                        stage.dropped
                    ).toLocaleString()}
                </td>

                <td class="reason">
                    ${stage.reason}
                </td>

            `;


            body.appendChild(
                row
            );
        }
    );
}


// =========================================================
// VALIDATION
// =========================================================

async function loadValidation(
    runId
) {

    try {

        const response =
            await fetch(
                `${API_URL}/run/${runId}/validate`
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Validation failed"
            );
        }


        displayValidation(
            data.validation
        );


    } catch (error) {

        console.error(
            "Validation error:",
            error
        );
    }
}


// =========================================================
// DISPLAY VALIDATION
// =========================================================

function displayValidation(
    validation
) {

    const list =
        document.getElementById(
            "validationList"
        );

    const overall =
        document.getElementById(
            "validationOverall"
        );


    list.innerHTML = "";


    if (!validation) {

        overall.textContent =
            "Not Run";

        return;
    }


    const checks = [];


    // -----------------------------------------------------
    // COUNTS
    // -----------------------------------------------------

    checks.push({

        name:
            "Total Rows",

        actual:
            validation.total_rows.actual,

        expected:
            validation.total_rows.expected,

        passed:
            validation.total_rows.passed
    });


    checks.push({

        name:
            "Distinct Claims",

        actual:
            validation.distinct_claims.actual,

        expected:
            validation.distinct_claims.expected,

        passed:
            validation.distinct_claims.passed
    });


    checks.push({

        name:
            "Distinct Patients",

        actual:
            validation.distinct_patients.actual,

        expected:
            validation.distinct_patients.expected,

        passed:
            validation.distinct_patients.passed
    });


    checks.push({

        name:
            "Distinct Diagnosis Codes",

        actual:
            validation.distinct_diagnosis_codes.actual,

        expected:
            validation.distinct_diagnosis_codes.expected,

        passed:
            validation.distinct_diagnosis_codes.passed
    });


    // -----------------------------------------------------
    // SOURCE COUNTS
    // -----------------------------------------------------

    checks.push({

        name:
            "Source Counts",

        actual:
            JSON.stringify(
                validation
                    .source_counts
                    .actual
            ),

        expected:
            JSON.stringify(
                validation
                    .source_counts
                    .expected
            ),

        passed:
            validation
                .source_counts
                .passed
    });


    // -----------------------------------------------------
    // P00042
    // -----------------------------------------------------

    checks.push({

        name:
            "P00042 Total Rows",

        actual:
            validation
                .p00042
                .total_rows,

        expected:
            validation
                .p00042
                .expected_rows,

        passed:
            validation
                .p00042
                .rows_passed
    });


    checks.push({

        name:
            "P00042 Diagnosis Codes",

        actual:
            validation
                .p00042
                .distinct_diagnosis_codes,

        expected:
            validation
                .p00042
                .expected_diagnosis_codes,

        passed:
            validation
                .p00042
                .diagnosis_codes_passed
    });


    // -----------------------------------------------------
    // QUALITY
    // -----------------------------------------------------

    checks.push({

        name:
            "Diagnosis Code Format",

        actual:
            validation
                .diagnosis_code_format
                .invalid_code_count,

        expected:
            0,

        passed:
            validation
                .diagnosis_code_format
                .passed
    });


    checks.push({

        name:
            "Missing Patient IDs",

        actual:
            validation
                .missing_patient_ids
                .count,

        expected:
            0,

        passed:
            validation
                .missing_patient_ids
                .passed
    });


    checks.push({

        name:
            "Invalid Service Dates",

        actual:
            validation
                .invalid_service_dates
                .count,

        expected:
            0,

        passed:
            validation
                .invalid_service_dates
                .passed
    });


    checks.push({

        name:
            "Duplicate Rows",

        actual:
            validation
                .duplicate_rows
                .count,

        expected:
            0,

        passed:
            validation
                .duplicate_rows
                .passed
    });


    // -----------------------------------------------------
    // RENDER
    // -----------------------------------------------------

    checks.forEach(
        check => {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "validation-item";


            item.innerHTML = `

                <div class="validation-name">

                    <span class="check-icon ${
                        check.passed
                            ? "pass"
                            : "fail"
                    }">

                        ${
                            check.passed
                                ? "✓"
                                : "✗"
                        }

                    </span>

                    <strong>
                        ${check.name}
                    </strong>

                </div>


                <div class="validation-values">

                    <span>
                        Actual:
                        <strong>
                            ${check.actual}
                        </strong>
                    </span>

                    <span>
                        Expected:
                        <strong>
                            ${check.expected}
                        </strong>
                    </span>

                </div>

            `;


            list.appendChild(
                item
            );
        }
    );


    if (
        validation.all_checks_passed
    ) {

        overall.textContent =
            "ALL PASSED";

        overall.className =
            "validation-badge success";

    } else {

        overall.textContent =
            "FAILED";

        overall.className =
            "validation-badge failed";
    }
}


// =========================================================
// REPRODUCIBILITY
// =========================================================

function displayReproducibility(
    data
) {

    const element =
        document.getElementById(
            "reproducibility"
        );


    if (!data) {

        element.innerHTML =
            "Run the pipeline again to compare outputs.";

        return;
    }


    if (
        data.identical_to_previous_run
    ) {

        element.innerHTML = `

            <div class="repro-success">

                ✓ Consecutive runs produced
                identical output.

                <br>

                SHA-256:
                <code>
                    ${data.current_file_hash}
                </code>

            </div>

        `;

    } else {

        element.innerHTML = `

            <div class="repro-info">

                First run completed.

                <br>

                Run the pipeline again to
                check whether the output is identical.

                <br><br>

                SHA-256:
                <code>
                    ${data.current_file_hash}
                </code>

            </div>

        `;
    }
}


// =========================================================
// DOWNLOAD
// =========================================================

function downloadCSV() {

    window.location.href =
        `${API_URL}/download`;
}


// =========================================================
// INITIAL LOAD
// =========================================================

window.addEventListener(
    "load",
    async () => {

        await checkAPI();

        await loadSummary();

    }
);