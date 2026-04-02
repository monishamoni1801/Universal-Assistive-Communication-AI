"""
Emergency Routes for All Users
Handles emergency alerts and notifications
"""

from flask import Blueprint, request, jsonify, current_app
import logging
from datetime import datetime
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

logger = logging.getLogger(__name__)

# Create blueprint
emergency_bp = Blueprint('emergency', __name__, url_prefix='/api/emergency')

# Store emergency alerts
emergency_alerts = []
alert_counter = 0

# Emergency contacts (in production, load from database)
DEFAULT_CONTACTS = [
    {'name': 'Emergency Services', 'phone': '911', 'email': None},
    {'name': 'Family Member', 'phone': '+1234567890', 'email': 'family@example.com'}
]

@emergency_bp.route('/send', methods=['POST'])
def send_emergency():
    """Send emergency alert"""
    global alert_counter
    
    try:
        data = request.json
        user_id = data.get('userId', 'unknown')
        location = data.get('location', {})
        emergency_type = data.get('type', 'general')
        message = data.get('message', 'Emergency assistance needed!')
        contacts = data.get('contacts', DEFAULT_CONTACTS)
        
        # Generate alert ID
        alert_counter += 1
        alert_id = f"EMG_{datetime.now().strftime('%Y%m%d')}_{alert_counter:04d}"
        
        # Create alert record
        alert = {
            'id': alert_id,
            'user_id': user_id,
            'type': emergency_type,
            'location': location,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'status': 'active',
            'notified_contacts': []
        }
        
        # Log emergency
        logger.warning(f"🚨 EMERGENCY {alert_id}: {emergency_type} from {user_id} at {location}")
        
        # In production, this would:
        # 1. Send SMS/email to emergency contacts
        # 2. Trigger buzzer/siren
        # 3. Notify nearby users
        # 4. Call emergency services
        
        # Simulate notifications
        for contact in contacts:
            if contact.get('email'):
                # Send email
                email_sent = send_email_alert(contact['email'], alert)
                if email_sent:
                    alert['notified_contacts'].append({
                        'name': contact['name'],
                        'method': 'email',
                        'timestamp': datetime.now().isoformat()
                    })
            
            if contact.get('phone'):
                # In production, send SMS via Twilio etc.
                alert['notified_contacts'].append({
                    'name': contact['name'],
                    'method': 'sms',
                    'timestamp': datetime.now().isoformat()
                })
        
        # Store alert
        emergency_alerts.append(alert)
        
        return jsonify({
            'success': True,
            'message': 'Emergency alert sent successfully',
            'alert_id': alert_id,
            'notified': len(alert['notified_contacts']),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error sending emergency: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@emergency_bp.route('/status/<alert_id>', methods=['GET'])
def get_alert_status(alert_id):
    """Get status of an emergency alert"""
    try:
        for alert in emergency_alerts:
            if alert['id'] == alert_id:
                return jsonify({
                    'success': True,
                    'alert': alert,
                    'timestamp': datetime.now().isoformat()
                })
        
        return jsonify({'success': False, 'error': 'Alert not found'}), 404
        
    except Exception as e:
        logger.error(f"Error getting alert status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@emergency_bp.route('/history', methods=['GET'])
def get_emergency_history():
    """Get emergency alert history"""
    try:
        user_id = request.args.get('user_id')
        limit = request.args.get('limit', 50, type=int)
        
        if user_id:
            # Filter by user
            alerts = [a for a in emergency_alerts if a['user_id'] == user_id][-limit:]
        else:
            # Get all alerts
            alerts = emergency_alerts[-limit:]
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'count': len(alerts),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@emergency_bp.route('/resolve/<alert_id>', methods=['POST'])
def resolve_alert(alert_id):
    """Mark an alert as resolved"""
    try:
        for alert in emergency_alerts:
            if alert['id'] == alert_id:
                alert['status'] = 'resolved'
                alert['resolved_time'] = datetime.now().isoformat()
                
                return jsonify({
                    'success': True,
                    'message': 'Alert resolved',
                    'alert_id': alert_id,
                    'timestamp': datetime.now().isoformat()
                })
        
        return jsonify({'success': False, 'error': 'Alert not found'}), 404
        
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@emergency_bp.route('/contacts', methods=['GET', 'POST'])
def manage_contacts():
    """Get or update emergency contacts"""
    if request.method == 'GET':
        user_id = request.args.get('user_id', 'default')
        
        # In production, fetch from database
        return jsonify({
            'success': True,
            'contacts': DEFAULT_CONTACTS,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        })
    
    elif request.method == 'POST':
        data = request.json
        user_id = data.get('user_id', 'default')
        contacts = data.get('contacts', [])
        
        # In production, save to database
        logger.info(f"Updated contacts for {user_id}: {len(contacts)} contacts")
        
        return jsonify({
            'success': True,
            'message': 'Contacts updated',
            'user_id': user_id,
            'contacts': contacts,
            'timestamp': datetime.now().isoformat()
        })

@emergency_bp.route('/test', methods=['POST'])
def test_emergency():
    """Test emergency system (no actual alerts sent)"""
    try:
        data = request.json or {}
        user_id = data.get('userId', 'test_user')
        
        logger.info(f"🔔 TEST EMERGENCY from {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Test emergency successful',
            'test_id': f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in test emergency: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Helper function to send email alerts
def send_email_alert(to_email, alert):
    """Send email alert (configure with your email settings)"""
    try:
        # Email configuration (set these in environment variables)
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        sender_email = os.environ.get('SENDER_EMAIL', 'your-email@gmail.com')
        sender_password = os.environ.get('SENDER_PASSWORD', 'your-password')
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = f"🚨 EMERGENCY ALERT: {alert['type'].upper()}"
        
        body = f"""
        EMERGENCY ALERT
        
        Alert ID: {alert['id']}
        User ID: {alert['user_id']}
        Type: {alert['type']}
        Time: {alert['timestamp']}
        Location: {alert['location']}
        Message: {alert['message']}
        
        Immediate assistance may be required.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email alert sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False