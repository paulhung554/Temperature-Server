
# app.py
from flask import Flask, jsonify
import random

app = Flask(__name__)

@app.route('/temperature', methods=['GET'])
def get_temperature():
    # Mocked temperature data
    temperature = round(random.uniform(20, 30), 2)
    return jsonify({"temperature": temperature})

if __name__ == '__main__':
    app.run()
