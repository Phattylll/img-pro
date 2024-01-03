# coding: utf-8

import sys
from flask import Flask, jsonify
import pytesseract
import cv2
import numpy as np
from fuzzywuzzy import fuzz
import re
from datetime import datetime
from pyzbar.pyzbar import decode
import requests
from urllib.request import urlopen
import json

sys.stdout.reconfigure(encoding='utf-8')

# app = Flask(__name__)
# app.config['JSON_AS_ASCII'] = False  # Ensure non-ASCII characters are not escaped in JSON

# Set the Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'D:\3.1\4.1\ImgPro\Lib\Tesseract\tesseract.exe'
# pytesseract.pytesseract.tesseract_cmd = r'/home/diplab/anaconda3/envs/chillmate/bin/tesseract'


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
def save_product_info(product_info, output_file_path, barcode_info):
    if product_info:
        print(f"Saving Product Information: {product_info}")
        with open(output_file_path, 'a', encoding='utf-8') as output_file:
            output_file.write(f"Product Information: {product_info}\n")
            output_file.write("----------------------\n")
        
        barcode_info['product_info'] = product_info

# Function to search for barcodes on the internet using Open Food Facts API
def search_barcodes_on_internet(barcodes, output_file_path, barcode_info):
    print("\nSearching for barcodes on the internet:")
    for barcode in barcodes:
        barcode_data = barcode.data.decode('utf-8')
        print(f"\nBarcode: {barcode_data}")

        # Get product information from barcode using Open Food Facts API
        product_info = get_product_info(barcode_data)

        # Save product information in wordsave.txt and barcode_info dictionary
        save_product_info(product_info, output_file_path, barcode_info)

        if product_info:
            print(f"Product Information: {product_info}")
        else:
            print("Product information not found.")

        barcode_info['barcode'] = barcode_data

    return barcode_info

# Function to get product information from barcode using Open Food Facts API
def get_product_info(barcode):
    url = f'https://world.openfoodfacts.org/api/v0/product/{barcode}.json'
    response = requests.get(url)

    if response.status_code == 200:
        product_data = response.json()
        if 'product' in product_data and 'product_name' in product_data['product']:
            return product_data['product']['product_name']
    return None

# Function to process the image and return barcode_info
def process_image(image_url):
    print(image_url)
    # Specify the image URL
    # image_url = "https://res.cloudinary.com/dw7kf4skd/image/upload/v1703026394/public/pe2tueyt4zpzalywleyi.jpg"

    # Download the image from the URL
    image_array = np.asarray(bytearray(urlopen(image_url).read()), dtype=np.uint8)
    image = cv2.imdecode(image_array, -1)

    # Check if the image was loaded successfully
    if image is None:
        return {'error': 'Unable to load the image from the specified URL'}

    # Preprocess the image
    preprocessed_image = preprocess_image(image)

    # Perform OCR on the preprocessed image
    results = pytesseract.image_to_string(preprocessed_image, lang='eng+tha', config='--psm 6')

    # Read search phrases from a text file
    with open(r'D:\3.1\4.1\ImgPro\ImgEXP\word.txt', 'r', encoding='utf-8') as file:
    # with open(r'/home/diplab/Desktop/chillmate_nas/ImgEXP/word.txt', 'r', encoding='utf-8') as file:
        search_phrases = [line.strip() for line in file.readlines()]

    # Specify the output file path
    output_file_path = r'D:\3.1\4.1\ImgPro\ImgEXP\wordsave.txt'
    # output_file_path = r'/home/diplab/Desktop/chillmate_nas/ImgEXP/wordsave.txt'
    # Dictionary to store Barcode and Product Information
    barcode_info = {}

    # Categorize text and search for barcodes
    categorize_text(results, search_phrases, output_file_path)
    barcodes = decode(image)

    if barcodes:
        for barcode in barcodes:
            barcode_data = barcode.data.decode('utf-8')
            barcode_info = search_barcodes_on_internet(barcodes, output_file_path, barcode_info)

    print("Processing finished.")
    print("Output saved in wordsave.txt")
    print(barcode_info)
    return barcode_info

def api_process_image(image_url):
    barcode_info = process_image(image_url)

    if 'product_info' in barcode_info and 'barcode' in barcode_info:
        product_name = barcode_info['product_info']
        barcode_number = barcode_info['barcode']

        # Define keywords for different categories
        categories_keywords = {
            'เนื้อสัตว์': ['meat', 'pork', 'beef', 'chicken', 'crayfish', 'duck', 'egg', 'fish', 'lamb', 'offal', 'shellfish', 'shrimp', 'squid','สันคอ', 'ซี่โครง', 'เนื้อสันนอก', 'เนื้อสันใน', 'เนื้อสะโพก', 'เนื้อน่อง', 'เนื้อติดหน้าอก', 'เนื้อติดดับขา', 'เนื้อส่วนหน้าท้อง', 'หาง', 'ปีกบน', 'น่องเล็ก', 'ปีกกลาง', 'ปีกปลาย', 'ขาไข่', 'สะโพกไก่', 'อกไก่', 'สันในไก่', 'น่องไก่', 'สะโพกไก่', 'ไก่ทั้งตัว', 'หนังไก่','ปูจั๊กจั่น', 'ปูทะเล', 'ปูแสม', 'ปูทองหลาง', 'ปูชัก', 'ปูดำ', 'ปูนา', 'ปูม้า', 'ปูทะเล', 'ปูไข่', 'ปูนิ่ม', 'ปูอลาสก้า', 'ปูขน', 'กั้ง', 'ไข่', 'ปลาสวาย', 'ปลาดุก', 'ปลาช่อน', 'ปลากระพง', 'ปลาสลิด', 'ปลาอินทรี', 'ปลาทู', 'ปลานิล', 'ปลาเก๋า', 'ปลาทับทิม', 'ปลาจะละเม็ดขาว', 'ปลาทูน่า', 'ปลาแซลม่อน', 'ปลาฉลาด', 'ปลาไหล', 'ปลาซิว', 'ปลาสำลี', 'ปลาสวาย', 'ปลากราย', 'ปลาตะเพียน', 'ปลาเนื้ออ่อน', 'ปลาหมอ', 'ตับหมู', 'หัวใจหมู', 'กระเพาะหมู', 'ปอดหมู', 'ไส้อ่อนหมู', 'ไส้ตันหมู', 'เซี้ยงจี้', 'ม้าม', 'กระเพาะวัว', 'ผ้าขี้ริ้ว', 'เลือดหมู', 'กึ๋นไก่', 'ตูดไก่', 'ตับไก่','หอยนางรม', 'หอยแมลงภู่', 'หอยแครง', 'หอยลอย', 'หอยหวาน', 'หอยหลอด', 'หอยตลับ', 'หอยเชลล์', 'หอยหมาก', 'หอยขม', 'หอยโข่ง', 'หอยเชอรี่', 'หอยเป๋าฮื้อ', 'หอยเม่น', 'หมึกล้วย', 'หมึกหอม', 'หมึกกระดอง', 'หมึกสาย', 'หมึกกระตอย', 'หมึกสาย', 'หมึกทาโกะ','กุ้งขาว', 'กุ้งแชบ๊วย', 'กุ้งโอคัก', 'กุ้งกุลาดำ', 'กุ้งลายเสือ', 'กุ้งก้ามกราม', 'กุ้งแม่น้ำ', 'กุ้งมังกร', 'กุ้งล็อบสเตอร์', 'กุ้งฝอย' ],
            'เห็ด': ['mushroom', 'เห็ด', 'golden needle mushroom', 'เห็ดเข็มทอง','เห็ดหอม', 'เห็ดหูหนูดำ', 'เห็นหูหนูขาว', 'เห็ดหลินจือ', 'เห็ดกระดุม', 'เห็นแชมปิญอง', 'เห็ดนางรม', 'เห็ดนางฟ้า', 'เห็นเป๋าฮื้อ', 'เห็ดฟาง', 'เห็ดโคน', 'เห็ดเผาะ', 'เห็ดขอนขาว', 'เห็ดยานางิ', 'เห็ดชิเมจิ'],
            'ผัก': ['bell pepper', 'พริกหยวก', 'raddish', 'หัวไชเท้า', 'spinach', 'ผักโขม', 'acacia', 'ชะอม', 'asparagus', 'หน่อไม้ฝรั่ง', 'baby corn', 'ข้าวโพดอ่อน', 'bamboo shoot', 'หน่อไม้', 'basil', 'โหระพา', 'bean sprout', 'ถั่วงอก', 'bitter been', 'สะตอ', 'bitter melon', 'มะระ', 'boy choy', 'กวางตุ้ง', 'broccoli', 'บร็อคโคลี', 'cabbage', 'กะหล่ำปลี', 'capsicum', 'carrot', 'แครอท', 'cauliflower', 'ดอกกะหล่ำ', 'celery', 'ขึ้นฉ่าย', 'chilli', 'พริก', 'ginger', 'ขิง', 'chinese cannage', 'ผักกาดขาว', 'corainder', 'ผักชี', 'cucumber', 'แตงกวา', 'egglant', 'มะเขือ', 'garlic', 'กระเทียม', 'garlic chives', 'อดกหอม', 'ivy gourd', 'ตำลึง', 'kaffir lime', 'มะกรูด', 'kale', 'คะน้า', 'lemon grass', 'ตะไคร้', 'long bean', 'ถั่วฝักยาว', 'lotus stem', 'รากบัว', 'neem', 'สะเดา', 'onion', 'หัวหอม', 'pepper', 'พริกไทย', 'peppermint', 'สาระแหน่', 'salad vegetable', 'กรีนโอ๊ค', 'green oak', 'เรดโอ๊ค', 'red oak', 'เรดคอรัล', 'red coral', 'บัตเตอร์เฮด', 'butterhead', 'คอส', 'cos', 'ผักกาดแก้ว', 'lceberg lettuce', 'เบบี้ร็อคเก็ต', 'baby rocket', 'wild rocket', 'ไวล์ดร็อคเก็ต', 'เรดิชิโอ', 'radicchio', 'mizuna', 'มิซูน่า', 'ฟิลเลย์ไแซ์เบิร์ก', 'frillice iceberg', 'ผักกาดหอม', 'green coral', 'เคล', 'vagetable', 'sesbania grandiflora', 'ดอกแค', 'spring onion', 'ต้นหอม', 'sweet basil', 'กะเพรา', 'water spinach', 'ผักบุ้ง', 'squash', 'ฝัก'],
            'ผลไม้': ['apple', 'avocado', 'banana', 'blueberry', 'cantaloupe', 'cherry', 'chinese pear', 'coconut', 'corn', 'custard apple', 'dragon fruit', 'durian', 'grapes', 'guava', 'jackfruit', 'jicama', 'kiwi', 'lemon', 'longan', 'lychee', 'mango', 'mangosteen', 'maprang', 'melon', 'orange', 'papaya', 'passion fruit', 'peach', 'pear', 'pineapple', 'plum', 'pomegranate', 'patato', 'pumpkin', 'rambutan', 'rose apple', 'salak', 'sapodilla', 'strawberry', 'taro', 'tomato', 'watermelon'],
            'เครื่องดื่ม': ['cola', 'น้ำ', 'tea', 'ชา', 'soda', 'coffee', 'กาแฟ', 'juice', ' เครื่องดื่ม', 'น้ำอัดลม', 'beverages', 'beer', 'spring water', 'mineral water', 'water', 'นม', 'milk', 'coke', 'เครื่องดื่ม', 'carbonated drinks', 'protein shakes'],
            'ผลิตภัณฑ์แปรรูปจากสัตว์': ['sausage','ไส้กรอก', 'ham', 'แฮม', 'หมูยอ', 'ชีส', 'cheese', 'โบโลน่า', 'Bologna', 'ไข่แดงเค็ม', 'เต้าหู้ไข่', 'เต้าหู้', 'ทอดมัน', 'พร้อมทาน', 'แช่แข็ง', 'ออมุก'],
            'อื่น ๆ': []
        }

        # Default category if not matched
        default_category = 'อื่น ๆ'

        # Find the matching category based on keywords
        for category, keywords in categories_keywords.items():
            if any(keyword.lower() in product_name.lower() for keyword in keywords):
                category_or_type = category
                break
        else:
            category_or_type = default_category

        result = {
            'product_name': product_name,
            'category_or_type': category_or_type,
            'barcode_number': barcode_number
        }

        return result
    else:
        return {'error': 'Product information not found.'}

# Route to trigger the image processing and return only data from barcode_info


# @app.route('/api/processImage', methods=['GET'])
# def api_process_image():
#     barcode_info = process_image()
#     return json.dumps(barcode_info, ensure_ascii=False).encode('utf8')

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=8001, debug=True)
