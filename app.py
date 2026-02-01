# Temperature Monitoring Server with SendGrid Email Alerts
# This file is self-contained for Render deployment

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests
import json
import logging
import sys
from datetime import datetime

# Configure logging for Render – stdout is captured in Render logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
lastesttempeturedata = None

# Configuration
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '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')
ALERT_EMAIL = "paulhung554@gmail.com"


@app.before_request
def log_request():
    """Log incoming requests for debugging."""
    logger.info("Request: %s %s", request.method, request.path)


@app.after_request
def log_response(response):
    """Log response status so 500s are visible with context."""
    if response.status_code >= 400:
        logger.warning("Response: %s %s -> %s", request.method, request.path, response.status_code)
    return response


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
        data = request.get_json(silent=True)
        logger.info("temperature/alert payload: %s", data)

        if data is None:
            logger.warning("temperature/alert: invalid or missing JSON body")
            return jsonify({"status": "error", "message": "Invalid or missing JSON body"}), 400

        current_temp = data.get('current_temperature')
        threshold_temp = data.get('threshold_temperature')

        if current_temp is None or threshold_temp is None:
            logger.warning("temperature/alert: missing fields (current_temperature=%s, threshold_temperature=%s)", current_temp, threshold_temp)
            return jsonify({"status": "error", "message": "Missing current_temperature or threshold_temperature"}), 400

        current_temp = float(current_temp)
        threshold_temp = float(threshold_temp)
        logger.info("temperature/alert: current=%.2f, threshold=%.2f", current_temp, threshold_temp)

        # Check if current temperature exceeds threshold
        if current_temp > threshold_temp:
            email_response = send_temperature_alert_email(current_temp, threshold_temp)
            if email_response.get("status") != "sent":
                logger.warning("temperature/alert: email send failed: %s", email_response)
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

    except (ValueError, TypeError) as e:
        logger.warning("temperature/alert: bad input - %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.exception("temperature/alert: 500 error - %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================================
# EMAIL NOTIFICATION SYSTEM - SendGrid Integration
# (Defined before if __name__ so they exist when running with python server.py)
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
        logger.error("send_temperature_alert_email: SENDGRID_API_KEY not configured")
        return {
            "status": "failed",
            "error": "SENDGRID_API_KEY environment variable not configured"
        }

    logger.info("send_temperature_alert_email: sending alert current=%.2f threshold=%.2f", current_temperature, threshold_temperature)
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
            logger.info("send_temperature_alert_email: SendGrid 202 accepted")
            return {
                "status": "sent",
                "message": "Email sent successfully",
                "response_code": response.status_code
            }
        else:
            logger.error(
                "send_temperature_alert_email: SendGrid failed status=%s body=%s",
                response.status_code,
                response.text[:500] if response.text else "(empty)"
            )
            return {
                "status": "failed",
                "error": f"SendGrid API error: {response.status_code}",
                "details": response.text
            }
    except Exception as e:
        logger.exception("send_temperature_alert_email: exception - %s", e)
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
            logger.error("send_custom_notification: SendGrid failed status=%s body=%s", response.status_code, response.text[:500] if response.text else "(empty)")
            return {
                "status": "failed",
                "error": f"SendGrid API error: {response.status_code}"
            }
    except Exception as e:
        logger.exception("send_custom_notification: exception - %s", e)
        return {
            "status": "failed",
            "error": str(e)
        }


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    logger.info("Starting Temperature Server on port %s", port)
    app.run(host='0.0.0.0', port=port)
