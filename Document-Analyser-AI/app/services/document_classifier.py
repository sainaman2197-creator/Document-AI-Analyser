def classify_document(text: str) -> str:
    text_lower = text.lower()

    aadhaar_keywords = [
        "aadhaar",
        "uidai",
        "unique identification",
        "government of india",
        "year of birth",
        "dob",
    ]

    score = sum(
        1 for keyword in aadhaar_keywords
        if keyword in text_lower
    )

    if score >= 2:
        return "Aadhaar Card"

    return "Unknown Document"
