

from flask import Flask, request, jsonify
from exp import detect_date_from_image

app = Flask(__name__)

@app.route('/exp-api', methods=['POST'])
def predict():
    try:
        # Check if 'img_path' is provided in the request body
        data = request.json
        if data is None or 'img_path' not in data:
            return jsonify({'error': 'Image path not provided'}), 400

        # Get the image path from the request body
        img_path = data['img_path']

        # Call detect_date_from_image function from exp.py with the provided image path
        dates, months, years = detect_date_from_image(img_path)

        # Return the extracted date components as JSON response
        return jsonify({'dates': dates, 'months': months, 'years': years}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
