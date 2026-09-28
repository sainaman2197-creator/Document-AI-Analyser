import os
import json
import base64
import re
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional









import google.generativeai as genai
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Product Analyzer API",
    description="Analyzes product descriptions from images using Gemini AI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)


ANALYSIS_PROMPT = """
You are an expert product safety analyst and nutritionist with deep knowledge of:
- Food ingredients and additives
- Cosmetic and personal care chemicals
- Pharmaceutical substances
- Household product chemicals
- Consumer product safety regulations (FDA, EU, WHO standards)

You have been given text extracted from a product label/description. Your job is to perform a thorough, accurate analysis.

EXTRACTED PRODUCT TEXT:
\"\"\"
{extracted_text}
\"\"\"

Analyze this product and return a STRICT JSON response (no markdown, no extra text) in this exact structure:

{{
  "product_name": "Detected product name or 'Unknown Product'",
  "product_category": "One of: Food & Beverage | Cosmetics & Personal Care | Pharmaceutical | Household Chemical | Supplement | Baby Product | Pet Product | Other",
  "brand": "Brand name if detected, else null",
  "ingredients_found": ["list", "of", "detected", "ingredients"],
  "analysis": {{
    "overall_safety_score": <integer 1-10, where 10 is completely safe>,
    "summary": "2-3 sentence plain-English summary of what this product is and its general safety profile",
    "ingredient_breakdown": [
      {{
        "name": "Ingredient name",
        "purpose": "What this ingredient does in the product",
        "safety_level": "Safe | Moderate Concern | High Concern | Harmful",
        "notes": "Any relevant health or safety notes"
      }}
    ]
  }},
  "harmful_substances": [
    {{
      "name": "Substance name",
      "risk_level": "Low | Medium | High | Critical",
      "health_effects": "Specific health effects this can cause",
      "who_is_at_risk": "e.g., pregnant women, children, people with kidney disease, everyone",
      "regulatory_status": "e.g., Banned in EU, FDA approved, WHO caution list"
    }}
  ],
  "allergens": ["list of detected allergens if any"],
  "recommendations": {{
    "use_product": <true if product is generally safe to use, false otherwise>,
    "verdict": "SAFE TO USE | USE WITH CAUTION | AVOID | NOT RECOMMENDED FOR CERTAIN GROUPS",
    "reasoning": "Clear explanation of why this verdict was reached",
    "usage_tips": ["tip1", "tip2"],
    "who_should_avoid": ["e.g., Pregnant women", "Children under 12"] or [],
    "safer_alternatives": "Suggest safer alternatives if the product has concerns, else null"
  }},
  "ocr_confidence": "High | Medium | Low",
  "data_completeness": "Complete | Partial | Insufficient"
}}

Rules:
- Be accurate and evidence-based. Do not exaggerate risks or downplay real ones.
- If the text is incomplete or unclear, set data_completeness to Partial or Insufficient.
- Base your analysis on peer-reviewed knowledge and official regulatory databases.
- If no harmful substances are found, return harmful_substances as an empty array [].
- Never return markdown or code blocks. Return only raw JSON.
"""


def extract_text_with_gemini(image_bytes: bytes) -> str:
    """Use Gemini Vision to extract all text from product image."""
    model = genai.GenerativeModel('gemini-2.5-flash')

    image = Image.open(io.BytesIO(image_bytes))

    ocr_prompt = """Extract ALL text visible in this product image. 
    Include: product name, brand, ingredients list, warnings, nutritional facts, 
    instructions, certifications, and any other text.
    Return the text exactly as it appears, preserving the structure (use newlines).
    Do not add any commentary — only return the raw extracted text."""

    response = model.generate_content([ocr_prompt, image])
    return response.text.strip()


def analyze_product_with_gemini(extracted_text: str) -> dict:
    """Send extracted text to Gemini for deep product analysis."""
    model = genai.GenerativeModel("gemini-1.5-pro")

    prompt = ANALYSIS_PROMPT.format(extracted_text=extracted_text)
    response = model.generate_content(prompt)

    raw = response.text.strip()

    # Strip markdown fences if Gemini wraps in ```json ... ```
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)


@app.get("/")
def root():
    return {"message": "Product Analyzer API is running", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "gemini_configured": bool(GEMINI_API_KEY)}


@app.post("/analyze")
async def analyze_product(file: UploadFile = File(...)):
    """
    Upload a product image → OCR → Analysis → JSON response
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp", "image/heic"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file.content_type}'. Allowed: JPEG, PNG, WEBP, HEIC"
        )

    # Validate file size (max 10MB)
    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max size is 10MB.")

    # Step 1: OCR — extract text from image
    try:
        extracted_text = extract_text_with_gemini(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")

    if not extracted_text or len(extracted_text.strip()) < 10:
        raise HTTPException(
            status_code=422,
            detail="Could not extract sufficient text from the image. Please upload a clearer product label photo."
        )

    # Step 2: Analysis — deep product analysis
    try:
        analysis_result = analyze_product_with_gemini(extracted_text)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Analysis returned invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # Attach raw OCR text for transparency
    analysis_result["extracted_text"] = extracted_text
    analysis_result["filename"] = file.filename

    return analysis_result


@app.post("/analyze-text")
async def analyze_text_directly(payload: dict):
    """
    Analyze product from raw text input (no image needed).
    Body: { "text": "..." }
    """
    text = payload.get("text", "").strip()
    if not text or len(text) < 10:
        raise HTTPException(status_code=400, detail="Text is too short or empty.")

    try:
        analysis_result = analyze_product_with_gemini(text)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Analysis returned invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    analysis_result["extracted_text"] = text
    return analysis_result
