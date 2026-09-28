# 🔬 Product Analyzer

An AI-powered product safety analyzer that extracts text from product label photos using OCR, then performs deep ingredient and safety analysis using Google Gemini AI.

## 🚀 Features

- **OCR via Gemini Vision** — Extracts all text from product images (labels, packaging, ingredient lists)
- **Deep Safety Analysis** — Identifies ingredients, harmful substances, allergens, and overall safety score
- **JSON API** — FastAPI backend with structured JSON responses
- **Beautiful UI** — Streamlit frontend with dark theme, safety metrics, and tabbed views
- **Downloadable Reports** — Export analysis as JSON or plain text

## 📁 Project Structure

```
product-analyzer/
├── backend/
│   └── main.py           # FastAPI backend with Gemini OCR + Analysis
├── frontend/
│   └── app.py            # Streamlit UI
├── .env.example          # Environment variable template
├── requirements.txt      # Python dependencies
└── README.md
```

## ⚙️ Setup

### 1. Clone / copy the project
```bash
cd product-analyzer
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your Gemini API Key
```bash
cp .env.example .env
# Edit .env and replace "your_gemini_api_key_here" with your actual key
```

Get your free API key from: https://aistudio.google.com/app/apikey

### 5. Run the backend (Terminal 1)
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 6. Run the frontend (Terminal 2)
```bash
cd frontend
streamlit run app.py
```

### 7. Open the app
Visit: **http://localhost:8501**

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| POST | `/analyze` | Upload image → OCR → Analysis |
| POST | `/analyze-text` | Raw text → Analysis (no image) |

### Example API Response (`/analyze`)
```json
{
  "product_name": "Oreo Original",
  "product_category": "Food & Beverage",
  "brand": "Nabisco",
  "ingredients_found": ["Sugar", "Enriched Flour", "High Oleic Canola Oil", ...],
  "analysis": {
    "overall_safety_score": 5,
    "summary": "Oreo cookies are a widely consumed snack product...",
    "ingredient_breakdown": [
      {
        "name": "High Fructose Corn Syrup",
        "purpose": "Sweetener",
        "safety_level": "Moderate Concern",
        "notes": "Linked to metabolic disorders when consumed in excess"
      }
    ]
  },
  "harmful_substances": [
    {
      "name": "TBHQ (tert-Butylhydroquinone)",
      "risk_level": "Medium",
      "health_effects": "Potential carcinogen at high doses; may cause nausea",
      "who_is_at_risk": "Children, individuals with allergies",
      "regulatory_status": "FDA approved below 0.02% of fat content; banned in some countries"
    }
  ],
  "allergens": ["Wheat", "Soy"],
  "recommendations": {
    "use_product": true,
    "verdict": "USE WITH CAUTION",
    "reasoning": "Safe for most adults in moderation, but contains additives of concern.",
    "usage_tips": ["Limit to occasional consumption", "Not suitable for diabetics"],
    "who_should_avoid": ["Diabetics", "People with wheat allergies"],
    "safer_alternatives": "Look for organic whole-grain cookies without artificial additives"
  },
  "ocr_confidence": "High",
  "data_completeness": "Complete",
  "extracted_text": "...",
  "filename": "oreo_label.jpg"
}
```

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| AI/OCR | Google Gemini 1.5 Flash (vision OCR) |
| AI Analysis | Google Gemini 1.5 Pro (reasoning) |
| Backend | FastAPI + Uvicorn |
| Frontend | Streamlit |
| Image Processing | Pillow (PIL) |

## 📌 Notes

- Maximum image size: **10MB**
- Supported formats: **JPEG, PNG, WEBP**
- For best OCR results, use **clear, well-lit** photos with **readable text**
- The analysis is AI-generated and should be used **for informational purposes only**

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | Your Google Gemini API key |
