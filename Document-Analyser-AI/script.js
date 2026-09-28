const API_BASE = "http://127.0.0.1:8000";

const fileInput = document.getElementById("fileInput");
const chooseButton = document.getElementById("chooseButton");
const changeButton = document.getElementById("changeButton");

const uploadSection = document.getElementById("uploadSection");
const previewSection = document.getElementById("previewSection");
const loadingSection = document.getElementById("loadingSection");
const resultSection = document.getElementById("resultSection");
const errorSection = document.getElementById("errorSection");

const previewBox = document.getElementById("previewBox");
const selectedFileName = document.getElementById("selectedFileName");
const selectedFileSize = document.getElementById("selectedFileSize");

const analyzeButton = document.getElementById("analyzeButton");
const loadingText = document.getElementById("loadingText");

const resultDocumentPreview =
    document.getElementById("resultDocumentPreview");

const resultFileName =
    document.getElementById("resultFileName");

const resultFileSize =
    document.getElementById("resultFileSize");

const documentType =
    document.getElementById("documentType");

const confidenceValue =
    document.getElementById("confidenceValue");

const confidenceBar =
    document.getElementById("confidenceBar");

const summaryText =
    document.getElementById("summaryText");

const extractedData =
    document.getElementById("extractedData");

const fieldsCount =
    document.getElementById("fieldsCount");

const insightsList =
    document.getElementById("insightsList");

const findingsList =
    document.getElementById("findingsList");

const rawResult =
    document.getElementById("rawResult");

const newDocumentButton =
    document.getElementById("newDocumentButton");

const copyButton =
    document.getElementById("copyButton");

const retryButton =
    document.getElementById("retryButton");

const errorMessage =
    document.getElementById("errorMessage");


let selectedFile = null;
let documentImageURL = null;
let latestAnalysis = null;


/* =========================================================
   FILE BUTTONS
========================================================= */

chooseButton.addEventListener("click", () => {
    fileInput.click();
});

changeButton.addEventListener("click", () => {
    fileInput.click();
});

fileInput.addEventListener("change", (event) => {

    const file = event.target.files[0];

    if (file) {
        handleFile(file);
    }

});


/* =========================================================
   DRAG AND DROP
========================================================= */

uploadSection.addEventListener("dragover", (event) => {

    event.preventDefault();

    uploadSection.classList.add("dragging");

});


uploadSection.addEventListener("dragleave", () => {

    uploadSection.classList.remove("dragging");

});


uploadSection.addEventListener("drop", (event) => {

    event.preventDefault();

    uploadSection.classList.remove("dragging");

    const file = event.dataTransfer.files[0];

    if (file) {
        handleFile(file);
    }

});


/* =========================================================
   FILE HANDLER
========================================================= */

function handleFile(file) {

    const allowedTypes = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf"
    ];

    if (!allowedTypes.includes(file.type)) {

        showError(
            "Please upload JPG, PNG, WEBP or PDF."
        );

        return;
    }


    if (file.size > 10 * 1024 * 1024) {

        showError(
            "File size must be less than 10 MB."
        );

        return;
    }


    selectedFile = file;


    if (documentImageURL) {

        URL.revokeObjectURL(
            documentImageURL
        );

    }


    documentImageURL =
        URL.createObjectURL(file);


    selectedFileName.textContent =
        file.name;

    selectedFileSize.textContent =
        formatFileSize(file.size);


    showSelectedPreview();


    uploadSection.classList.add("hidden");

    previewSection.classList.remove("hidden");

    resultSection.classList.add("hidden");

    errorSection.classList.add("hidden");

}


/* =========================================================
   SELECTED PREVIEW
========================================================= */

function showSelectedPreview() {

    previewBox.innerHTML = "";


    if (
        selectedFile &&
        selectedFile.type.startsWith("image/")
    ) {

        const image =
            document.createElement("img");

        image.src =
            documentImageURL;

        image.alt =
            "Selected document";


        previewBox.appendChild(image);

    } else {

        const iframe =
            document.createElement("iframe");

        iframe.src =
            documentImageURL;

        iframe.title =
            "PDF document preview";


        previewBox.appendChild(iframe);

    }

}


/* =========================================================
   ANALYZE BUTTON
========================================================= */

analyzeButton.addEventListener("click", async () => {

    if (!selectedFile) {

        showError(
            "Please select a document first."
        );

        return;
    }


    uploadSection.classList.add("hidden");

    previewSection.classList.add("hidden");

    resultSection.classList.add("hidden");

    errorSection.classList.add("hidden");

    loadingSection.classList.remove("hidden");


    const messages = [
        "Reading document...",
        "Detecting document type...",
        "Extracting document fields...",
        "Analyzing visible information...",
        "Preparing AI result..."
    ];


    let index = 0;

    loadingText.textContent =
        messages[0];


    const timer = setInterval(() => {

        index++;

        if (index < messages.length) {

            loadingText.textContent =
                messages[index];

        }

    }, 1000);


    try {

        const data =
            await analyzeDocument(
                selectedFile
            );


        clearInterval(timer);


        console.log(
            "FINAL BACKEND RESPONSE:",
            data
        );


        latestAnalysis = data;


        loadingSection.classList.add("hidden");


        displayResult(data);

    } catch (error) {

        clearInterval(timer);

        console.error(error);

        loadingSection.classList.add("hidden");

        showError(
            error.message ||
            "Document analysis failed."
        );

    }

});


/* =========================================================
   BACKEND REQUEST
========================================================= */

async function analyzeDocument(file) {

    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );


    const endpoints = [
        "/analyse",
        "/analyze",
        "/api/analyse",
        "/api/analyze",
        "/analyze-document",
        "/api/analyze-document"
    ];


    let lastError =
        null;


    for (const endpoint of endpoints) {

        try {

            console.log(
                "Trying:",
                endpoint
            );


            const response =
                await fetch(
                    API_BASE + endpoint,
                    {
                        method: "POST",
                        body: formData
                    }
                );


            if (response.status === 404) {

                continue;

            }


            const contentType =
                response.headers.get(
                    "content-type"
                ) || "";


            let data;


            if (
                contentType.includes(
                    "application/json"
                )
            ) {

                data =
                    await response.json();

            } else {

                const text =
                    await response.text();


                try {

                    data =
                        JSON.parse(text);

                } catch {

                    data = {
                        raw_text: text
                    };

                }

            }


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    data.message ||
                    data.error ||
                    `Server error ${response.status}`
                );

            }


            return data;

        } catch (error) {

            console.warn(
                endpoint,
                error
            );

            lastError =
                error;

        }

    }


    throw new Error(
        lastError?.message ||
        "Cannot connect to backend."
    );

}


/* =========================================================
   DISPLAY RESULT
========================================================= */

function displayResult(data) {

    console.log(
        "Displaying result:",
        data
    );


    resultSection.classList.remove(
        "hidden"
    );


    /* =====================================================
       DOCUMENT PHOTO
    ===================================================== */

    resultDocumentPreview.innerHTML =
        "";


    if (
        selectedFile &&
        selectedFile.type.startsWith("image/")
    ) {

        const image =
            document.createElement("img");


        image.src =
            documentImageURL;


        image.alt =
            "Uploaded document";


        image.className =
            "result-document-image";


        resultDocumentPreview.appendChild(
            image
        );


    } else if (
        selectedFile &&
        selectedFile.type ===
        "application/pdf"
    ) {

        const iframe =
            document.createElement("iframe");


        iframe.src =
            documentImageURL;


        iframe.className =
            "pdf-viewer";


        resultDocumentPreview.appendChild(
            iframe
        );

    }


    /* FILE INFORMATION */

    resultFileName.textContent =
        selectedFile?.name ||
        "Document";


    resultFileSize.textContent =
        selectedFile
            ? formatFileSize(
                selectedFile.size
            )
            : "Unknown";


    /* =====================================================
       DOCUMENT TYPE
    ===================================================== */

    const type =
        data.document_type ||
        data.documentType ||
        "Unknown Document";


    documentType.textContent =
        type;


    /* =====================================================
       CONFIDENCE
    ===================================================== */

    let confidence =
        data.confidence ?? 0;


    confidence =
        Number(confidence);


    if (confidence <= 1) {

        confidence =
            confidence * 100;

    }


    confidence =
        Math.round(
            Math.max(
                0,
                Math.min(
                    100,
                    confidence
                )
            )
        );


    confidenceValue.textContent =
        confidence + "%";


    setTimeout(() => {

        confidenceBar.style.width =
            confidence + "%";

    }, 100);


    /* =====================================================
       IMPORTANT:
       YOUR BACKEND RETURNS "fields"
    ===================================================== */

    const fields =
        data.fields || {};


    console.log(
        "EXTRACTED FIELDS:",
        fields
    );


    renderFields(
        fields
    );


    /* =====================================================
       RAW TEXT
    ===================================================== */

    const rawText =
        data.raw_text ||
        data.rawText ||
        "";


    if (rawText) {

        summaryText.textContent =
            rawText;

    } else {

        summaryText.textContent =
            `AI identified this document as ${type} and extracted ${Object.keys(fields).length} visible fields.`;

    }


    /* =====================================================
       INSIGHTS
    ===================================================== */

    renderInsights(
        type,
        fields
    );


    /* =====================================================
       FINDINGS
    ===================================================== */

    renderFindings(
        fields
    );


    /* =====================================================
       RAW JSON
    ===================================================== */

    rawResult.textContent =
        JSON.stringify(
            data,
            null,
            2
        );


    /* Scroll */

    resultSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


/* =========================================================
   RENDER FIELDS
========================================================= */

function renderFields(fields) {

    extractedData.innerHTML =
        "";


    const entries =
        Object.entries(fields);


    fieldsCount.textContent =
        entries.length;


    if (entries.length === 0) {

        extractedData.innerHTML = `
            <div class="data-item">
                <span class="data-value">
                    No visible document fields were extracted.
                </span>
            </div>
        `;

        return;
    }


    entries.forEach(
        ([key, value]) => {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "data-item";


            const keyElement =
                document.createElement(
                    "span"
                );


            keyElement.className =
                "data-key";


            keyElement.textContent =
                formatKey(key);


            const valueElement =
                document.createElement(
                    "span"
                );


            valueElement.className =
                "data-value";


            if (
                value === null ||
                value === undefined ||
                value === ""
            ) {

                valueElement.textContent =
                    "Not visible";

                valueElement.style.color =
                    "#64748b";

            } else {

                valueElement.textContent =
                    formatValue(value);

            }


            item.appendChild(
                keyElement
            );


            item.appendChild(
                valueElement
            );


            extractedData.appendChild(
                item
            );

        }
    );

}


/* =========================================================
   AI INSIGHTS
========================================================= */

function renderInsights(
    type,
    fields
) {

    insightsList.innerHTML =
        "";


    const entries =
        Object.entries(fields);


    const visibleFields =
        entries.filter(
            ([, value]) =>
                value !== null &&
                value !== undefined &&
                value !== ""
        );


    const messages = [];


    messages.push(
        `The document was classified as ${type}.`
    );


    messages.push(
        `${visibleFields.length} visible field(s) were successfully detected.`
    );


    if (
        fields.document_number
    ) {

        messages.push(
            "A document number was detected."
        );

    }


    if (
        fields.name
    ) {

        messages.push(
            "A person's name was detected."
        );

    }


    if (
        fields.date_of_birth
    ) {

        messages.push(
            "Date of birth information was detected."
        );

    }


    messages.forEach(
        message => {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "insight-item";


            item.textContent =
                message;


            insightsList.appendChild(
                item
            );

        }
    );

}


/* =========================================================
   FINDINGS
========================================================= */

function renderFindings(fields) {

    findingsList.innerHTML =
        "";


    const entries =
        Object.entries(fields);


    const visible =
        entries.filter(
            ([, value]) =>
                value !== null &&
                value !== undefined &&
                value !== ""
        );


    if (visible.length === 0) {

        const item =
            document.createElement(
                "div"
            );


        item.className =
            "finding-item";


        item.textContent =
            "No additional findings available.";


        findingsList.appendChild(
            item
        );


        return;

    }


    visible.forEach(
        ([key, value]) => {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "finding-item";


            item.textContent =
                `${formatKey(key)}: ${formatValue(value)}`;


            findingsList.appendChild(
                item
            );

        }
    );

}


/* =========================================================
   NEW DOCUMENT
========================================================= */

newDocumentButton.addEventListener(
    "click",
    resetApplication
);


function resetApplication() {

    selectedFile =
        null;


    latestAnalysis =
        null;


    fileInput.value =
        "";


    if (documentImageURL) {

        URL.revokeObjectURL(
            documentImageURL
        );

        documentImageURL =
            null;

    }


    previewBox.innerHTML =
        "";


    resultDocumentPreview.innerHTML =
        "";


    extractedData.innerHTML =
        "";


    insightsList.innerHTML =
        "";


    findingsList.innerHTML =
        "";


    rawResult.textContent =
        "";


    confidenceBar.style.width =
        "0%";


    resultSection.classList.add(
        "hidden"
    );


    previewSection.classList.add(
        "hidden"
    );


    loadingSection.classList.add(
        "hidden"
    );


    errorSection.classList.add(
        "hidden"
    );


    uploadSection.classList.remove(
        "hidden"
    );


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });

}


/* =========================================================
   COPY
========================================================= */

copyButton.addEventListener(
    "click",
    async () => {

        const text = `
DocuMind AI Analysis

Document Type:
${documentType.textContent}

Confidence:
${confidenceValue.textContent}

Extracted Information:
${extractedData.innerText}

Summary:
${summaryText.textContent}

AI Insights:
${insightsList.innerText}

Important Findings:
${findingsList.innerText}
        `.trim();


        try {

            await navigator.clipboard.writeText(
                text
            );


            const oldText =
                copyButton.textContent;


            copyButton.textContent =
                "✓ Analysis Copied";


            setTimeout(() => {

                copyButton.textContent =
                    oldText;

            }, 2000);

        } catch {

            alert(
                "Could not copy analysis."
            );

        }

    }
);


/* =========================================================
   RETRY
========================================================= */

retryButton.addEventListener(
    "click",
    () => {

        errorSection.classList.add(
            "hidden"
        );


        if (selectedFile) {

            previewSection.classList.remove(
                "hidden"
            );

        } else {

            uploadSection.classList.remove(
                "hidden"
            );

        }

    }
);


/* =========================================================
   ERROR
========================================================= */

function showError(message) {

    uploadSection.classList.add(
        "hidden"
    );

    previewSection.classList.add(
        "hidden"
    );

    loadingSection.classList.add(
        "hidden"
    );

    resultSection.classList.add(
        "hidden"
    );

    errorSection.classList.remove(
        "hidden"
    );


    errorMessage.textContent =
        message;

}


/* =========================================================
   HELPERS
========================================================= */

function formatKey(key) {

    return String(key)
        .replace(/_/g, " ")
        .replace(
            /([A-Z])/g,
            " $1"
        )
        .replace(
            /\s+/g,
            " "
        )
        .trim()
        .replace(
            /\b\w/g,
            char =>
                char.toUpperCase()
        );

}


function formatValue(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "Not visible";

    }


    if (
        typeof value === "object"
    ) {

        return JSON.stringify(
            value
        );

    }


    return String(value);

}


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
                Math.pow(
                    1024,
                    index
                )
            ).toFixed(2)
        )
        + " "
        + units[index]
    );

}


console.log(
    "%cDocuMind AI ready",
    "color:#a78bfa;font-size:18px;font-weight:bold"
);
