import re


def extract_aadhaar_number(text: str):
    pattern = r"\b\d{4}\s?\d{4}\s?\d{4}\b"

    match = re.search(pattern, text)

    if not match:
        return None

    number = re.sub(r"\D", "", match.group())

    return f"XXXX XXXX {number[-4:]}"


def extract_date_of_birth(text: str):
    patterns = [
        r"(?:DOB|D\.O\.B|Date of Birth|Birth)\s*[:\-]?\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})",
        r"(?:DOB|D\.O\.B|Date of Birth|Birth)\s*[:\-]?\s*(\d{4}[\/\-]\d{2}[\/\-]\d{2})",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:
            return match.group(1)

    return None


def extract_gender(text: str):
    text_lower = text.lower()

    if re.search(r"\bmale\b", text_lower):
        return "Male"

    if re.search(r"\bfemale\b", text_lower):
        return "Female"

    if re.search(r"\btransgender\b", text_lower):
        return "Transgender"

    return None


def extract_name(text: str):
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    ignore_words = [
        "aadhaar",
        "uidai",
        "government",
        "india",
        "unique",
        "identification",
        "authority",
        "male",
        "female",
        "transgender",
    ]

    for line in lines:
        lower_line = line.lower()

        if any(word in lower_line for word in ignore_words):
            continue

        if re.search(r"\d", line):
            continue

        words = line.split()

        if 2 <= len(words) <= 5:
            if all(re.match(r"^[A-Za-z.\-]+$", word) for word in words):
                return line

    return None


def extract_address(text: str):
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    address_lines = []
    collecting = False

    for line in lines:
        lower_line = line.lower()

        if "address" in lower_line:
            collecting = True
            continue

        if collecting:
            address_lines.append(line)

            if len(address_lines) >= 5:
                break

    if address_lines:
        return " ".join(address_lines)

    return None


def extract_aadhaar_fields(text: str):
    return {
        "name": extract_name(text),
        "date_of_birth": extract_date_of_birth(text),
        "gender": extract_gender(text),
        "aadhaar_number": extract_aadhaar_number(text),
        "address": extract_address(text),
    }
