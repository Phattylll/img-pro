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
from categories_keywords import class_labels, class_details, class_unit, class_labels_meat, class_labels_fruit, class_labels_vegetable, meat_groups, fruit_groups, vegetable_groups

IMAGE_SIZE = (224, 224)
loaded_model = None

def load_image_common(img_path, target_size):
    try:
        if img_path.startswith(('http://', 'https://')):
            response = requests.get(img_path)
            response.raise_for_status()
            img = image.load_img(BytesIO(response.content), target_size=target_size)
        else:
            img = image.load_img(img_path, target_size=target_size)

        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array /= 255.0

        return img_array

    except requests.exceptions.HTTPError as e:
        raise e

    except Exception as e:
        raise e

def load_image(img_path):
    return load_image_common(img_path, IMAGE_SIZE)

def load_imagesub(img_path):
    return load_image_common(img_path, (244, 244))

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
        api_url = f'https://world.openfoodfacts.org/api/v0/product/{barcode}.json'
        response = requests.get(api_url)
        product_data = response.json()

        if product_data['status'] == 1:
            product_name = product_data['product']['product_name']
            return product_name
        else:
            return None

    except requests.exceptions.HTTPError as e:
        raise e

    except Exception as e:
        raise e

def load_sub_model(model_path, img_path, labels, groups):
    model = load_model(model_path)
    print(f"Sub-model loaded successfully: {model}")

    img_array = load_imagesub(img_path)
    print(f"Image loaded and preprocessed successfully for sub-model {img_array}")

    predictions = model.predict(img_array)
    sorted_indices = np.argsort(-predictions[0])
    most_confident_idx = sorted_indices[0]
    most_confident_label = labels[most_confident_idx]
    most_confident_confidence = predictions[0][most_confident_idx]
    sub_class_detail = []

    most_confident_subclass = groups[most_confident_label]
    sorted_subclass = sorted(most_confident_subclass, key=lambda x: x.lower())
    for sub_idx, sub_name in enumerate(sorted_subclass, start=1):
        sub_confidence = predictions[0][labels.index(most_confident_label)] if sub_name in most_confident_subclass else 0
        print(f"{sub_name}")
        sub_class_detail.append(sub_name)

    for idx in sorted_indices[1:]:
        current_label = labels[idx]
        current_subclass = groups[current_label]
        sorted_current_subclass = sorted(current_subclass, key=lambda x: x.lower())
        for sub_idx, sub_name in enumerate(sorted_current_subclass, start=1):
            sub_confidence = predictions[0][labels.index(current_label)] if sub_name in current_subclass else 0
            print(f"{sub_name}")
            sub_class_detail.append(sub_name)

    return most_confident_label, most_confident_confidence, sub_class_detail

def predict_class(img_path):
    try:
        status = 'success'
        Img_path = None
        barcode = decode_barcode(img_path)
        Img_path = img_path

        if barcode:
            product_name = fetch_product_info(barcode)

            if product_name:
                return {
                    'status': status,
                    'Img_path': Img_path,
                    'barcode': barcode,
                    'predicted_class': 'อื่น ๆ',
                    'product_name': product_name,
                    'sub_class': class_labels,
                    'subclass_unit': class_unit,
                }
            else:
                return {
                    'status': status,
                    'Img_path': Img_path,
                    'barcode': barcode,
                    'predicted_class': 'อื่น ๆ',
                    'product_name': 'No data in open food fact api',
                    'sub_class': class_labels,
                    'subclass_unit': class_unit,
                }

        img_array = load_image(img_path)
        loaded_model = load_model(r'D:\3.1\4.1\ImgPro\Lib\food_classtest4')
        predictions = loaded_model.predict(img_array)
        confidence = np.max(predictions) * 100
        predicted_class_index = np.argmax(predictions)

        predicted_class = class_labels[predicted_class_index]
        class_details_result = class_details.get(predicted_class, {})
        class_unit_result = class_unit.get(predicted_class, [])

        if predicted_class in {"ผลไม้", "ผัก", "เนื้อสัตว์"}:
            model_path, labels, groups = {
                "ผลไม้": ("D:\\3.1\\4.1\\ImgPro\\Lib\\groupFruit_class_epoch_200.h5", class_labels_fruit, fruit_groups),
                "ผัก": ("D:\\3.1\\4.1\\ImgPro\\Lib\\groupVeg_class_epoch_200.h5", class_labels_vegetable, vegetable_groups),
                "เนื้อสัตว์": ("D:\\3.1\\4.1\\ImgPro\\Lib\\groupMeat_class_epoch_200.h5", class_labels_meat, meat_groups),
            }[predicted_class]

            most_confident_label, sub_class_confidence, sub_class_detail = load_sub_model(model_path, img_path, labels, groups)

            if predicted_class == "ผลไม้":
                if most_confident_label == 'Green and Brown Fruits':
                    sub_class = 'ผลไม้โทนสีเขียวและสีน้ำตาล'
                elif most_confident_label == 'Red and Blue Fruits':
                    sub_class = 'ผลไม้โทนสีแดงและสีน้ำเงิน'
                elif most_confident_label == 'Yellow and Orange Fruits':
                    sub_class = 'ผลไม้โทนสีเหลืองและสีส้ม'

            elif predicted_class == "ผัก":
                if most_confident_label == 'Green vegetables':
                    sub_class = 'ผักโทนสีเขียว'
                elif most_confident_label == 'Red and orange vegetables':
                    sub_class = 'ผักโทนสีแดงและสีส้ม'
                elif most_confident_label == 'White and light-colored vegetables':
                    sub_class = 'ผักโทนสีสว่าง'

            elif predicted_class == "เนื้อสัตว์":
                if most_confident_label == 'OtherMeats and Mushroom':
                    sub_class = 'เห็ดหรือเนื้อสัตว์อื่น ๆ '
                elif most_confident_label == 'Poultry':
                    sub_class = 'สัตว์ปีก'
                elif most_confident_label == 'Seafood':
                    sub_class = 'อาหารทะเล'

            return {
                'status': status,
                'Img_path': Img_path,
                'predicted_class': predicted_class,
                'confidence': f'{confidence:.4f}%',
                'barcode': None,
                'product_name': None,
                'class_details': class_details_result,
                'class_unit': class_unit_result,
                'sub_class': sub_class,
                'sub_class_detail': sub_class_detail,
            }

        else:
            predicted_sub_class = 'other'
            predicted_sub_class_detail = {}

        result = {
            'status': status,
            'Img_path': Img_path,
            'predicted_class': predicted_class,
            'confidence': f'{confidence:.4f}%',
            'barcode': None,
            'product_name': None,
            'class_details': class_details_result,
            'class_unit': class_unit_result,
            'sub_class': sub_class,
            'sub_class_detail': sub_class_detail,
        }

        return result

    except Exception as e:
        status = 'error'
        return {'status': status, 'Img_path': Img_path, 'error': str(e)}
