"""
Sign Language Routes for Mute/Deaf Screens
Handles text-to-sign and sign-to-text conversion
"""

from flask import Blueprint, request, jsonify, current_app, send_file
import logging
from datetime import datetime
import os
import cv2
import numpy as np
import base64

logger = logging.getLogger(__name__)

# Create blueprint
sign_bp = Blueprint('sign', __name__, url_prefix='/api/sign')

# Sign-to-Text detection sessions
detection_sessions = {}

@sign_bp.route('/convert', methods=['POST'])
def convert_to_sign():
    """Convert text to sign language representation"""
    try:
        data = request.json
        text = data.get('text', '').strip().lower()
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400
        
        sign_model = current_app.config.get('sign_model')
        if not sign_model:
            return jsonify({'success': False, 'error': 'Sign model not available'}), 500
        
        # Convert text to sign
        result = sign_model.convert(text)
        
        return jsonify({
            'success': True,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error converting to sign: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sign_bp.route('/dictionary', methods=['GET'])
def get_dictionary():
    """Get dictionary of available signs"""
    try:
        sign_model = current_app.config.get('sign_model')
        if not sign_model:
            return jsonify({'success': False, 'error': 'Sign model not available'}), 500
        
        dictionary = sign_model.get_dictionary()
        
        # Group by type
        gifs = [item for item in dictionary if item['type'] == 'gif']
        letters = [item for item in dictionary if item['type'] == 'letter']
        
        return jsonify({
            'success': True,
            'dictionary': dictionary,
            'counts': {
                'total': len(dictionary),
                'gifs': len(gifs),
                'letters': len(letters)
            },
            'gifs': gifs,
            'letters': letters,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting dictionary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sign_bp.route('/image/<path:sign_name>', methods=['GET'])
def get_sign_image(sign_name):
    """Get sign image/GIF"""
    try:
        sign_model = current_app.config.get('sign_model')
        if not sign_model:
            return jsonify({'success': False, 'error': 'Sign model not available'}), 500
        
        image_path = sign_model.get_sign_image(sign_name)
        
        if image_path and os.path.exists(image_path):
            # Determine mimetype
            if image_path.endswith('.gif'):
                mimetype = 'image/gif'
            else:
                mimetype = 'image/jpeg'
            
            return send_file(image_path, mimetype=mimetype)
        else:
            return jsonify({'success': False, 'error': 'Image not found'}), 404
            
    except Exception as e:
        logger.error(f"Error getting sign image: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sign_bp.route('/image_base64/<path:sign_name>', methods=['GET'])
def get_sign_image_base64(sign_name):
    """Get sign image as base64"""
    try:
        sign_model = current_app.config.get('sign_model')
        if not sign_model:
            return jsonify({'success': False, 'error': 'Sign model not available'}), 500
        
        image_path = sign_model.get_sign_image(sign_name)
        
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                image_data = f.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                return jsonify({
                    'success': True,
                    'image': image_base64,
                    'format': 'gif' if image_path.endswith('.gif') else 'jpg',
                    'sign_name': sign_name
                })
        else:
            return jsonify({'success': False, 'error': 'Image not found'}), 404
            
    except Exception as e:
        logger.error(f"Error getting sign image base64: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== SIGN-TO-TEXT ROUTES ====================

@sign_bp.route('/detect/start', methods=['POST'])
def start_sign_detection():
    """Start sign language detection session"""
    try:
        data = request.json or {}
        session_id = data.get('session_id', f"sign_session_{len(detection_sessions)}")
        
        s2t_model = current_app.config.get('s2t_model')
        if not s2t_model:
            return jsonify({'success': False, 'error': 'Sign-to-Text model not available'}), 500
        
        # Initialize session
        detection_sessions[session_id] = {
            'start_time': datetime.now().isoformat(),
            'detections': [],
            'current_sentence': [],
            'current_word': ''
        }
        
        return jsonify({
            'success': True,
            'message': 'Sign detection started',
            'session_id': session_id,
            'available_classes': {
                'words': s2t_model.word_classes[:20],  # First 20 words
                'letters': s2t_model.letter_classes
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error starting sign detection: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sign_bp.route('/detect/frame', methods=['POST'])
def detect_sign_frame():
    """Detect sign from a single frame"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if 'image' not in data:
            return jsonify({'success': False, 'error': 'No image data'}), 400
        
        # Get image from base64
        image_data = data['image'].split(',')[1] if ',' in data['image'] else data['image']
        image_bytes = base64.b64decode(image_data)
        
        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        s2t_model = current_app.config.get('s2t_model')
        if not s2t_model:
            return jsonify({'success': False, 'error': 'Sign-to-Text model not available'}), 500
        
        # Process frame
        def dummy_callback(msg):
            pass
            
        processed = s2t_model.detect_signs(frame, dummy_callback)
        
        # Get current detection
        result = {
            'mode': s2t_model.detection_mode,
            'current_word': s2t_model.current_word,
            'sentence': ' '.join(s2t_model.current_sentence)
        }
        
        # Update session if exists
        if session_id and session_id in detection_sessions:
            detection_sessions[session_id]['detections'].append({
                'timestamp': datetime.now().isoformat(),
                'result': result
            })
            detection_sessions[session_id]['current_sentence'] = s2t_model.current_sentence
            detection_sessions[session_id]['current_word'] = s2t_model.current_word
        
        return jsonify({
            'success': True,
            'result': result,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error detecting sign frame: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sign_bp.route('/detect/stop', methods=['POST'])
def stop_sign_detection():
    """Stop sign detection session"""
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        
        if session_id and session_id in detection_sessions:
            session_data = detection_sessions[session_id]
            session_data['end_time'] = datetime.now().isoformat()
            
            result = {
                'success': True,
                'session': session_data,
                'final_sentence': ' '.join(session_data['current_sentence'])
            }
            
            del detection_sessions[session_id]
            return jsonify(result)
        else:
            return jsonify({
                'success': True,
                'message': 'No active session'
            })
        
    except Exception as e:
        logger.error(f"Error stopping sign detection: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sign_bp.route('/detect/clear', methods=['POST'])
def clear_sign_detection():
    """Clear current sign detection"""
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        
        s2t_model = current_app.config.get('s2t_model')
        if not s2t_model:
            return jsonify({'success': False, 'error': 'Sign-to-Text model not available'}), 500
        
        s2t_model.clear_sentence()
        
        # Update session if exists
        if session_id and session_id in detection_sessions:
            detection_sessions[session_id]['current_sentence'] = []
            detection_sessions[session_id]['current_word'] = ''
        
        return jsonify({
            'success': True,
            'message': 'Detection cleared',
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error clearing detection: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sign_bp.route('/detect/speak', methods=['POST'])
def speak_sign_sentence():
    """Speak the detected sign sentence"""
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        
        s2t_model = current_app.config.get('s2t_model')
        if not s2t_model:
            return jsonify({'success': False, 'error': 'Sign-to-Text model not available'}), 500
        
        if s2t_model.current_sentence:
            s2t_model.speak_sentence()
            
            return jsonify({
                'success': True,
                'message': 'Speaking sentence',
                'sentence': ' '.join(s2t_model.current_sentence),
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No sentence to speak'
            }), 400
            
    except Exception as e:
        logger.error(f"Error speaking sign sentence: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sign_bp.route('/detect/sessions', methods=['GET'])
def get_detection_sessions():
    """Get all active detection sessions"""
    return jsonify({
        'success': True,
        'active_sessions': len(detection_sessions),
        'sessions': detection_sessions,
        'timestamp': datetime.now().isoformat()
    })