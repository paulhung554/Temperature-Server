# Temperature Monitoring Server with SendGrid Email Alerts
# This file is self-contained for Render deployment

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests
import json
import logging
from datetime import datetime
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('server.log')  # File output
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
lastesttempeturedata = None

# Store data for both PLCs
plc_data = {
    "PLC1": None,
    "PLC2": None
}

# Configuration
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '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')
ALERT_EMAIL = "paulhung554@gmail.com"

# Threshold storage (in-memory for now, can be upgraded to database)
threshold_config = {
    "plc1_setpoint": 30.0,
    "plc1_threshold": 30.0,
    "plc2_setpoint": 32.0,
    "plc2_threshold": 32.0
}

# Manual temperature storage
manual_temperatures = {
    "PLC1": None,
    "PLC2": None
}

# PLC configuration
PLC_CONFIG = {
    "PLC1": {"ip": "192.168.3.100", "port": 502, "slave_unit": 1},
    "PLC2": {"ip": "192.168.3.101", "port": 502, "slave_unit": 1}
}

def read_plc_temperature(plc_id):
    """
    Read current temperature from PLC
    """
    if plc_id not in PLC_CONFIG:
        return None
    
    config = PLC_CONFIG[plc_id]
    try:
        client = ModbusTcpClient(config["ip"], port=config["port"])
        if client.connect():
            result = client.read_holding_registers(8959, count=1, device_id=config["slave_unit"])
            client.close()
            if not result.isError():
                temperature = result.registers[0]
                timestamp = datetime.now().isoformat()
                data = {
                    "temperature": temperature,
                    "plc": plc_id,
                    "register": 8959,
                    "timestamp": timestamp
                }
                # Update plc_data
                plc_data[plc_id] = data
                logger.info(f"Read temperature from {plc_id}: {temperature}°C")
                return data
            else:
                logger.error(f"Modbus error reading from {plc_id}")
                return None
        else:
            logger.error(f"Failed to connect to {plc_id}")
            return None
    except Exception as e:
        logger.error(f"Error reading from {plc_id}: {str(e)}")
        return None

@app.route('/', methods=['GET'])
def root():
    logger.info("Root endpoint accessed")
    return jsonify({"message": "Temperature Server", "endpoints": ["/temperature", "/threshold"]})

@app.route('/temperature', methods=['GET'])
def get_temperature():
    # Return temperature data including which PLC it came from
    if lastesttempeturedata:
        temp_value = lastesttempeturedata.get('temperature')
        plc_source = lastesttempeturedata.get('plc', 'Unknown')
        timestamp = lastesttempeturedata.get('timestamp', 'N/A')
        register = lastesttempeturedata.get('register', 'N/A')
        
        logger.debug(f"GET /temperature - Returning current temperature: {temp_value}°C from {plc_source}")
        return jsonify({
            "temperature": temp_value,
            "plc": plc_source,
            "register": register,
            "timestamp": timestamp
        })
    logger.warning("GET /temperature - No temperature data available yet")
    return jsonify({
        "temperature": "Not Available",
        "plc": "Unknown",
        "error": "No data received from any PLC yet"
    })

@app.route('/plc-data', methods=['GET'])
def get_plc_data():
    """
    Get current data for both PLCs including temperatures, setpoints and thresholds
    """
    plc1_data = plc_data.get("PLC1")
    plc2_data = plc_data.get("PLC2")
    
    # Use manual temperature if available, otherwise use PLC data
    plc1_temp = manual_temperatures.get("PLC1") or (plc1_data.get('temperature') if plc1_data else "Not Available")
    plc2_temp = manual_temperatures.get("PLC2") or (plc2_data.get('temperature') if plc2_data else "Not Available")
    
    response = {
        "PLC1": {
            "temperature": plc1_temp,
            "setpoint": threshold_config.get('plc1_setpoint', 30.0),
            "threshold": threshold_config.get('plc1_threshold', 30.0),
            "timestamp": plc1_data.get('timestamp') if plc1_data else "N/A",
            "register": plc1_data.get('register') if plc1_data else "N/A"
        },
        "PLC2": {
            "temperature": plc2_temp,
            "setpoint": threshold_config.get('plc2_setpoint', 32.0),
            "threshold": threshold_config.get('plc2_threshold', 32.0),
            "timestamp": plc2_data.get('timestamp') if plc2_data else "N/A",
            "register": plc2_data.get('register') if plc2_data else "N/A"
        }
    }
    
    logger.info("GET /plc-data - Returning data for both PLCs")
    return jsonify(response), 200
        
    
@app.route('/read-plc/<plc_id>', methods=['GET'])
def read_plc(plc_id):
    """
    Read current temperature from specified PLC
    """
    plc_id = plc_id.upper()
    if plc_id not in ["PLC1", "PLC2"]:
        return jsonify({"status": "error", "message": "Invalid PLC ID"}), 400
    
    data = read_plc_temperature(plc_id)
    if data:
        return jsonify({"status": "success", "data": data}), 200
    else:
        return jsonify({"status": "error", "message": f"Failed to read from {plc_id}"}), 500

@app.route('/temperature', methods=['POST'])
def receive_sensordata():
    # Mocked temperature data
    global lastesttempeturedata 
    data = request.get_json()
    lastesttempeturedata = data
    
    # Store data for specific PLC
    plc = data.get('plc', 'Unknown')
    if plc in plc_data:
        plc_data[plc] = data
    
    logger.info("=" * 70)
    logger.info("📊 RECEIVED TEMPERATURE DATA FROM LOCAL MODBUS")
    logger.info("=" * 70)
    logger.info(f"  PLC: {data.get('plc', 'Unknown')}")
    logger.info(f"  Temperature Value: {data.get('temperature')}°C")
    logger.info(f"  Register: {data.get('register', 'N/A')}")
    logger.info(f"  Timestamp: {data.get('timestamp', 'N/A')}")
    logger.info(f"  Raw Payload: {json.dumps(data, indent=2)}")
    logger.info("=" * 70)
    
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
        
        logger.debug(f"Temperature Alert Check - Current: {current_temp}°C, Threshold: {threshold_temp}°C")
        
        if current_temp is None or threshold_temp is None:
            logger.warning(f"Temperature Alert - Missing parameters. Current: {current_temp}, Threshold: {threshold_temp}")
            return jsonify({"status": "error", "message": "Missing current_temperature or threshold_temperature"}), 400
        
        current_temp = float(current_temp)
        threshold_temp = float(threshold_temp)
        
        # Check if current temperature exceeds threshold
        if current_temp > threshold_temp:
            logger.warning(f"🚨 TEMPERATURE ALERT TRIGGERED - {current_temp}°C > {threshold_temp}°C (Excess: {current_temp - threshold_temp}°C)")
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
            logger.info(f"✅ Temperature within threshold - {current_temp}°C <= {threshold_temp}°C")
            return jsonify({
                "status": "ok",
                "message": f"Temperature {current_temp}°C is within threshold {threshold_temp}°C",
                "current_temperature": current_temp,
                "threshold_temperature": threshold_temp
            }), 200
            
    except Exception as e:
        logger.error(f"❌ Error in temperature alert check: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/threshold', methods=['GET'])
def get_threshold():
    """
    Get current threshold configuration for all PLCs
    """
    logger.info("GET /threshold - Retrieving all thresholds")
    logger.debug(f"Current threshold config: {json.dumps(threshold_config)}")
    return jsonify(threshold_config), 200

@app.route('/threshold/<plc_id>', methods=['GET'])
def get_plc_threshold(plc_id):
    """
    Get threshold for a specific PLC
    Args:
        plc_id: 'plc1' or 'plc2'
    """
    key = f"{plc_id}_threshold"
    if key in threshold_config:
        value = threshold_config[key]
        logger.info(f"GET /threshold/{plc_id} - Retrieved threshold: {value}°C")
        return jsonify({"plc": plc_id, "threshold": value}), 200
    logger.warning(f"GET /threshold/{plc_id} - Invalid PLC ID: {plc_id}")
    return jsonify({"error": f"Invalid PLC ID: {plc_id}"}), 404

@app.route('/threshold', methods=['POST'])
def update_threshold():
    """
    Update threshold configuration
    Expects JSON: {"plc1_threshold": <value>, "plc2_threshold": <value>}
    """
    try:
        data = request.get_json()
        
        logger.info("=" * 70)
        logger.info("🎯 RECEIVED NEW SETPOINT(S) FROM FRONTEND")
        logger.info("=" * 70)
        
        updated_plcs = []
        
        if 'plc1_threshold' in data:
            old_value = threshold_config.get('plc1_threshold', 'N/A')
            new_value = float(data['plc1_threshold'])
            threshold_config['plc1_threshold'] = new_value
            logger.info(f"  PLC1 Threshold Updated: {old_value}°C → {new_value}°C")
            updated_plcs.append(f"PLC1: {old_value}°C → {new_value}°C")
            
        if 'plc2_threshold' in data:
            old_value = threshold_config.get('plc2_threshold', 'N/A')
            new_value = float(data['plc2_threshold'])
            threshold_config['plc2_threshold'] = new_value
            logger.info(f"  PLC2 Threshold Updated: {old_value}°C → {new_value}°C")
            updated_plcs.append(f"PLC2: {old_value}°C → {new_value}°C")
        
        logger.info(f"  Total Updates: {len(updated_plcs)}")
        logger.info(f"  New Configuration: {json.dumps(threshold_config)}")
        logger.info("  ✅ Will be sent to local modbus on next poll cycle")
        logger.info("=" * 70)
        
        return jsonify({
            "status": "success",
            "message": "Threshold updated",
            "config": threshold_config
        }), 200
    except Exception as e:
        logger.error(f"❌ Error updating threshold: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/threshold/<plc_id>', methods=['POST'])
def update_plc_threshold(plc_id):
    """
    Update threshold for a specific PLC
    Args:
        plc_id: 'plc1' or 'plc2'
    Expects JSON: {"threshold": <value>}
    """
    try:
        data = request.get_json()
        threshold = float(data.get('threshold'))
        key = f"{plc_id}_threshold"
        
        if key not in threshold_config:
            logger.warning(f"POST /threshold/{plc_id} - Invalid PLC ID: {plc_id}")
            return jsonify({"error": f"Invalid PLC ID: {plc_id}"}), 404
        
        old_value = threshold_config[key]
        threshold_config[key] = threshold
        
        logger.info("=" * 70)
        logger.info(f"🎯 RECEIVED NEW SETPOINT FROM FRONTEND FOR {plc_id.upper()}")
        logger.info("=" * 70)
        logger.info(f"  Previous Threshold: {old_value}°C")
        logger.info(f"  New Threshold: {threshold}°C")
        logger.info(f"  Change: {threshold - old_value:+.1f}°C")
        logger.info(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("  ✅ Will be sent to local modbus on next poll cycle")
        logger.info("=" * 70)
        
        return jsonify({
            "status": "success",
            "message": f"{plc_id} threshold updated",
            "plc": plc_id,
            "threshold": threshold,
            "previous_threshold": old_value
        }), 200
    except Exception as e:
        logger.error(f"❌ Error updating {plc_id} threshold: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 400
    
    
@app.route('/setpoint/<plc_id>', methods=['POST'])
def update_plc_setpoint(plc_id):
    """
    Update setpoint for a specific PLC
    Args:
        plc_id: 'plc1' or 'plc2'
    Expects JSON: {"setpoint": <value>}
    """
    try:
        data = request.get_json()
        setpoint = float(data.get('setpoint'))
        key = f"{plc_id}_setpoint"
        
        if key not in threshold_config:
            logger.warning(f"POST /setpoint/{plc_id} - Invalid PLC ID: {plc_id}")
            return jsonify({"error": f"Invalid PLC ID: {plc_id}"}), 404
        
        old_value = threshold_config[key]
        threshold_config[key] = setpoint
        
        logger.info("=" * 70)
        logger.info(f"🎯 RECEIVED NEW SETPOINT FROM FRONTEND FOR {plc_id.upper()}")
        logger.info("=" * 70)
        logger.info(f"  Previous Setpoint: {old_value}°C")
        logger.info(f"  New Setpoint: {setpoint}°C")
        logger.info(f"  Change: {setpoint - old_value:+.1f}°C")
        logger.info(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("  ✅ Setpoint updated")
        logger.info("=" * 70)
        
        return jsonify({
            "status": "success",
            "message": f"{plc_id} setpoint updated",
            "plc": plc_id,
            "setpoint": setpoint,
            "previous_setpoint": old_value
        }), 200
    except Exception as e:
        logger.error(f"❌ Error updating {plc_id} setpoint: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/temperature/manual/<plc_id>', methods=['POST'])
def set_manual_temperature(plc_id):
    """
    Set manual temperature for a specific PLC
    Args:
        plc_id: 'PLC1' or 'PLC2'
    Expects JSON: {"temperature": <value>}
    """
    try:
        data = request.get_json()
        temperature = float(data.get('temperature'))
        plc_key = plc_id.upper()
        
        if plc_key not in manual_temperatures:
            logger.warning(f"POST /temperature/manual/{plc_id} - Invalid PLC ID: {plc_id}")
            return jsonify({"error": f"Invalid PLC ID: {plc_id}"}), 404
        
        old_value = manual_temperatures[plc_key]
        manual_temperatures[plc_key] = temperature
        
        logger.info("=" * 70)
        logger.info(f"🎯 RECEIVED MANUAL TEMPERATURE FOR {plc_key}")
        logger.info("=" * 70)
        logger.info(f"  Previous Temperature: {old_value}°C")
        logger.info(f"  New Manual Temperature: {temperature}°C")
        logger.info(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("  ✅ Manual temperature set")
        logger.info("=" * 70)
        
        return jsonify({
            "status": "success",
            "message": f"{plc_key} manual temperature set",
            "plc": plc_key,
            "temperature": temperature,
            "previous_temperature": old_value
        }), 200
    except Exception as e:
        logger.error(f"❌ Error setting manual temperature for {plc_id}: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 400
    
    
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
