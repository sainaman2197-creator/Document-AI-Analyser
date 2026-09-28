import json
from google import genai
from google.genai import types

from app.core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)


def analyze_document(image_bytes: bytes, mime_type: str):

    prompt = """
You are an AI document analyser.

Analyze the uploaded document image and return ONLY valid JSON.

Supported document types:
- Aadhaar Card
- PAN Card
- Passport
- Driving Licence
- Voter ID
- Unknown Document

Return this exact structure:

{
    "document_type": null,
    "confidence": null,
    "fields": {
        "name": null,
        "date_of_birth": null,
        "gender": null,
        "father_name": null,
        "address": null,
        "document_number": null
    },
    "raw_text": null
}

Rules:

1. Identify the document type.
2. Extract all clearly visible text.
3. Extract only information that is actually visible.
4. Never guess or invent information.
5. If a field is not available, return null.
6. For Aadhaar, NEVER return the complete Aadhaar number.
7. For Aadhaar, document_number must be:
   "XXXX XXXX <last4digits>"
8. For PAN, return the visible PAN number.
9. For Passport, return the passport number if clearly visible.
10. For Driving Licence, return the licence number if clearly visible.
11. Confidence must be a number between 0 and 1.
12. Return valid JSON only.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            ),
            prompt
        ]
    )

    text = response.text.strip()

    if text.startswith("```json"):
        text = text[7:]

    if text.endswith("```"):
        text = text[:-3]

    return json.loads(text.strip())
