
# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import os

app = Flask(__name__)
CORS(app)
lastesttempeturedata = None

@app.route('/temperature', methods=['GET'])
def get_temperature():
    # Mocked temperature data
    if lastesttempeturedata :
        return jsonify({"temperature": lastesttempeturedata.get('temperature')})
    return jsonify({"temperature": "Not Availablable"})
        
    
@app.route('/temperature', methods=['POST'])
def receive_sensordata():
    # Mocked temperature data
    global lastesttempeturedata 
    data = request.get_json()
    lastesttempeturedata = data
    return 
    
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
