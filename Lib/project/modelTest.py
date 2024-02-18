import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import sys

sys.path.append(r'D:\3.1\4.1\ImgPro\Lib')
from categories_keywords import class_labels, class_details, class_unit, class_labels_meat, class_labels_fruit, class_labels_vegetable, meat_groups, fruit_groups, vegetable_groups
# Load the trained model
model = load_model(r"D:\3.1\4.1\ImgPro\Lib\groupFruit_class_epoch_200.h5")

# Load and preprocess the image to be predicted
img_path = r"D:\3.1\4.1\ImgPro\ImgFood\kaggle\train\fruit\Red and Blue Fruits\tomato\Image_6.jpg"
img = image.load_img(img_path, target_size=(244, 244))
img_array = image.img_to_array(img)
img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
img_array /= 255.  # Normalize the image data

# Make prediction
predictions = model.predict(img_array)

# Get indices of predicted classes sorted by confidence level in descending order
sorted_indices = np.argsort(-predictions[0])


# Print predicted labels arranged by confidence level
print("Predicted Labels (arranged by confidence):")
for idx, ordinal in enumerate(sorted_indices, start=1):
    predicted_label = class_labels_fruit[ordinal]
    confidence = predictions[0][ordinal]
    print(f"{idx}. Label: {predicted_label} - Confidence: {confidence}")

    # Access the corresponding subclass from fruit_groups
    subclass = fruit_groups[predicted_label]

    # Sort the subclass based on confidence level and alphabetically
    sorted_subclass = sorted(subclass, key=lambda x: (predictions[0][class_labels_fruit.index(predicted_label)], x.lower()))

    # Print the sorted subclass with confidence levels
    print(f"   Subclass (arranged by confidence and alphabetically):")
    for sub_idx, sub_name in enumerate(sorted_subclass, start=1):
        sub_confidence = predictions[0][class_labels_fruit.index(predicted_label)] if sub_name in fruit_groups[predicted_label] else 0
        print(f"      {sub_idx}. {sub_name} - Confidence: {sub_confidence * 100:.2f}%")