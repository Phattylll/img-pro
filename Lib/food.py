import cv2
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
import numpy as np

# Load the pre-trained MobileNetV2 model
base_model = MobileNetV2(weights='imagenet', include_top=True)

# Function to preprocess the image
def preprocess_image(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    return preprocess_input(img_array)

# Function to predict the class of the image
def predict_fruit_vegetable(img_path):
    processed_img = preprocess_image(img_path)
    predictions = base_model.predict(processed_img)
    decoded_predictions = decode_predictions(predictions)

    # Assuming the top prediction is the class of interest
    top_prediction = decoded_predictions[0][0]
    class_label = top_prediction[1]
    confidence = top_prediction[2]

    return class_label, confidence

# Function to display the image with bounding box
def display_image_with_bounding_box(img_path, class_label, confidence):
    img = cv2.imread(img_path)
    img = cv2.resize(img, (224, 224))  # Resize image to match the model input size

    # Draw bounding box
    color = (0, 255, 0)  # Green color for bounding box
    cv2.putText(img, f"{class_label} ({confidence:.2f})", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.imshow('Food Recognition', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Example usage
img_path = r'D:\3.1\4.1\ImgPro\ImgFood\5.jpg'
class_label, confidence = predict_fruit_vegetable(img_path)
print('Predicted Class:', class_label)
print('Confidence:', confidence)

# Display the image with bounding box
display_image_with_bounding_box(img_path, class_label, confidence)