import os

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.services.gemini_vision import analyze_document


app = FastAPI(
    title="AI Document Analyser",
    description="AI-powered document analysis using Gemini Vision",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}


ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp"
}


@app.get("/")
def root():
    return {
        "message": "AI Document Analyser is running",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):

    extension = os.path.splitext(
        file.filename or ""
    )[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, JPEG, PNG and WEBP images are supported"
        )

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid image type"
        )

    image_bytes = await file.read()

    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    if len(image_bytes) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File size must be less than {settings.MAX_FILE_SIZE_MB} MB"
        )

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    try:

        result = analyze_document(
            image_bytes=image_bytes,
            mime_type=file.content_type
        )

        return {
            "success": True,
            "filename": file.filename,
            "document_analysis": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Document analysis failed: {str(e)}"
        )
