import cv2
import pytesseract

from app.core.config import settings


pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH


def preprocess_image(image_path: str):
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError("Unable to read image")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    processed = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    return processed


def extract_text(image_path: str) -> str:
    processed_image = preprocess_image(image_path)

    text = pytesseract.image_to_string(
        processed_image,
        config="--psm 6"
    )

    return text.strip()
