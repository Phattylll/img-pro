import json
from PIL import Image
import pytesseract
from dateutil import parser
import requests
from io import BytesIO

# Set the path to Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'D:\3.1\4.1\ImgPro\Lib\Tesseract\tesseract.exe'

def detect_date_from_image(image_source):
    try:
        if image_source.startswith('http://') or image_source.startswith('https://'):
            # Image source is a URL
            response = requests.get(image_source)
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
            else:
                raise ValueError("Failed to fetch image from URL")
        else:
            # Image source is a local file path
            image = Image.open(image_source)

        # Use pytesseract to extract text from the image
        text = pytesseract.image_to_string(image)

        # Split the text into individual lines
        lines = text.split('\n')

        # Initialize an empty list to store parsed dates
        parsed_dates = []

        # Iterate over each line and detect dates
        for line in lines:
            try:
                # Use dateutil to parse extracted text for dates
                parsed_date = parser.parse(line, fuzzy=True)

                # Check if the parsed date has incomplete information
                if not (parsed_date.day and parsed_date.month and parsed_date.year):
                    raise ValueError("Incomplete date information")

                # Append the parsed date to the list
                parsed_dates.append(parsed_date)
            except Exception as e:
                pass  # Ignore lines that cannot be parsed as dates

        if not parsed_dates:
            return "No date detected"
        elif all(not (date.day and date.month and date.year) for date in parsed_dates):
            return "All three components (day, month, year) are incomplete"
        else:
            return parsed_dates

    except Exception as e:
        return str(e)

def process_images(image_paths):
    try:
        # Initialize a dictionary to store production and expiration dates
        date_info = {}

        # Iterate over each image path and detect dates
        for image_path in image_paths:
            result = detect_date_from_image(image_path)
            if isinstance(result, list):
                if len(result) == 1:  # If only one date is detected, assume it is the expiration date
                    date_info = {
                        "status": "success",
                        "Img_path": image_path,
                        "EXP": {
                            "d": str(result[-1].day),
                            "m": str(result[-1].month),
                            "Y": str(result[-1].year)
                        }
                    }
                elif len(result) > 1:  # If multiple dates are detected
                    # Set the earliest date as production date and the latest date as expiration date
                    result.sort()  # Sort the dates
                    date_info = {
                        "status": "success",
                        "Img_path": image_path,
                        "PD": {
                            "d": str(result[0].day),
                            "m": str(result[0].month),
                            "Y": str(result[0].year)
                        },
                        "EXP": {
                            "d": str(result[-1].day),
                            "m": str(result[-1].month),
                            "Y": str(result[-1].year)
                        }
                    }
            else:
                date_info = {
                    "status": "error",
                    "Img_path": image_path,
                    "Msg": result
                }

        return date_info

    except ValueError as ve:
        return {
            "status": "error",
            "Msg": "Please try again or customize by yourself"
        }
    except Exception as e:
        return {
            "status": "error",
            "Msg": str(e)
        }


