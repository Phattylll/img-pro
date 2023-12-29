# coding: utf-8

import sys
from flask import Flask

sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)

@app.route('/api/thai', methods=['GET'])
def thai_response():
    thai_text = "สวัสดี"
    return thai_text

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
