
# app.py
from flask import Flask, jsonify
from flask_cors import CORS
import random
import os

app = Flask(__name__)
CORS(app)

@app.route('/temperature', methods=['GET'])
def get_temperature():
    # Mocked temperature data
    temperature = round(random.uniform(20, 30), 2)
    return jsonify({"temperature": temperature})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
