# coding: utf-8

from flask import Flask, Response, request
import cloudinary_conf as conf
from cloudinary.uploader import upload
import requests
import os
import time
import test2
from test2 import api_process_image
import json


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False 

def download_image(file_url):
    resp = requests.get(file_url)
    if not os.path.isdir("downloaded_image"):
        os.mkdir("downloaded_image")
    timestamp_str = time.strftime("%Y%m%d-%H%M%S")
    file_ext = os.path.splitext(file_url)[1]
    collect_path = "./downloaded_image/" + timestamp_str + file_ext
    with open(collect_path, "wb") as f:
        f.write(resp.content)
    return collect_path
    # delete_file(collect_path)


def delete_file(collect_path):
    time.sleep(10)
    if os.path.isfile(collect_path):
        os.remove(collect_path)

def upload_file(filename):
    return upload(filename)

@app.route('/api/process-image', methods=['POST'])
def process_received_image():
    try:
        file_url = request.json.get('file_url')
        # collect_path = download_image(file_url)
        # latest_image_path = "./downloaded_image/" + sorted(os.listdir("./downloaded_image"), key=os.path.getmtime, reverse=True)[0]

        # Add the image processing code here
        # ...
        barcode_info = api_process_image(file_url)
        # For now, let's return a simple response
        # return {'status': 'success', 'message': 'Image processed successfully.', 'data':barcode_info}\
        json_data = json.dumps({
            'status': 'success', 
            'message': 'Image processed successfully.', 
            'data':barcode_info
        }, ensure_ascii=False).encode('utf8')
        return Response(json_data, content_type='application/json; charset=utf-8')
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8002, debug=True)
