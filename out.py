import pytesseract
import cv2
import numpy as np
from fuzzywuzzy import fuzz
import re
from datetime import datetime
from pyzbar.pyzbar import decode
import requests

# Set the Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'D:\3.1\4.1\ImgPro\Lib\Tesseract\tesseract.exe'

# Function to preprocess the image
def preprocess_image(image):
    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Invert the image (make characters white on a dark background)
    inverted_image = cv2.bitwise_not(gray_image)

    # Apply adaptive thresholding to enhance text
    _, threshold_image = cv2.threshold(inverted_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Sharpen the image by applying a kernel
    sharpening_kernel = np.array([[-1, -1, -1], [-1, 10, -1], [-1, -1, -1]])
    sharpened_image = cv2.filter2D(threshold_image, -1, sharpening_kernel)

    return sharpened_image

# Function to detect the dominant script in a line
def detect_script(line):
    # Define characters for different scripts
    thai_characters = set('กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ')
    english_characters = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    numeric_characters = set('0123456789')

    # Count characters from different scripts in the line
    thai_count = sum(char in thai_characters for char in line)
    english_count = sum(char in english_characters for char in line)
    numeric_count = sum(char in numeric_characters for char in line)

    # Compare counts to determine the dominant script
    max_count = max(thai_count, english_count, numeric_count)
    if max_count == thai_count:
        return 'Thai'
    elif max_count == english_count:
        return 'English'
    elif max_count == numeric_count:
        return 'Numeric'
    else:
        return 'Unknown'

# Function to detect dates in text
def detect_dates(text):
    # Define regex patterns for various date formats
    date_patterns = [
        r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b',
        r'\b(\d{1,2}\.\d{1,2}\.\d{2,4})\b',
        r'\b(\d{2}\d{2}\d{2})\b',
        r'\b(\d{2}\d{2}\d{4})\b'
    ]

    detected_dates = []

    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        detected_dates.extend(matches)

    # Convert detected dates to a standardized format
    formatted_dates = []
    for date_str in detected_dates:
        try:
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
            formatted_dates.append(date_obj.strftime('%d/%m/%Y'))
        except ValueError:
            pass  # Handle invalid date formats gracefully

    return formatted_dates

# Function to categorize text and perform searches
def categorize_text(text, search_phrases, output_file_path):
    thai_text = ''
    english_text = ''
    numeric_text = ''

    for line in text.split('\n'):
        script = detect_script(line)
        line_without_spaces = ''.join(line.split())

        if script == 'Thai':
            thai_text += line_without_spaces + '\n'
        elif script == 'English':
            english_text += line_without_spaces + '\n'
        elif script == 'Numeric':
            numeric_text += line_without_spaces + '\n'

    print("Detected Thai Text:")
    print(thai_text)
    print("\nDetected English Text:")
    print(english_text)
    print("\nDetected Numeric Text:")
    print(numeric_text)

    # Perform searches for each category
    search_in_text('Thai Text', thai_text, search_phrases, output_file_path)
    search_in_text('English Text', english_text, search_phrases, output_file_path)
    search_in_text('Numeric Text', numeric_text, search_phrases, output_file_path)

    # Detect and print dates
    detected_dates = detect_dates(text)
    if detected_dates:
        print("\nDetected Dates:")
        for date in detected_dates:
            print(f"- {date}")

    # Print "----------------------" only after saving the last word
    with open(output_file_path, 'a', encoding='utf-8') as output_file:
        output_file.write("----------------------\n")

# Function to search for phrases in text
def search_in_text(category, text, search_phrases, output_file_path):
    print(f"\nSearching in {category}:")
    found_phrases = []

    for phrase in search_phrases:
        # Check if the phrase is approximately 70% similar to any word in the text
        similarity_threshold = 40
        similar_words = [word for word in text.split() if fuzz.ratio(phrase, word) >= similarity_threshold]

        if similar_words:
            found_phrases.append((phrase, similar_words))

    if found_phrases:
        print(f"Found the following phrases in {category}:")
        with open(output_file_path, 'a', encoding='utf-8') as output_file:
            for found_phrase, similar_words in found_phrases:
                output_file.write(f"{found_phrase}\n")
                print(f"- {found_phrase} (Similar words: {', '.join(similar_words)}), Similarity: {fuzz.ratio(found_phrase, similar_words[0])}%")

# Function to save product information in wordsave.txt
def save_product_info(product_info, output_file_path):
    if product_info:
        print(f"Saving Product Information: {product_info}")
        with open(output_file_path, 'a', encoding='utf-8') as output_file:
            output_file.write(f"Product Information: {product_info}\n")
            output_file.write("----------------------\n")

# Function to search for barcodes on the internet using Open Food Facts API
def search_barcodes_on_internet(barcodes, output_file_path):
    print("\nSearching for barcodes on the internet:")
    for barcode in barcodes:
        barcode_data = barcode.data.decode('utf-8')
        print(f"\nBarcode: {barcode_data}")

        # Get product information from barcode using Open Food Facts API
        product_info = get_product_info(barcode_data)

        # Save product information in wordsave.txt
        save_product_info(product_info, output_file_path)

        if product_info:
            print(f"Product Information: {product_info}")
        else:
            print("Product information not found.")

        # Optionally, you can open the search URL in a headless browser or skip it
        # search_url = f"https://www.google.com/search?q={barcode_data}"
        # webbrowser.open(search_url)

        # Optionally, you can print the search URL
        # print(f"Search URL: {search_url}")

# Function to get product information from barcode using Open Food Facts API
def get_product_info(barcode):
    url = f'https://world.openfoodfacts.org/api/v0/product/{barcode}.json'
    response = requests.get(url)

    if response.status_code == 200:
        product_data = response.json()
        if 'product' in product_data and 'product_name' in product_data['product']:
            return product_data['product']['product_name']
    return None

# Load the image using OpenCV
image_path = r'D:\3.1\4.1\ImgPro\ImgEXP\5.jpg'
image = cv2.imread(image_path)

if image is None:
    print(f"Error: Unable to load the image at {image_path}.")
else:
    # Preprocess the image
    preprocessed_image = preprocess_image(image)

    # Perform OCR on the preprocessed image
    results = pytesseract.image_to_string(preprocessed_image, lang='eng+tha', config='--psm 6')

    # Read search phrases from a text file
    with open(r'D:\3.1\4.1\ImgPro\ImgEXP\word.txt', 'r', encoding='utf-8') as file:
        search_phrases = [line.strip() for line in file.readlines()]

    # Specify the output file path
    output_file_path = r'D:\3.1\4.1\ImgPro\ImgEXP\wordsave.txt'

    # Use the specified output file path when calling the categorize_text function
    categorize_text(results, search_phrases, output_file_path)

    # Read barcodes from the image
    barcodes = decode(image)
    if barcodes:
        print("\nDetected Barcodes:")
        for barcode in barcodes:
            barcode_data = barcode.data.decode('utf-8')
            print(f"- {barcode_data}")

        # Search for barcodes on the internet
        search_barcodes_on_internet(barcodes, output_file_path)

    # Optionally, you can print a message indicating that the results have been saved
    print(f"\nResults saved to: {output_file_path}")
