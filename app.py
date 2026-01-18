
# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import os

app = Flask(__name__)
CORS(app)
lastesttempeturedata = None

@app.route('/', methods=['GET'])
def root():
    return jsonify({"message": "Temperature Server", "endpoints": ["/temperature"]})

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
    return jsonify({"status": "success"}), 200 

@app.route('/temperature/alert', methods=['POST'])
def check_temperature_alert():
    """
    Check if current temperature exceeds threshold and send email alert
    Expects JSON: {"current_temperature": <value>, "threshold_temperature": <value>}
    """
    try:
        data = request.get_json()
        current_temp = data.get('current_temperature')
        threshold_temp = data.get('threshold_temperature')
        
        if current_temp is None or threshold_temp is None:
            return jsonify({"status": "error", "message": "Missing current_temperature or threshold_temperature"}), 400
        
        current_temp = float(current_temp)
        threshold_temp = float(threshold_temp)
        
        # Check if current temperature exceeds threshold
        if current_temp > threshold_temp:
            # Send email alert
            email_response = send_temperature_alert_email(current_temp, threshold_temp)
            return jsonify({
                "status": "alert_sent",
                "message": f"Temperature {current_temp}°C exceeds threshold {threshold_temp}°C. Email alert sent!",
                "current_temperature": current_temp,
                "threshold_temperature": threshold_temp,
                "email_response": email_response
            }), 200
        else:
            return jsonify({
                "status": "ok",
                "message": f"Temperature {current_temp}°C is within threshold {threshold_temp}°C",
                "current_temperature": current_temp,
                "threshold_temperature": threshold_temp
            }), 200
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


import os
import requests

def send_temperature_alert_email(current_temperature, threshold_temperature):
    """
    Send email alert when temperature exceeds threshold
    """
    subject = f"🚨 Temperature Alert: {current_temperature}°C exceeds {threshold_temperature}°C"
    text = f"""
    TEMPERATURE ALERT!
    
    Current Temperature: {current_temperature}°C
    Temperature Threshold: {threshold_temperature}°C
    
    The room temperature has exceeded the set threshold. Please take action.
    
    This is an automated alert from your Temperature Monitoring System.
    """
    
    try:
        response = requests.post(
            "https://api.mailgun.net/v3/sandboxc72ebb5f873545dab6a76ccbbada1ee8.mailgun.org/messages",
            auth=("api", os.getenv('API_KEY', '308ece5584d7caa50f867a625b8afaac-42b8ce75-5d3b502e')),
            data={
                "from": "Mailgun Sandbox <postmaster@sandboxc72ebb5f873545dab6a76ccbbada1ee8.mailgun.org>",
                "to": "paul hung <paulhung554@gmail.com>",
                "subject": subject,
                "text": text
            }
        )
        return {"status": "sent", "response_code": response.status_code}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

 
