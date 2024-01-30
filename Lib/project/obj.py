import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import os
import sys
import requests
from io import BytesIO

sys.path.append(r'D:\3.1\4.1\ImgPro\Lib')
from categories_keywords import class_labels, class_details

IMAGE_SIZE = (224, 224)

# Load the Trained Model
loaded_model = None  # Initialize as None

def load_model():
    global loaded_model
    if loaded_model is None:
        loaded_model = tf.keras.models.load_model(r'D:\3.1\4.1\ImgPro\Lib\food_class')
    return loaded_model

def load_image(img_path):
    try:
        if img_path.startswith(('http://', 'https://')):
            # Load image from URL
            response = requests.get(img_path)
            img = image.load_img(BytesIO(response.content), target_size=IMAGE_SIZE)
        else:
            # Load local image
            img = image.load_img(img_path, target_size=IMAGE_SIZE)

        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array /= 255.0

        return img_array

    except Exception as e:
        raise e

def predict_class(img_path):
    try:
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
            class_items = class_details.get(predicted_class, [])
        else:
            predicted_class = 'other'
            class_items = []

        # Include only the desired fields in the result
        result = {
            'class_items': class_items,
            'confidence': f'{confidence:.2f}%',
            'predicted_class': predicted_class,
            
        }

        return result

    except Exception as e:
        return {'error': str(e)}
