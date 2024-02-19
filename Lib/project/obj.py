import tensorflow as tf
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
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

# def load_model(model_path):
#     global loaded_model
#     try:
#         if loaded_model is None:
#             loaded_model = tf.keras.models.load_model(model_path)
#         return loaded_model
#     except Exception as e:
#         raise RuntimeError(f"Error loading model from {model_path}: {str(e)}")


def load_image(img_path):
    try:
        if img_path.startswith(('http://', 'https://')):
            response = requests.get(img_path)
            response.raise_for_status()
            img = image.load_img(BytesIO(response.content), target_size=IMAGE_SIZE)
        else:
            img = image.load_img(img_path, target_size=IMAGE_SIZE)

        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array /= 255.0

        return img_array

    except requests.exceptions.HTTPError as e:
        raise e

    except Exception as e:
        raise e
    
def load_imagesub(img_path):
    try:
        if img_path.startswith(('http://', 'https://')):
            response = requests.get(img_path)
            response.raise_for_status()
            img = image.load_img(BytesIO(response.content), target_size=(244, 244))
        else:
            img = image.load_img(img_path, target_size=(244, 244))

        img_array2 = image.img_to_array(img)
        img_array2 = np.expand_dims(img_array2, axis=0)  # Fix typo here, replace img_array with img_array2
        img_array2 /= 255.0

        return img_array2

    except requests.exceptions.HTTPError as e:
        raise e

    except Exception as e:
        raise e


def decode_barcode(img_path):
    try:
        if img_path.startswith(('http://', 'https://')):
            response = requests.get(img_path)
            response.raise_for_status()
            img = image.load_img(BytesIO(response.content))
        else:
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
        loaded_model = load_model(r'D:\3.1\4.1\ImgPro\Lib\food_classtest4')
        predictions = loaded_model.predict(img_array)

        # Get predicted class
        predicted_class_index = np.argmax(predictions)
        confidence = np.max(predictions) * 100

        predicted_class = class_labels[predicted_class_index]
        class_details_result = class_details.get(predicted_class, {})  # Retrieve class details
        class_unit_result = class_unit.get(predicted_class, [])

        # Add sub-classification based on predicted class
        if predicted_class == "ผลไม้":
            model = load_model(r"D:\3.1\4.1\ImgPro\Lib\groupFruit_class_epoch_200.h5")
            print(f"Sub-model loaded successfully: {model}")
            img_array = load_imagesub(img_path)
            print(f"Image loaded and preprocessed successfully for sub-model{img_array}")       
            predictions = model.predict(img_array)
            sorted_indices = np.argsort(-predictions[0])
            most_confident_idx = sorted_indices[0]
            most_confident_label = class_labels_fruit[most_confident_idx]
            most_confident_confidence = predictions[0][most_confident_idx]
            sub_class_detail = []
            # sub_class = {}
                # Check for specific conditions and set 'sub_class' accordingly
            if most_confident_label == 'Green and Brown Fruits':
                sub_class = 'ผลไม้โทนสีเขียวและสีน้ำตาล'
            elif most_confident_label == 'Red and Blue Fruits':
                sub_class = 'ผลไม้โทนสีแดงและสีน้ำเงิน'
            elif most_confident_label == 'Yellow and Orange Fruits':
                sub_class = 'ผลไม้โทนสีเหลืองและสีส้ม'
            print(f"1. Label: {most_confident_label} - Confidence: {most_confident_confidence}")
            # Print corresponding fruit_groups for the most confident label
            most_confident_subclass = fruit_groups[most_confident_label]
            sorted_subclass = sorted(most_confident_subclass, key=lambda x: x.lower())
            for sub_idx, sub_name in enumerate(sorted_subclass, start=1):
                sub_confidence = predictions[0][class_labels_fruit.index(most_confident_label)] if sub_name in most_confident_subclass else 0
                # print(f"{sub_name} - Confidence: {sub_confidence * 100:.2f}%")
                print(f"{sub_name}")
                sub_class_detail.append(sub_name)
            # Print fruit_groups for the rest of the class_labels_fruit
            for idx in sorted_indices[1:]:
                current_label = class_labels_fruit[idx]
                current_subclass = fruit_groups[current_label]
                sorted_current_subclass = sorted(current_subclass, key=lambda x: x.lower())
                # print(f"\n{idx}. {current_label} - Confidence:")
                for sub_idx, sub_name in enumerate(sorted_current_subclass, start=1):
                    sub_confidence = predictions[0][class_labels_fruit.index(current_label)] if sub_name in current_subclass else 0
                    print(f"{sub_name}")
                    sub_class_detail.append(sub_name)


        elif predicted_class == "ผัก":
            model = load_model(r"D:\3.1\4.1\ImgPro\Lib\groupVeg_class_epoch_200.h5")
            print(f"Sub-model loaded successfully: {model}")

            # Load and preprocess the image using load_imagesub function
            img_array = load_imagesub(img_path)
            print(f"Image loaded and preprocessed successfully for sub-model {img_array}")       
            predictions = model.predict(img_array)
            sorted_indices = np.argsort(-predictions[0])
            most_confident_idx = sorted_indices[0]
            most_confident_label = class_labels_vegetable[most_confident_idx]
            most_confident_confidence = predictions[0][most_confident_idx]
            sub_class_detail = []
            if most_confident_label == 'Green vegetables':
                sub_class = 'ผักโทนสีเขียว'
            elif most_confident_label == 'Red and orange vegetables':
                sub_class = 'ผักโทนสีแดงและสีส้ม'
            elif most_confident_label == 'White and light-colored vegetables':
                sub_class = 'ผักโทนสีสว่าง'
            print(f"1. Label: {most_confident_label} - Confidence: {most_confident_confidence}")
            
            # Print corresponding vegetable_groups for the most confident label
            most_confident_subclass = vegetable_groups[most_confident_label]
            sorted_subclass = sorted(most_confident_subclass, key=lambda x: x.lower())
            for sub_idx, sub_name in enumerate(sorted_subclass, start=1):
                sub_confidence = predictions[0][class_labels_vegetable.index(most_confident_label)] if sub_name in most_confident_subclass else 0
                print(f"{sub_name}")
                sub_class_detail.append(sub_name)

            # Print vegetable_groups for the rest of the class_labels_vegetable
            for idx in sorted_indices[1:]:
                current_label = class_labels_vegetable[idx]
                current_subclass = vegetable_groups[current_label]
                sorted_current_subclass = sorted(current_subclass, key=lambda x: x.lower())
                for sub_idx, sub_name in enumerate(sorted_current_subclass, start=1):
                    sub_confidence = predictions[0][class_labels_vegetable.index(current_label)] if sub_name in current_subclass else 0
                    print(f"{sub_name}")
                    sub_class_detail.append(sub_name)

        elif predicted_class == "เนื้อสัตว์":
            model = load_model(r"D:\3.1\4.1\ImgPro\Lib\groupMeat_class_epoch_200.h5")
            print(f"Sub-model loaded successfully: {model}")

            # Load and preprocess the image using load_imagesub function
            img_array = load_imagesub(img_path)
            print(f"Image loaded and preprocessed successfully for sub-model {img_array}")       
            predictions = model.predict(img_array)
            sorted_indices = np.argsort(-predictions[0])
            most_confident_idx = sorted_indices[0]
            most_confident_label = class_labels_meat[most_confident_idx]
            most_confident_confidence = predictions[0][most_confident_idx]
            sub_class_detail = []
            if most_confident_label == 'OtherMeats and Mushroom':
                sub_class = 'เห็ดหรือเนื้อสัตว์อื่น ๆ '
            elif most_confident_label == 'Poultry':
                sub_class = 'สัตว์ปีก'
            elif most_confident_label == 'Seafood':
                sub_class = 'อาหารทะเล'
            print(f"1. Label: {most_confident_label} - Confidence: {most_confident_confidence}")
            
            # Print corresponding meat_groups for the most confident label
            most_confident_subclass = meat_groups[most_confident_label]
            sorted_subclass = sorted(most_confident_subclass, key=lambda x: x.lower())
            for sub_idx, sub_name in enumerate(sorted_subclass, start=1):
                sub_confidence = predictions[0][class_labels_meat.index(most_confident_label)] if sub_name in most_confident_subclass else 0
                print(f"{sub_name}")
                sub_class_detail.append(sub_name)

            # Print meat_groups for the rest of the class_labels_meat
            for idx in sorted_indices[1:]:
                current_label = class_labels_meat[idx]
                current_subclass = meat_groups[current_label]
                sorted_current_subclass = sorted(current_subclass, key=lambda x: x.lower())
                for sub_idx, sub_name in enumerate(sorted_current_subclass, start=1):
                    sub_confidence = predictions[0][class_labels_meat.index(current_label)] if sub_name in current_subclass else 0
                    print(f"{sub_name}")
                    sub_class_detail.append(sub_name)


        else:
            predicted_sub_class = 'other'
            predicted_sub_class_detail = {}

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
            'sub_class': sub_class, 
            'sub_class_detail': sub_class_detail, 
            }

        return result

    except Exception as e:
        # Move the status variable outside the try block to ensure it's defined even if an exception occurs
        status = 'error'
        return {'status': status, 'Img_path': Img_path, 'error': str(e)}
