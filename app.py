# Temperature Monitoring Server with SendGrid Email Alerts
# This file is self-contained for Render deployment

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)
lastesttempeturedata = None

# Configuration
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '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')
ALERT_EMAIL = "paulhung554@gmail.com"

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


# ============================================================================
# EMAIL NOTIFICATION SYSTEM - SendGrid Integration
# Self-contained for Render deployment
# ============================================================================

def send_temperature_alert_email(current_temperature, threshold_temperature):
    """
    Send email alert when temperature exceeds threshold using SendGrid API.
    
    Args:
        current_temperature (float): Current temperature in Celsius
        threshold_temperature (float): Temperature threshold in Celsius
        
    Returns:
        dict: Status and response information
    """
    if not SENDGRID_API_KEY:
        return {
            "status": "failed", 
            "error": "SENDGRID_API_KEY environment variable not configured"
        }
    
    subject = f"🚨 Temperature Alert: {current_temperature}°C exceeds {threshold_temperature}°C"
    
    text_content = f"""
TEMPERATURE ALERT!

Current Temperature: {current_temperature}°C
Temperature Threshold: {threshold_temperature}°C
Alert Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The room temperature has exceeded the set threshold. Please take action.

This is an automated alert from your Temperature Monitoring System.
"""
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="border-left: 4px solid #ff6b6b; padding: 20px; background-color: #ffe0e0;">
                <h2 style="color: #ff6b6b; margin: 0 0 10px 0;">🚨 TEMPERATURE ALERT</h2>
                <p><strong>Current Temperature:</strong> {current_temperature}°C</p>
                <p><strong>Threshold:</strong> {threshold_temperature}°C</p>
                <p><strong>Excess:</strong> {current_temperature - threshold_temperature}°C above threshold</p>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="color: #666; font-size: 12px;">This is an automated alert from your Temperature Monitoring System.</p>
            </div>
        </body>
    </html>
    """
    
    try:
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {SENDGRID_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "personalizations": [
                    {
                        "to": [
                            {
                                "email": ALERT_EMAIL,
                                "name": "Temperature Alert System"
                            }
                        ],
                        "subject": subject
                    }
                ],
                "from": {
                    "email": ALERT_EMAIL,
                    "name": "Temperature Monitoring System"
                },
                "content": [
                    {
                        "type": "text/plain",
                        "value": text_content
                    },
                    {
                        "type": "text/html",
                        "value": html_content
                    }
                ],
                "reply_to": {
                    "email": ALERT_EMAIL
                }
            }
        )
        
        if response.status_code == 202:
            return {
                "status": "sent",
                "message": "Email sent successfully",
                "response_code": response.status_code
            }
        else:
            return {
                "status": "failed",
                "error": f"SendGrid API error: {response.status_code}",
                "details": response.text
            }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }


def send_custom_notification(subject, message, recipient_email=None):
    """
    Send a custom email notification via SendGrid.
    
    Args:
        subject (str): Email subject
        message (str): Email message content
        recipient_email (str): Recipient email address (defaults to ALERT_EMAIL)
        
    Returns:
        dict: Status and response information
    """
    if not SENDGRID_API_KEY:
        return {
            "status": "failed",
            "error": "SENDGRID_API_KEY environment variable not configured"
        }
    
    recipient = recipient_email or ALERT_EMAIL
    
    try:
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {SENDGRID_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "personalizations": [
                    {
                        "to": [{"email": recipient}],
                        "subject": subject
                    }
                ],
                "from": {
                    "email": ALERT_EMAIL,
                    "name": "System Notification"
                },
                "content": [
                    {
                        "type": "text/plain",
                        "value": message
                    }
                ]
            }
        )
        
        if response.status_code == 202:
            return {
                "status": "sent",
                "message": "Email sent successfully",
                "response_code": response.status_code
            }
        else:
            return {
                "status": "failed",
                "error": f"SendGrid API error: {response.status_code}"
            }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }
