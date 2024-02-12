import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import os
import sys
import requests
from io import BytesIO
from pyzbar.pyzbar import decode

sys.path.append(r'D:\3.1\4.1\ImgPro\Lib')
from categories_keywords import class_labels, class_details, class_unit  # Assuming you have class_unit defined

IMAGE_SIZE = (224, 224)

# Load the Trained Model
loaded_model = None  # Initialize as None

def load_model():
    global loaded_model
    if loaded_model is None:
        loaded_model = tf.keras.models.load_model(r'D:\3.1\4.1\ImgPro\Lib\food_classtest4')
    return loaded_model

def load_image(img_path):
    try:
        if img_path.startswith(('http://', 'https://')):
            # Load image from URL
            response = requests.get(img_path)
            response.raise_for_status()  # Raise an exception for HTTP errors
            img = image.load_img(BytesIO(response.content), target_size=IMAGE_SIZE)
        else:
            # Load local image
            img = image.load_img(img_path, target_size=IMAGE_SIZE)

        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array /= 255.0

        return img_array

    except requests.exceptions.HTTPError as e:
        raise e

    except Exception as e:
        raise e

def decode_barcode(img_path):
    try:
        if img_path.startswith(('http://', 'https://')):
            # Load image from URL
            response = requests.get(img_path)
            response.raise_for_status()  # Raise an exception for HTTP errors
            img = image.load_img(BytesIO(response.content))
        else:
            # Load local image
            img = image.load_img(img_path)

        img_array = image.img_to_array(img).astype(np.uint8)
        barcodes = decode(img_array)

        if barcodes:
            return barcodes[0].data.decode('utf-8')
        else:
            return None

    except requests.exceptions.HTTPError as e:
        raise e

    except Exception as e:
        raise e

def fetch_product_info(barcode):
    try:
        # Fetch product information from Open Food Facts API
        api_url = f'https://world.openfoodfacts.org/api/v0/product/{barcode}.json'
        response = requests.get(api_url)
        product_data = response.json()

        if product_data['status'] == 1:  # Product found in Open Food Facts
            product_name = product_data['product']['product_name']
            return product_name
        else:
            return None

    except requests.exceptions.HTTPError as e:
        raise e

    except Exception as e:
        raise e

def predict_class(img_path):
    try:
        # Initialize variables
        status = 'success'
        Img_path = None

        # Decode barcode
        barcode = decode_barcode(img_path)
        Img_path = img_path  # Set Img_path

        if barcode:
            # Fetch product info from Open Food Facts
            product_name = fetch_product_info(barcode)

            if product_name:
                return {'status': status, 'Img_path': Img_path, 'barcode': barcode, 'predicted_class': 'อื่น ๆ', 'product_name': product_name}
            else:
                return {'status': status, 'Img_path': Img_path, 'barcode': barcode, 'predicted_class': 'อื่น ๆ', 'product_name': "No product name in open food fact api"}

        # Preprocess the image
        img_array = load_image(img_path)

        # Make predictions
        loaded_model = load_model()
        predictions = loaded_model.predict(img_array)

        # Get predicted class
        predicted_class_index = np.argmax(predictions)
        confidence = np.max(predictions) * 100

        if confidence >= 50:
            predicted_class = class_labels[predicted_class_index]
            class_details_result = class_details.get(predicted_class, {})  # Retrieve class details
            class_unit_result = class_unit.get(predicted_class, [])
        else:
            predicted_class = 'other'
            class_details_result = {}
            class_unit_result = []

        # Include only the desired fields in the result
        result = {
            'status': status,
            'Img_path': Img_path,
            'predicted_class': predicted_class,
            'confidence': f'{confidence:.4f}%',  # Display confidence with four decimal places
            'barcode': None,  # Since no barcode was found
            'product_name': None,  # Product name not applicable
            'class_details': class_details_result,  # Include class details in the result
            'class_unit': class_unit_result,
        }

        return result

    except Exception as e:
        return {'status': 'error', 'Img_path': Img_path, 'error': str(e)}
