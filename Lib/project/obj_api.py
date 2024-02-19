from flask import Flask, jsonify, request
from obj import predict_class

app = Flask(__name__)

@app.route('/obj-api', methods=['POST'])
def predict():
    try:
        # Get image path from the JSON payload
        data = request.get_json()
        img_path = data.get('img_path')

        # Predict the class
        result = predict_class(img_path)

        # Wrap the result in a dictionary with key 'class'
        response = {'class': result}

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
