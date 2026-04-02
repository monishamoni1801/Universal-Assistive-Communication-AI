"""
Speech-to-Text Routes for Deaf Screen
Handles real-time captioning and speech recognition
"""

from flask import Blueprint, request, jsonify, current_app
from flask_socketio import emit
import logging
from datetime import datetime
import threading
import time

logger = logging.getLogger(__name__)

# Create blueprint
stt_bp = Blueprint('stt', __name__, url_prefix='/api/stt')

# Global variables for managing STT sessions
active_sessions = {}
session_counter = 0

@stt_bp.route('/start', methods=['POST'])
def start_listening():
    """Start continuous speech recognition for a session"""
    global session_counter
    
    try:
        # Get session ID from request or create new one
        data = request.json or {}
        session_id = data.get('session_id', f"session_{session_counter}")
        
        # Get STT model from app config
        stt_model = current_app.config.get('stt_model')
        if not stt_model:
            return jsonify({'success': False, 'error': 'STT model not available'}), 500
        
        # Start listening
        stt_model.start_listening()
        
        # Store session
        session_counter += 1
        active_sessions[session_id] = {
            'start_time': datetime.now().isoformat(),
            'last_text': '',
            'text_count': 0
        }
        
        logger.info(f"🎤 STT started for session: {session_id}")
        
        return jsonify({
            'success': True,
            'message': 'Listening started',
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error starting STT: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@stt_bp.route('/stop', methods=['POST'])
def stop_listening():
    """Stop continuous speech recognition"""
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        
        stt_model = current_app.config.get('stt_model')
        if not stt_model:
            return jsonify({'success': False, 'error': 'STT model not available'}), 500
        
        # Stop listening
        stt_model.stop_listening()
        
        # Remove session if exists
        if session_id and session_id in active_sessions:
            active_sessions[session_id]['end_time'] = datetime.now().isoformat()
            del active_sessions[session_id]
        
        logger.info(f"🛑 STT stopped for session: {session_id}")
        
        return jsonify({
            'success': True,
            'message': 'Listening stopped',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error stopping STT: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@stt_bp.route('/latest', methods=['GET'])
def get_latest_text():
    """Get the latest recognized text"""
    try:
        stt_model = current_app.config.get('stt_model')
        if not stt_model:
            return jsonify({'success': False, 'error': 'STT model not available'}), 500
        
        latest = stt_model.get_latest_text()
        
        if latest:
            return jsonify({
                'success': True,
                'text': latest['text'],
                'confidence': latest['confidence'],
                'is_emergency': latest['is_emergency'],
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': True,
                'text': None,
                'confidence': 0,
                'is_emergency': False,
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Error getting latest text: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@stt_bp.route('/listen_once', methods=['POST'])
def listen_once():
    """Listen once and return text"""
    try:
        data = request.json or {}
        timeout = data.get('timeout', 5)
        
        stt_model = current_app.config.get('stt_model')
        if not stt_model:
            return jsonify({'success': False, 'error': 'STT model not available'}), 500
        
        text, confidence = stt_model.listen_once(timeout=timeout)
        
        return jsonify({
            'success': True,
            'text': text,
            'confidence': confidence,
            'is_emergency': stt_model._check_emergency(text) if text else False,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error listening once: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@stt_bp.route('/history', methods=['GET'])
def get_history():
    """Get recognition history"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        stt_model = current_app.config.get('stt_model')
        if not stt_model:
            return jsonify({'success': False, 'error': 'STT model not available'}), 500
        
        history = stt_model.get_history(limit)
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@stt_bp.route('/status', methods=['GET'])
def get_status():
    """Get STT system status"""
    try:
        stt_model = current_app.config.get('stt_model')
        if not stt_model:
            return jsonify({'success': False, 'error': 'STT model not available'}), 500
        
        return jsonify({
            'success': True,
            'is_listening': stt_model.is_listening,
            'is_available': stt_model.is_available(),
            'active_sessions': len(active_sessions),
            'sessions': active_sessions,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# WebSocket event handlers for real-time captions
def register_socketio_handlers(socketio):
    """Register SocketIO handlers for STT"""
    
    @socketio.on('start_captions')
    def handle_start_captions(data):
        """Start sending real-time captions"""
        session_id = data.get('session_id', 'default')
        
        def caption_generator():
            stt_model = current_app.config.get('stt_model')
            last_text = ""
            
            while True:
                try:
                    latest = stt_model.get_latest_text()
                    if latest and latest['text'] != last_text:
                        socketio.emit('new_caption', {
                            'session_id': session_id,
                            'text': latest['text'],
                            'confidence': latest['confidence'],
                            'is_emergency': latest['is_emergency'],
                            'timestamp': datetime.now().isoformat()
                        }, room=request.sid)
                        last_text = latest['text']
                    
                    socketio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Caption generator error: {e}")
                    socketio.sleep(1)
        
        socketio.start_background_task(caption_generator)
        emit('captions_started', {
            'message': 'Real-time captions enabled',
            'session_id': session_id
        })
    
    @socketio.on('stop_captions')
    def handle_stop_captions():
        """Stop sending real-time captions"""
        emit('captions_stopped', {'message': 'Real-time captions disabled'})