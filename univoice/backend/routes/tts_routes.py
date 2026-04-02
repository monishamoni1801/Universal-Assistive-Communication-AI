"""
Text-to-Speech Routes for Mute Screen
Handles voice synthesis and audio generation
"""

from flask import Blueprint, request, jsonify, current_app, send_file
import logging
from datetime import datetime
import os
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

# Create blueprint
tts_bp = Blueprint('tts', __name__, url_prefix='/api/tts')

@tts_bp.route('/voices', methods=['GET'])
def get_voices():
    """Get available TTS voices"""
    try:
        tts_model = current_app.config.get('tts_model')
        if not tts_model:
            return jsonify({'success': False, 'error': 'TTS model not available'}), 500
        
        voices = tts_model.get_available_voices()
        
        return jsonify({
            'success': True,
            'voices': voices,
            'count': len(voices),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@tts_bp.route('/speak', methods=['POST'])
def speak_text():
    """Convert text to speech and return audio file"""
    try:
        data = request.json
        text = data.get('text', '')
        voice_id = data.get('voice_id', 0)
        rate = data.get('rate', 170)
        volume = data.get('volume', 0.9)
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400
        
        tts_model = current_app.config.get('tts_model')
        if not tts_model:
            return jsonify({'success': False, 'error': 'TTS model not available'}), 500
        
        # Generate unique filename
        filename = f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Save to file
        result = tts_model.speak(text, voice_id, rate, volume, filepath)
        
        if result and os.path.exists(result):
            return send_file(
                result,
                as_attachment=True,
                download_name=filename,
                mimetype='audio/mpeg'
            )
        else:
            return jsonify({'success': False, 'error': 'TTS failed'}), 500
            
    except Exception as e:
        logger.error(f"Error in TTS speak: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@tts_bp.route('/speak_base64', methods=['POST'])
def speak_base64():
    """Convert text to speech and return base64 audio"""
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400
        
        tts_model = current_app.config.get('tts_model')
        if not tts_model:
            return jsonify({'success': False, 'error': 'TTS model not available'}), 500
        
        # Use gTTS for base64 conversion
        from gtts import gTTS
        import base64
        from io import BytesIO
        
        tts = gTTS(text=text, lang='en', slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        audio_base64 = base64.b64encode(fp.read()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'audio': audio_base64,
            'format': 'mp3',
            'text': text[:50] + '...' if len(text) > 50 else text,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in TTS base64: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@tts_bp.route('/save', methods=['POST'])
def save_audio():
    """Save TTS audio to file and return path"""
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400
        
        filename = f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Use gTTS for better file saving
        from gtts import gTTS
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'size': os.path.getsize(filepath) if os.path.exists(filepath) else 0,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error saving audio: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@tts_bp.route('/preview', methods=['POST'])
def preview_voice():
    """Preview a voice with sample text"""
    try:
        data = request.json
        voice_id = data.get('voice_id', 0)
        sample_text = data.get('sample_text', 'Hello, this is a voice preview.')
        
        tts_model = current_app.config.get('tts_model')
        if not tts_model:
            return jsonify({'success': False, 'error': 'TTS model not available'}), 500
        
        # Generate preview audio
        filename = f"preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        result = tts_model.speak(sample_text, voice_id, 170, 0.9, filepath)
        
        if result and os.path.exists(result):
            return send_file(
                result,
                as_attachment=True,
                download_name=filename,
                mimetype='audio/mpeg'
            )
        else:
            return jsonify({'success': False, 'error': 'Preview failed'}), 500
            
    except Exception as e:
        logger.error(f"Error in voice preview: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@tts_bp.route('/languages', methods=['GET'])
def get_languages():
    """Get supported languages for TTS"""
    return jsonify({
        'success': True,
        'languages': [
            {'code': 'en', 'name': 'English'},
            {'code': 'es', 'name': 'Spanish'},
            {'code': 'fr', 'name': 'French'},
            {'code': 'de', 'name': 'German'},
            {'code': 'it', 'name': 'Italian'},
            {'code': 'ja', 'name': 'Japanese'},
            {'code': 'ko', 'name': 'Korean'},
            {'code': 'zh', 'name': 'Chinese'}
        ],
        'timestamp': datetime.now().isoformat()
    })