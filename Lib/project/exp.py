import json
from PIL import Image
import pytesseract
from dateutil import parser
import requests
from io import BytesIO


pytesseract.pytesseract.tesseract_cmd = r'D:\3.1\4.1\ImgPro\Lib\Tesseract\tesseract.exe'

def detect_date_from_image(image_source):
    try:
        image = Image.open(BytesIO(requests.get(image_source).content)) if image_source.startswith(('http://', 'https://')) else Image.open(image_source)
        lines = pytesseract.image_to_string(image).split('\n')
        
        parsed_dates = [parser.parse(line, fuzzy=True) for line in lines if line.strip()]
        valid_dates = [date for date in parsed_dates if date.day and date.month and date.year]

        if not valid_dates:
            return "No date detected"
        
        return valid_dates

    except Exception as e:
        return str(e)

def process_images(image_paths):
    try:
        date_info = {}

        for image_path in image_paths:
            result = detect_date_from_image(image_path)
            if isinstance(result, list):
                result.sort()
                date_info = {
                    "status": "success",
                    "Img_path": image_path,
                    "PD": {"d": str(result[0].day), "m": str(result[0].month), "Y": str(result[0].year)},
                    "EXP": {"d": str(result[-1].day), "m": str(result[-1].month), "Y": str(result[-1].year)},
                } if len(result) > 1 else {
                    "status": "success",
                    "Img_path": image_path,
                    "EXP": {"d": str(result[0].day), "m": str(result[0].month), "Y": str(result[0].year)},
                }
            else:
                date_info = {"status": "error", "Img_path": image_path, "Msg": result}

        return date_info

    except (ValueError, Exception) as e:
        return {"status": "error", "Msg": "Please try again or customize by yourself"}
