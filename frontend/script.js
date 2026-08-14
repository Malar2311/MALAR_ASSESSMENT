const API_BASE = "http://127.0.0.1:8000";


// =========================================================
// CHECK API
// =========================================================

async function checkAPI() {

    try {

        const response = await fetch(
            `${API_BASE}/`
        );

        if (!response.ok) {

            throw new Error(
                "API unavailable"
            );
        }

        await response.json();

        document.getElementById(
            "statusDot"
        ).style.background = "#22c55e";

        document.getElementById(
            "statusText"
        ).textContent =
            "API Connected";

    } catch (error) {

        document.getElementById(
            "statusDot"
        ).style.background = "#ef4444";

        document.getElementById(
            "statusText"
        ).textContent =
            "API Offline";
    }
}


// =========================================================
// LOAD SUMMARY
// =========================================================

async function loadSummary() {

    try {

        const response = await fetch(
            `${API_BASE}/summary`
        );

        if (!response.ok) {

            throw new Error(
                "Summary unavailable"
            );
        }

        const data =
            await response.json();


        // -----------------------------------------------
        // SUMMARY CARDS
        // -----------------------------------------------

        document.getElementById(
            "totalRows"
        ).textContent =
            data.total_rows.toLocaleString();


        document.getElementById(
            "claims"
        ).textContent =
            data.distinct_claims.toLocaleString();


        document.getElementById(
            "patients"
        ).textContent =
            data.distinct_patients.toLocaleString();


        document.getElementById(
            "diagnosisCodes"
        ).textContent =
            data.distinct_diagnosis_codes.toLocaleString();


        // -----------------------------------------------
        // SOURCE COUNTS
        // -----------------------------------------------

        const sourceA =
            data.source_counts.A || 0;

        const sourceB =
            data.source_counts.B || 0;

        const sourceC =
            data.source_counts.C || 0;


        document.getElementById(
            "sourceA"
        ).textContent =
            sourceA.toLocaleString();


        document.getElementById(
            "sourceB"
        ).textContent =
            sourceB.toLocaleString();


        document.getElementById(
            "sourceC"
        ).textContent =
            sourceC.toLocaleString();


        // -----------------------------------------------
        // PROGRESS BARS
        // -----------------------------------------------

        const total =
            data.total_rows;


        if (total > 0) {

            document.getElementById(
                "barA"
            ).style.width =
                `${(sourceA / total) * 100}%`;


            document.getElementById(
                "barB"
            ).style.width =
                `${(sourceB / total) * 100}%`;


            document.getElementById(
                "barC"
            ).style.width =
                `${(sourceC / total) * 100}%`;
        }


    } catch (error) {

        console.error(
            "Failed to load summary:",
            error
        );
    }
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
        "Running Pipeline...";


    try {

        const response =
            await fetch(
                `${API_BASE}/run`,
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


        // -----------------------------------------------
        // SHOW RESULT
        // -----------------------------------------------

        const resultPanel =
            document.getElementById(
                "resultPanel"
            );

        const runResult =
            document.getElementById(
                "runResult"
            );


        resultPanel.classList.remove(
            "hidden"
        );


        let html = "";


        html += `
            <div class="result-item">
                <strong>Run ID:</strong>
                ${data.run_id}
            </div>
        `;


        html += `
            <div class="result-item">
                <strong>Status:</strong>
                ${data.status}
            </div>
        `;


        html += `
            <div class="result-item">
                <strong>Rows:</strong>
                ${data.rows.toLocaleString()}
            </div>
        `;


        html += `
            <div class="result-item">
                <strong>Output:</strong>
                ${data.output_file}
            </div>
        `;


        html += `
            <div class="result-item">
                <strong>Stages:</strong>
            </div>
        `;


        data.stages.forEach(
            stage => {

                html += `
                    <div class="result-item">
                        ✓
                        ${stage.stage}
                        —
                        ${stage.status}
                    </div>
                `;
            }
        );


        runResult.innerHTML =
            html;


        // -----------------------------------------------
        // REFRESH SUMMARY
        // -----------------------------------------------

        await loadSummary();


    } catch (error) {

        alert(
            "Pipeline error: " +
            error.message
        );

    } finally {

        button.disabled = false;

        button.textContent =
            "Run Pipeline";
    }
}


// =========================================================
// DOWNLOAD FINAL CSV
// =========================================================

function downloadCSV() {

    window.open(
        `${API_BASE}/download`,
        "_blank"
    );
}


// =========================================================
// INITIALIZE
// =========================================================

checkAPI();

loadSummary();