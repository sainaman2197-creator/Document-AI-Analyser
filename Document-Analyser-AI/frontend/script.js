const API_URL = "http://127.0.0.1:8000";

let selectedFile = null;
let documentImageURL = null;

const uploadArea = document.getElementById("uploadArea");
const fileInput = document.getElementById("fileInput");
const browseBtn = document.getElementById("browseBtn");

const filePreview = document.getElementById("filePreview");
const previewImage = document.getElementById("previewImage");
const previewFileName = document.getElementById("previewFileName");
const previewFileSize = document.getElementById("previewFileSize");

const analyzeBtn = document.getElementById("analyzeBtn");
const removeFileBtn = document.getElementById("removeFileBtn");

const loadingSection = document.getElementById("loadingSection");
const errorSection = document.getElementById("errorSection");
const errorMessage = document.getElementById("errorMessage");

const resultSection = document.getElementById("resultSection");

const resultDocumentPreview =
    document.getElementById("resultDocumentPreview");

const resultFileName =
    document.getElementById("resultFileName");

const resultFileSize =
    document.getElementById("resultFileSize");

const resultDocumentStatus =
    document.getElementById("resultDocumentStatus");

const documentType =
    document.getElementById("documentType");

const confidenceValue =
    document.getElementById("confidenceValue");

const summaryText =
    document.getElementById("summaryText");

const extractedFields =
    document.getElementById("extractedFields");

const extractedCount =
    document.getElementById("extractedCount");

const insightsList =
    document.getElementById("insightsList");

const findingsList =
    document.getElementById("findingsList");

const rawResponse =
    document.getElementById("rawResponse");

const copyResponseBtn =
    document.getElementById("copyResponseBtn");

const newDocumentBtn =
    document.getElementById("newDocumentBtn");


// ===============================
// FILE SELECTION
// ===============================

browseBtn?.addEventListener("click", () => {
    fileInput.click();
});

uploadArea?.addEventListener("click", (event) => {

    if (
        event.target === browseBtn ||
        browseBtn?.contains(event.target)
    ) {
        return;
    }

    fileInput.click();
});


fileInput?.addEventListener("change", (event) => {

    const file = event.target.files[0];

    if (file) {
        handleFile(file);
    }
});


// ===============================
// DRAG & DROP
// ===============================

uploadArea?.addEventListener("dragover", (event) => {

    event.preventDefault();

    uploadArea.classList.add("dragging");
});


uploadArea?.addEventListener("dragleave", () => {

    uploadArea.classList.remove("dragging");
});


uploadArea?.addEventListener("drop", (event) => {

    event.preventDefault();

    uploadArea.classList.remove("dragging");

    const file = event.dataTransfer.files[0];

    if (file) {
        handleFile(file);
    }
});


// ===============================
// HANDLE FILE
// ===============================

function handleFile(file) {

    selectedFile = file;

    hideError();

    if (documentImageURL) {
        URL.revokeObjectURL(documentImageURL);
    }

    documentImageURL = URL.createObjectURL(file);

    previewFileName.textContent = file.name;

    previewFileSize.textContent =
        formatFileSize(file.size);


    if (file.type.startsWith("image/")) {

        previewImage.src = documentImageURL;

        previewImage.style.display = "block";

    } else {

        previewImage.style.display = "none";
    }


    filePreview.style.display = "block";

    uploadArea.style.display = "none";
}


// ===============================
// REMOVE FILE
// ===============================

removeFileBtn?.addEventListener("click", resetApp);


// ===============================
// ANALYZE BUTTON
// ===============================

analyzeBtn?.addEventListener("click", analyzeDocument);


// ===============================
// ANALYZE DOCUMENT
// ===============================

async function analyzeDocument() {

    if (!selectedFile) {

        showError("Please select a document first.");

        return;
    }


    hideError();

    filePreview.style.display = "none";

    loadingSection.style.display = "block";

    analyzeBtn.disabled = true;


    try {

        const formData = new FormData();

        formData.append("file", selectedFile);


        const endpoints = [
            "/analyse",
            "/analyze",
            "/api/analyse",
            "/api/analyze",
            "/analyze-document",
            "/api/analyze-document"
        ];


        let response = null;
        let data = null;


        for (const endpoint of endpoints) {

            try {

                console.log("Trying endpoint:", endpoint);


                const res = await fetch(
                    API_URL + endpoint,
                    {
                        method: "POST",
                        body: formData
                    }
                );


                if (!res.ok) {
                    continue;
                }


                const json = await res.json();

                console.log(
                    "BACKEND RESPONSE:",
                    json
                );


                response = res;

                data = json;

                break;


            } catch (error) {

                console.log(
                    "Endpoint failed:",
                    endpoint,
                    error
                );
            }
        }


        if (!data) {

            throw new Error(
                "Could not connect to the document analysis API."
            );
        }


        console.log(
            "COMPLETE BACKEND RESPONSE:",
            data
        );


        displayResult(data);


    } catch (error) {

        console.error(
            "Analysis error:",
            error
        );


        showError(
            error.message ||
            "Failed to analyze the document."
        );


    } finally {

        loadingSection.style.display = "none";

        analyzeBtn.disabled = false;
    }
}


// ===============================
// DISPLAY RESULT
// ===============================

function displayResult(data) {

    console.log(
        "RAW API DATA:",
        data
    );


    /*
        IMPORTANT:

        Backend response is:

        {
            success: true,
            filename: "...",
            document_analysis: {
                document_type: "...",
                confidence: 0.98,
                fields: {...},
                raw_text: "..."
            }
        }

        Therefore we MUST use:

        data.document_analysis
    */


    const analysis =
        data.document_analysis ||
        data.analysis ||
        data;


    console.log(
        "ACTUAL DOCUMENT ANALYSIS:",
        analysis
    );


    // ===============================
    // DOCUMENT IMAGE
    // ===============================

    if (documentImageURL) {

        resultDocumentPreview.src =
            documentImageURL;

        resultDocumentPreview.style.display =
            "block";
    }


    // ===============================
    // FILE INFORMATION
    // ===============================

    resultFileName.textContent =
        data.filename ||
        selectedFile.name;


    resultFileSize.textContent =
        formatFileSize(selectedFile.size);


    resultDocumentStatus.textContent =
        "Analyzed";


    // ===============================
    // DOCUMENT TYPE
    // ===============================

    const type =
        analysis.document_type ||
        analysis.documentType ||
        "Unknown Document";


    documentType.textContent = type;


    // ===============================
    // CONFIDENCE
    // ===============================

    let confidence =
        analysis.confidence ?? 0;


    confidence = Number(confidence);


    if (confidence <= 1) {
        confidence *= 100;
    }


    confidenceValue.textContent =
        Math.round(confidence) + "%";


    // ===============================
    // FIELDS
    // ===============================

    const fields =
        analysis.fields || {};


    console.log(
        "EXTRACTED FIELDS:",
        fields
    );


    renderFields(fields);


    // ===============================
    // SUMMARY
    // ===============================

    const rawText =
        analysis.raw_text ||
        analysis.rawText ||
        "";


    if (rawText) {

        summaryText.textContent =
            rawText;

    } else {

        summaryText.textContent =
            `AI identified this document as ${type} and extracted ${Object.keys(fields).length} visible fields.`;
    }


    // ===============================
    // INSIGHTS
    // ===============================

    renderInsights(
        type,
        confidence,
        fields
    );


    // ===============================
    // FINDINGS
    // ===============================

    renderFindings(
        fields
    );


    // ===============================
    // RAW RESPONSE
    // ===============================

    if (rawResponse) {

        rawResponse.textContent =
            JSON.stringify(
                data,
                null,
                2
            );
    }


    // ===============================
    // SHOW RESULTS
    // ===============================

    resultSection.style.display =
        "block";


    resultSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


// ===============================
// RENDER EXTRACTED FIELDS
// ===============================

function renderFields(fields) {

    extractedFields.innerHTML = "";


    const entries =
        Object.entries(fields);


    const visibleFields =
        entries.filter(
            ([key, value]) =>
                value !== null &&
                value !== undefined &&
                String(value).trim() !== ""
        );


    extractedCount.textContent =
        visibleFields.length;


    if (entries.length === 0) {

        extractedFields.innerHTML = `
            <div class="empty-state">
                No extracted fields found.
            </div>
        `;

        return;
    }


    entries.forEach(
        ([key, value]) => {

            const card =
                document.createElement("div");


            card.className =
                "field-card";


            const label =
                formatFieldName(key);


            const displayValue =
                value === null ||
                value === undefined ||
                String(value).trim() === ""
                    ? "Not available"
                    : value;


            card.innerHTML = `
                <div class="field-label">
                    ${escapeHTML(label)}
                </div>

                <div class="field-value">
                    ${escapeHTML(String(displayValue))}
                </div>
            `;


            extractedFields.appendChild(card);
        }
    );
}


// ===============================
// INSIGHTS
// ===============================

function renderInsights(
    type,
    confidence,
    fields
) {

    insightsList.innerHTML = "";


    const insights = [];


    if (confidence >= 90) {

        insights.push(
            `High-confidence ${type} identification (${Math.round(confidence)}%).`
        );

    } else if (confidence >= 70) {

        insights.push(
            `The document was identified with moderate confidence (${Math.round(confidence)}%).`
        );

    } else {

        insights.push(
            `The document identification has low confidence (${Math.round(confidence)}%).`
        );
    }


    const count =
        Object.values(fields)
            .filter(
                value =>
                    value !== null &&
                    value !== undefined &&
                    String(value).trim() !== ""
            )
            .length;


    insights.push(
        `${count} visible field${count === 1 ? "" : "s"} were extracted from the document.`
    );


    if (fields.name) {

        insights.push(
            "A person's name was successfully detected."
        );
    }


    if (fields.date_of_birth) {

        insights.push(
            "Date of birth information was detected."
        );
    }


    if (fields.address) {

        insights.push(
            "Address information was detected."
        );
    }


    insights.forEach(
        insight => {

            const li =
                document.createElement("li");

            li.textContent =
                insight;

            insightsList.appendChild(li);
        }
    );
}


// ===============================
// FINDINGS
// ===============================

function renderFindings(fields) {

    findingsList.innerHTML = "";


    const missingFields =
        Object.entries(fields)
            .filter(
                ([key, value]) =>
                    value === null ||
                    value === undefined ||
                    String(value).trim() === ""
            )
            .map(
                ([key]) =>
                    formatFieldName(key)
            );


    if (missingFields.length === 0) {

        const li =
            document.createElement("li");

        li.textContent =
            "All requested fields were successfully detected.";

        findingsList.appendChild(li);

        return;
    }


    missingFields.forEach(
        field => {

            const li =
                document.createElement("li");

            li.textContent =
                `${field} was not clearly visible or available.`;

            findingsList.appendChild(li);
        }
    );
}


// ===============================
// COPY RESPONSE
// ===============================

copyResponseBtn?.addEventListener(
    "click",
    async () => {

        if (!rawResponse) return;


        try {

            await navigator.clipboard.writeText(
                rawResponse.textContent
            );


            const originalText =
                copyResponseBtn.textContent;


            copyResponseBtn.textContent =
                "✓ Copied";


            setTimeout(() => {

                copyResponseBtn.textContent =
                    originalText;

            }, 1500);


        } catch (error) {

            console.error(
                "Copy failed:",
                error
            );
        }
    }
);


// ===============================
// NEW DOCUMENT
// ===============================

newDocumentBtn?.addEventListener(
    "click",
    resetApp
);


function resetApp() {

    selectedFile = null;


    if (documentImageURL) {

        URL.revokeObjectURL(
            documentImageURL
        );

        documentImageURL = null;
    }


    fileInput.value = "";


    filePreview.style.display =
        "none";


    uploadArea.style.display =
        "block";


    loadingSection.style.display =
        "none";


    resultSection.style.display =
        "none";


    hideError();


    previewImage.src = "";


    resultDocumentPreview.src = "";


    if (extractedFields) {

        extractedFields.innerHTML =
            "";
    }


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


// ===============================
// ERROR
// ===============================

function showError(message) {

    errorMessage.textContent =
        message;


    errorSection.style.display =
        "block";
}


function hideError() {

    errorSection.style.display =
        "none";
}


// ===============================
// FORMAT FILE SIZE
// ===============================

function formatFileSize(bytes) {

    if (!bytes) {
        return "0 KB";
    }


    const units = [
        "Bytes",
        "KB",
        "MB",
        "GB"
    ];


    const index =
        Math.floor(
            Math.log(bytes) /
            Math.log(1024)
        );


    return (
        parseFloat(
            (
                bytes /
                Math.pow(1024, index)
            ).toFixed(2)
        ) +
        " " +
        units[index]
    );
}


// ===============================
// FORMAT FIELD NAME
// ===============================

function formatFieldName(key) {

    return key
        .replace(/_/g, " ")
        .replace(/\b\w/g, char =>
            char.toUpperCase()
        );
}


// ===============================
// ESCAPE HTML
// ===============================

function escapeHTML(value) {

    return value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}