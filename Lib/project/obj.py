import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import os
import sys
import requests
from io import BytesIO
from pyzbar.pyzbar import decode

sys.path.append(r'D:\3.1\4.1\ImgPro\Lib')
from categories_keywords import class_labels, class_details, class_unit, class_labels_meat, class_labels_fruit, class_labels_vegetable, meat_groups, fruit_groups, vegetable_groups  # Assuming you have class_unit and class_labels_fruit defined

IMAGE_SIZE = (224, 224)

# Load the Trained Model
loaded_model = None  # Initialize as None

def load_model(model_path):
    global loaded_model
    if loaded_model is None:
        loaded_model = tf.keras.models.load_model(model_path)
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

def predict_sub_class(img_path, sub_model_path, sub_class_labels, subclass_details):
    try:
        sub_model = load_model(sub_model_path)
        sub_img_array = load_image(img_path)
        sub_predictions = sub_model.predict(sub_img_array)
        sub_class_index = np.argmax(sub_predictions)
        sub_class_label = sub_class_labels[sub_class_index]
        sub_class_detail = subclass_details.get(sub_class_label, {})  # Retrieve subclass details
        return sub_class_label, sub_class_detail

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
        loaded_model = load_model(r'D:\3.1\4.1\ImgPro\Lib\food_classtest4')
        predictions = loaded_model.predict(img_array)

        # Get predicted class
        predicted_class_index = np.argmax(predictions)
        confidence = np.max(predictions) * 100

        if confidence >= 50:
            predicted_class = class_labels[predicted_class_index]
            class_details_result = class_details.get(predicted_class, {})  # Retrieve class details
            class_unit_result = class_unit.get(predicted_class, [])

            # Add sub-classification based on predicted class
            if predicted_class == "ผลไม้":
                sub_model_path = r"D:\3.1\4.1\ImgPro\Lib\groupFruit_class_epoch_200.h5"
                sub_class_labels = class_labels_fruit
                subclass_details = fruit_groups
                sub_class, sub_class_detail = predict_sub_class(img_path, sub_model_path, sub_class_labels, subclass_details)
            elif predicted_class == "ผัก":
                sub_model_path = r"D:\3.1\4.1\ImgPro\Lib\groupVeg_class_epoch_200.h5"
                sub_class_labels = class_labels_vegetable
                subclass_details = vegetable_groups
                sub_class, sub_class_detail = predict_sub_class(img_path, sub_model_path, sub_class_labels, subclass_details)
            elif predicted_class == "เนื้อสัตว์":
                sub_model_path = r"D:\3.1\4.1\ImgPro\Lib\groupMeat_class_epoch_200.h5"
                sub_class_labels = class_labels_meat
                subclass_details = meat_groups
                sub_class, sub_class_detail = predict_sub_class(img_path, sub_model_path, sub_class_labels, subclass_details)
            else:
                sub_class = []
                sub_class_detail = {}

        else:
            predicted_class = 'other'
            class_details_result = {}
            class_unit_result = []
            sub_class = []
            sub_class_detail = {}

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
            'sub_class': sub_class,  # Include sub-classification in the result
            'sub_class_detail': sub_class_detail,  # Include subclass details in the result
        }

        return result

    except Exception as e:
        # Move the status variable outside the try block to ensure it's defined even if an exception occurs
        status = 'error'
        return {'status': status, 'Img_path': Img_path, 'error': str(e)}
