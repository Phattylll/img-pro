from PIL import Image
import pytesseract
from dateutil import parser

# Set the path to Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'D:\3.1\4.1\ImgPro\Lib\Tesseract\tesseract.exe'

def detect_date_from_image(image_path):
    try:
        # Read the image using PIL
        image = Image.open(image_path)

        # Use pytesseract to extract text from the image
        text = pytesseract.image_to_string(image)

        # Use dateutil to parse extracted text for dates
        parsed_date = parser.parse(text, fuzzy=True)

        # Extract date, month, and year components
        date = parsed_date.day
        month = parsed_date.month
        year = parsed_date.year

        return date, month, year

    except Exception as e:
        return str(e)