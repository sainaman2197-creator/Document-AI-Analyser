"""
Product Analyzer — Streamlit frontend.

Uploads a photo of a product label to a FastAPI backend, which runs OCR +
AI analysis and returns ingredient safety data. This module renders that
data as a clean, professional dashboard.

Run with:
    streamlit run product_analyzer_app.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import requests
import streamlit as st
from PIL import Image

# ──────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────

DEFAULT_BACKEND_URL = "http://localhost:8000"
REQUEST_TIMEOUT_HEALTH = 3
REQUEST_TIMEOUT_ANALYZE = 120
ALLOWED_IMAGE_TYPES = ["jpg", "jpeg", "png", "webp"]

# Background photo shown behind the whole app (duotone-tinted with the violet
# theme). Swap this for any image URL to personalize it — e.g. your own
# product/lab photo hosted somewhere, or another stock image.
BACKGROUND_IMAGE_URL = "https://picsum.photos/seed/productanalyzer/1920/1080?grayscale&blur=1"

SAFETY_COLORS = {
    "good": "#10b981",
    "warn": "#f59e0b",
    "bad": "#ef4444",
}

RISK_EMOJI = {
    "low": "🟡",
    "medium": "🟠",
    "high": "🔴",
    "critical": "☠️",
}

BADGE_CLASS_BY_LEVEL = {
    "safe": "badge-safe",
    "moderate": "badge-moderate",
    "high": "badge-high",
}

VERDICT_CLASS_KEYWORDS = {
    "verdict-safe": ("safe",),
    "verdict-caution": ("caution", "certain"),
}

SESSION_KEY_RESULT = "analysis_result"
SESSION_KEY_FILE_ID = "analyzed_file_id"


# ──────────────────────────────────────────────────────────────────────────
# Page setup
# ──────────────────────────────────────────────────────────────────────────

def configure_page() -> None:
    """Set Streamlit page metadata and inject the custom theme CSS."""
    st.set_page_config(
        page_title="Product Analyzer",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    css = CUSTOM_CSS.replace("__BACKGROUND_IMAGE_URL__", BACKGROUND_IMAGE_URL)
    st.markdown(css, unsafe_allow_html=True)


CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* ── Background photo, duotone-tinted with the theme ─────────────────── */
    @keyframes bgPan {
        0%, 100% { background-position: 50% 50%, 50% 50%; }
        50%      { background-position: 50% 50%, 56% 46%; }
    }
    @keyframes gridPan {
        from { background-position: 0 0; }
        to   { background-position: 48px 48px; }
    }

    .stApp {
        background-color: #241c3d;
        background-image:
            linear-gradient(160deg, rgba(53,33,92,0.82), rgba(36,28,61,0.85)),
            url('__BACKGROUND_IMAGE_URL__');
        background-size: cover, cover;
        background-position: center, center;
        background-attachment: fixed, fixed;
        background-repeat: no-repeat, no-repeat;
        animation: bgPan 30s ease-in-out infinite;
    }
    [data-testid="stAppViewContainer"] { position: relative; z-index: 1; }
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        background-image:
            linear-gradient(rgba(196,181,253,0.07) 1px, transparent 1px),
            linear-gradient(90deg, rgba(196,181,253,0.07) 1px, transparent 1px);
        background-size: 48px 48px;
        animation: gridPan 9s linear infinite;
        pointer-events: none;
        z-index: 0;
    }

    /* ── Entrance animation for cards ──────────────────────────────────── */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(14px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    @media (prefers-reduced-motion: reduce) {
        .stApp, .stApp::before, .main-header::after,
        .metric-card, .verdict-card, .ingredient-row, .harmful-card, .tip-item,
        .stButton button {
            animation: none !important;
        }
    }

    .main-header {
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, #2a1f4d 0%, #4527a0 50%, #8b5cf6 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.25);
    }
    @keyframes scanSweep {
        0%   { transform: translateY(-100%); }
        100% { transform: translateY(220%); }
    }
    .main-header::after {
        content: "";
        position: absolute;
        top: 0; left: -20%;
        width: 140%;
        height: 45%;
        background: linear-gradient(180deg, transparent, rgba(233,224,255,0.22), transparent);
        animation: scanSweep 5s linear infinite;
        pointer-events: none;
    }
    .main-header h1 { color: #fff; font-size: 2.2rem; font-weight: 700; margin: 0; position: relative; }
    .main-header p  { color: #e0d4ff; font-size: 1rem; margin: 0.5rem 0 0; position: relative; }

    .verdict-safe    { background: linear-gradient(135deg, #065f46, #047857); border-left: 5px solid #10b981; }
    .verdict-caution { background: linear-gradient(135deg, #78350f, #92400e); border-left: 5px solid #f59e0b; }
    .verdict-avoid   { background: linear-gradient(135deg, #7f1d1d, #991b1b); border-left: 5px solid #ef4444; }

    .verdict-card {
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
        animation: fadeInUp 0.5s ease both;
    }
    .verdict-card h2 { font-size: 1.6rem; margin: 0 0 0.3rem; }
    .verdict-card p  { font-size: 0.95rem; opacity: 0.9; margin: 0; }

    .metric-card {
        border: 1px solid rgba(196,181,253,0.25);
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        transition: border-color 0.2s ease, transform 0.2s ease;
        animation: fadeInUp 0.5s ease both;
        background: rgba(70,54,108,0.55);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
    }
    .metric-card:hover { border-color: rgba(196,181,253,0.55); transform: translateY(-2px); }
    .metric-card .value { font-size: 2rem; font-weight: 700; color: #d8cdfb; }
    .metric-card .label { font-size: 0.8rem; color: #c9c2e6; text-transform: uppercase; letter-spacing: 0.05em; }

    .section-card {
        background: rgba(50,39,86,0.45);
        border: 1px solid rgba(196,181,253,0.15);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
    }

    .ingredient-row {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        padding: 0.75rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        background: rgba(70,54,108,0.5);
        border: 1px solid rgba(196,181,253,0.22);
        animation: fadeInUp 0.4s ease both;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }

    .badge-safe     { background: #065f46; color: #6ee7b7; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .badge-moderate { background: #78350f; color: #fcd34d; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .badge-high     { background: #7c2d12; color: #fca5a5; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .badge-harmful  { background: #4c0519; color: #fda4af; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }

    .harmful-card {
        background: rgba(80,30,30,0.55);
        border: 1px solid rgba(239,68,68,0.4);
        border-left: 4px solid #ef4444;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
        animation: fadeInUp 0.4s ease both;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }
    .harmful-card h4 { color: #fecaca; margin: 0 0 0.4rem; }
    .harmful-card p  { color: #e5e7eb; font-size: 0.88rem; margin: 0.2rem 0; }

    .tip-item {
        background: rgba(70,54,108,0.5);
        border: 1px solid rgba(167,139,250,0.5);
        border-radius: 8px;
        padding: 0.6rem 1rem;
        margin-bottom: 0.4rem;
        color: #e0d4ff;
        font-size: 0.9rem;
        animation: fadeInUp 0.4s ease both;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }

    .ocr-box {
        background: rgba(30,22,50,0.6);
        border: 1px solid rgba(196,181,253,0.2);
        border-radius: 8px;
        padding: 1rem;
        font-family: monospace;
        font-size: 0.82rem;
        color: #ddd6f3;
        white-space: pre-wrap;
        max-height: 300px;
        overflow-y: auto;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }

    .score-bar-bg {
        background: rgba(70,54,108,0.5);
        border-radius: 20px;
        height: 12px;
        width: 100%;
        margin-top: 6px;
        overflow: hidden;
    }
    .score-bar-fill {
        height: 12px;
        border-radius: 20px;
        transition: width 0.5s ease;
    }

    div[data-testid="stSidebar"] {
        background: rgba(42,33,71,0.92);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
    }

    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 0 0 rgba(139,92,246,0.45); }
        50%      { box-shadow: 0 0 0 9px rgba(139,92,246,0); }
    }
    .stButton button {
        background: linear-gradient(135deg, #8b5cf6, #7c3aed) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.4rem !important;
        width: 100%;
        transition: filter 0.15s ease;
    }
    .stButton button:not(:disabled) { animation: pulseGlow 2.4s ease-in-out infinite; }
    .stButton button:hover  { filter: brightness(1.15); }
    .stButton button:focus-visible { outline: 2px solid #e0d4ff; outline-offset: 2px; }

    .allergen-tag {
        display: inline-block;
        background: rgba(95,60,150,0.55);
        color: #e9defe;
        border: 1px solid rgba(167,139,250,0.55);
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.8rem;
        margin: 3px;
    }
</style>
"""


# ──────────────────────────────────────────────────────────────────────────
# Small presentation helpers
# ──────────────────────────────────────────────────────────────────────────

def safety_score_color(score: int) -> str:
    """Map a 0-10 safety score to a traffic-light hex color."""
    if score >= 8:
        return SAFETY_COLORS["good"]
    if score >= 5:
        return SAFETY_COLORS["warn"]
    return SAFETY_COLORS["bad"]


def verdict_card_class(verdict: str) -> str:
    """Pick the CSS class for the top verdict banner based on its text."""
    verdict_lower = verdict.lower()
    for css_class, keywords in VERDICT_CLASS_KEYWORDS.items():
        if any(keyword in verdict_lower for keyword in keywords):
            return css_class
    return "verdict-avoid"


def ingredient_badge_class(safety_level: str) -> str:
    """Pick the CSS class for an ingredient's safety-level badge."""
    safety_level_lower = safety_level.lower()
    for keyword, css_class in BADGE_CLASS_BY_LEVEL.items():
        if keyword in safety_level_lower:
            return css_class
    return "badge-harmful"


def risk_level_emoji(risk_level: str) -> str:
    """Pick a representative emoji for a harmful-substance risk level."""
    return RISK_EMOJI.get(risk_level.lower(), "⚠️")


def render_card(css_class: str, inner_html: str) -> None:
    """Render a div with the given class and pre-built inner HTML."""
    st.markdown(f'<div class="{css_class}">{inner_html}</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────
# Backend communication
# ──────────────────────────────────────────────────────────────────────────

@dataclass
class BackendStatus:
    reachable: bool
    message: str


def check_backend_health(backend_url: str) -> BackendStatus:
    """Ping the backend's /health endpoint and report whether it's up."""
    try:
        response = requests.get(f"{backend_url}/health", timeout=REQUEST_TIMEOUT_HEALTH)
    except requests.exceptions.RequestException:
        return BackendStatus(False, "Backend offline — make sure FastAPI is running on port 8000")

    if response.status_code == 200:
        return BackendStatus(True, "Backend connected")
    return BackendStatus(False, f"Backend returned status {response.status_code}")


def analyze_product_image(backend_url: str, filename: str, file_bytes: bytes, mime_type: str) -> dict[str, Any]:
    """
    Send the uploaded image to the backend's /analyze endpoint.

    Raises:
        requests.exceptions.ConnectionError: if the backend can't be reached.
        RuntimeError: if the backend responds with a non-200 status.
    """
    files = {"file": (filename, file_bytes, mime_type)}
    response = requests.post(f"{backend_url}/analyze", files=files, timeout=REQUEST_TIMEOUT_ANALYZE)

    if response.status_code != 200:
        try:
            detail = response.json().get("detail", "Unknown error")
        except ValueError:
            detail = f"HTTP {response.status_code}"
        raise RuntimeError(detail)

    return response.json()


# ──────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────

def render_sidebar() -> str:
    """Render the settings sidebar and return the configured backend URL."""
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        backend_url = st.text_input("Backend URL", value=DEFAULT_BACKEND_URL).rstrip("/")

        st.markdown("---")
        st.markdown("### 📋 How to Use")
        st.markdown(
            """
1. **Upload** a clear photo of the product label
2. Click **Analyze Product**
3. Review the **safety analysis**
4. Check the **harmful substances** section
5. Read the **verdict** before using
            """
        )

        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown(
            """
**Product Analyzer** uses AI to:
- Extract text via OCR
- Identify ingredients
- Flag harmful substances
- Give safety recommendations

*For informational purposes only — not medical advice.*
            """
        )

        st.markdown("---")
        status = check_backend_health(backend_url)
        if status.reachable:
            st.success(f"✅ {status.message}")
        else:
            st.warning(f"⚠️ {status.message}")

    return backend_url


# ──────────────────────────────────────────────────────────────────────────
# Header + upload section
# ──────────────────────────────────────────────────────────────────────────

def render_header() -> None:
    render_card(
        "main-header",
        "<h1>🔬 Product Analyzer</h1>"
        "<p>Upload a product label photo — AI extracts ingredients, "
        "flags harmful substances, and gives a safety verdict</p>",
    )


def render_upload_section() -> tuple[Any, bool]:
    """Render the upload + preview columns. Returns (uploaded_file, analyze_clicked)."""
    col_upload, col_preview = st.columns([1, 1], gap="large")

    with col_upload:
        st.markdown("### 📷 Upload Product Image")
        uploaded_file = st.file_uploader(
            "Drag & drop or click to browse",
            type=ALLOWED_IMAGE_TYPES,
            help="Upload a clear photo of the product label showing ingredients",
        )
        analyze_clicked = st.button("🔍 Analyze Product", disabled=uploaded_file is None)

    with col_preview:
        st.markdown("### 🖼️ Image Preview")
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, use_container_width=True, caption=uploaded_file.name)
        else:
            st.info("Upload an image to see a preview here.")

    return uploaded_file, analyze_clicked


# ──────────────────────────────────────────────────────────────────────────
# Result rendering — verdict banner + top metrics
# ──────────────────────────────────────────────────────────────────────────

def render_verdict_banner(recommendations: dict[str, Any]) -> None:
    verdict = recommendations.get("verdict", "UNKNOWN")
    reasoning = recommendations.get("reasoning", "")
    use_product = recommendations.get("use_product", False)
    icon = "✅" if use_product else "🚫"
    css_class = verdict_card_class(verdict)

    render_card(
        f"verdict-card {css_class}",
        f"<h2>{icon} {verdict}</h2><p>{reasoning}</p>",
    )


def render_metric(value: str, label: str, color: str) -> None:
    render_card(
        "metric-card",
        f'<div class="value" style="color:{color}">{value}</div>'
        f'<div class="label">{label}</div>',
    )


def render_top_metrics(data: dict[str, Any], analysis: dict[str, Any]) -> int:
    """Render the four headline metric cards. Returns the safety score."""
    score = analysis.get("overall_safety_score", 0)
    score_color = safety_score_color(score)

    harmful_count = len(data.get("harmful_substances", []))
    allergen_count = len(data.get("allergens", []))
    ingredient_count = len(data.get("ingredients_found", []))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric(f"{score}/10", "Safety Score", score_color)
    with col2:
        render_metric(str(harmful_count), "Harmful Substances", "#ef4444")
    with col3:
        render_metric(str(allergen_count), "Allergens Found", "#a78bfa")
    with col4:
        render_metric(str(ingredient_count), "Ingredients Detected", "#c4b5fd")

    return score


def render_score_bar(score: int) -> None:
    color = safety_score_color(score)
    bar_width = max(0, min(score, 10)) * 10
    st.markdown(
        f"""
        <div style="margin: 1rem 0 1.5rem;">
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span style="color:#94a3b8; font-size:0.85rem;">Safety Score</span>
                <span style="color:{color}; font-weight:600;">{score}/10</span>
            </div>
            <div class="score-bar-bg">
                <div class="score-bar-fill" style="width:{bar_width}%; background:{color};"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────
# Result rendering — tabs
# ──────────────────────────────────────────────────────────────────────────

def render_overview_tab(data: dict[str, Any], analysis: dict[str, Any]) -> None:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🏷️ Product Info")
        st.markdown(f"**Product:** {data.get('product_name', 'N/A')}")
        st.markdown(f"**Brand:** {data.get('brand') or 'Not detected'}")
        st.markdown(f"**Category:** {data.get('product_category', 'N/A')}")
        st.markdown(f"**Data Completeness:** {data.get('data_completeness', 'N/A')}")
        st.markdown(f"**OCR Confidence:** {data.get('ocr_confidence', 'N/A')}")

    with col2:
        st.markdown("#### 🧾 Summary")
        st.info(analysis.get("summary", "No summary available."))

        st.markdown("#### ⚠️ Allergens")
        allergens = data.get("allergens", [])
        if allergens:
            tags = "".join(f'<span class="allergen-tag">🌿 {a}</span>' for a in allergens)
            st.markdown(f'<div style="margin-top:0.3rem">{tags}</div>', unsafe_allow_html=True)
        else:
            st.success("No common allergens detected.")


def render_ingredients_tab(data: dict[str, Any], analysis: dict[str, Any]) -> None:
    breakdown = analysis.get("ingredient_breakdown", [])

    if not breakdown:
        ingredients = data.get("ingredients_found", [])
        if ingredients:
            for ingredient in ingredients:
                st.markdown(f"• {ingredient}")
        else:
            st.warning("No ingredient breakdown available.")
        return

    st.markdown(f"#### 🧪 Ingredient Analysis ({len(breakdown)} ingredients)")
    for ingredient in breakdown:
        badge_class = ingredient_badge_class(ingredient.get("safety_level", ""))
        render_card(
            "ingredient-row",
            f"""
            <div style="flex:1">
                <div style="display:flex; align-items:center; gap:0.7rem; margin-bottom:0.3rem;">
                    <strong style="color:#e2e8f0">{ingredient.get('name', '')}</strong>
                    <span class="{badge_class}">{ingredient.get('safety_level', '')}</span>
                </div>
                <div style="color:#94a3b8; font-size:0.85rem;">
                    <strong>Purpose:</strong> {ingredient.get('purpose', 'N/A')}
                </div>
                <div style="color:#94a3b8; font-size:0.85rem;">
                    {ingredient.get('notes', '')}
                </div>
            </div>
            """,
        )


def render_harmful_substances_tab(data: dict[str, Any]) -> None:
    harmful_substances = data.get("harmful_substances", [])

    if not harmful_substances:
        st.success("🎉 No harmful substances detected in this product!")
        return

    st.markdown(f"#### ☠️ {len(harmful_substances)} Harmful Substance(s) Detected")
    for substance in harmful_substances:
        emoji = risk_level_emoji(substance.get("risk_level", ""))
        render_card(
            "harmful-card",
            f"""
            <h4>{emoji} {substance.get('name', '')}
                <span style="font-size:0.8rem; background:#450a0a; color:#fca5a5;
                    padding:2px 8px; border-radius:10px; margin-left:0.5rem;">
                    {substance.get('risk_level', '')} Risk
                </span>
            </h4>
            <p><strong>⚕️ Health Effects:</strong> {substance.get('health_effects', 'N/A')}</p>
            <p><strong>👥 Who's at Risk:</strong> {substance.get('who_is_at_risk', 'N/A')}</p>
            <p><strong>📋 Regulatory Status:</strong> {substance.get('regulatory_status', 'N/A')}</p>
            """,
        )


def render_recommendations_tab(recommendations: dict[str, Any]) -> None:
    st.markdown("#### 💡 Usage Tips")
    tips = recommendations.get("usage_tips", [])
    if tips:
        for tip in tips:
            render_card("tip-item", f"💡 {tip}")
    else:
        st.info("No specific usage tips available.")

    who_should_avoid = recommendations.get("who_should_avoid", [])
    if who_should_avoid:
        st.markdown("#### 🚫 Who Should Avoid This Product")
        for group in who_should_avoid:
            st.markdown(f"- ⛔ {group}")

    safer_alternatives = recommendations.get("safer_alternatives")
    if safer_alternatives:
        st.markdown("#### 🔄 Safer Alternatives")
        st.info(safer_alternatives)


def render_raw_data_tab(data: dict[str, Any]) -> None:
    st.markdown("#### 📄 Extracted Text (OCR)")
    ocr_text = data.get("extracted_text", "N/A")
    st.markdown(f'<div class="ocr-box">{ocr_text}</div>', unsafe_allow_html=True)

    st.markdown("#### 🔧 Full JSON Response")
    st.json(data)

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            label="⬇️ Download JSON",
            data=json.dumps(data, indent=2),
            file_name="product_analysis.json",
            mime="application/json",
        )
    with col_dl2:
        st.download_button(
            label="⬇️ Download OCR Text",
            data=data.get("extracted_text", ""),
            file_name="extracted_text.txt",
            mime="text/plain",
        )


def render_results(data: dict[str, Any]) -> None:
    """Render the full results dashboard for a completed analysis."""
    recommendations = data.get("recommendations", {})
    analysis = data.get("analysis", {})

    render_verdict_banner(recommendations)
    score = render_top_metrics(data, analysis)
    render_score_bar(score)

    tab_overview, tab_ingredients, tab_harmful, tab_recs, tab_raw = st.tabs(
        ["📋 Overview", "🧪 Ingredients", "☠️ Harmful Substances", "💡 Recommendations", "📄 Raw Data"]
    )

    with tab_overview:
        render_overview_tab(data, analysis)
    with tab_ingredients:
        render_ingredients_tab(data, analysis)
    with tab_harmful:
        render_harmful_substances_tab(data)
    with tab_recs:
        render_recommendations_tab(recommendations)
    with tab_raw:
        render_raw_data_tab(data)


# ──────────────────────────────────────────────────────────────────────────
# Main flow
# ──────────────────────────────────────────────────────────────────────────

def run_analysis(backend_url: str, uploaded_file: Any) -> None:
    """Call the backend and store the result in session state, or show an error."""
    with st.spinner("🧠 Extracting text and analyzing ingredients..."):
        uploaded_file.seek(0)
        try:
            result = analyze_product_image(
                backend_url=backend_url,
                filename=uploaded_file.name,
                file_bytes=uploaded_file.read(),
                mime_type=uploaded_file.type or "application/octet-stream",
            )
        except requests.exceptions.ConnectionError:
            st.error(
                "❌ Could not connect to backend. Make sure FastAPI is running:\n"
                "```\nuvicorn main:app --reload\n```"
            )
            return
        except requests.exceptions.Timeout:
            st.error("❌ The backend took too long to respond. Please try again.")
            return
        except RuntimeError as exc:
            st.error(f"❌ Analysis failed: {exc}")
            return

    st.session_state[SESSION_KEY_RESULT] = result
    st.session_state[SESSION_KEY_FILE_ID] = uploaded_file.file_id
    st.success("✅ Analysis complete!")


def main() -> None:
    configure_page()
    backend_url = render_sidebar()
    render_header()

    uploaded_file, analyze_clicked = render_upload_section()
    st.markdown("---")

    # Clear stale results if a different file has been uploaded.
    if uploaded_file is not None and st.session_state.get(SESSION_KEY_FILE_ID) != uploaded_file.file_id:
        if not analyze_clicked:
            st.session_state.pop(SESSION_KEY_RESULT, None)

    if analyze_clicked and uploaded_file is not None:
        run_analysis(backend_url, uploaded_file)

    result = st.session_state.get(SESSION_KEY_RESULT)
    if result is not None:
        render_results(result)


if __name__ == "__main__":
    main()
