"""
Main Flask Application for Universal Assistive Communication System
Integrates all 4 deep learning models with React Native frontend
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import logging
import os
import threading
import time
from datetime import datetime
import glob
import json  # Added for JSON handling

# Import models
from models.speech_to_text import SpeechToText
from models.text_to_speech import TextToSpeech
from models.text_to_sign import TextToSign
from models.sign_to_text import SignToTextConverter
from models.object_detection import ObjectDetector
from models.currency_detection_orb import CurrencyDetector
from models.text_reader import TextReader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['SENTENCES_FILE'] = os.path.join(os.path.dirname(__file__), 'data', 'sentences.json')

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize SocketIO for real-time communication
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=None)

# Create upload folder if not exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('models/ISL_Gifs', exist_ok=True)
os.makedirs('models/letters', exist_ok=True)
os.makedirs('data', exist_ok=True)  # Create data folder for sentences

# ==================== INITIALIZE MODELS ====================
logger.info("🚀 Initializing models...")

# Model 1: Speech-to-Text (for Deaf users)
stt_model = SpeechToText()
if not stt_model.is_available():
    logger.warning("⚠️ Speech-to-Text running in simulation mode")

# Model 2: Text-to-Sign (for Mute/Deaf users)
sign_model = TextToSign(base_dir=os.path.dirname(os.path.abspath(__file__)))
if not sign_model.is_available():
    logger.warning("⚠️ Text-to-Sign running with limited functionality")

# Model 3: Text-to-Speech (for Mute/Blind users)
tts_model = TextToSpeech()
if not tts_model.is_available():
    logger.warning("⚠️ Text-to-Speech running with gTTS fallback")

# Model 4: Sign-to-Text (for Mute users)
s2t_model = SignToTextConverter()
logger.info("✅ Sign-to-Text model initialized")

# Model 5: Object Detector (for Blind users)
object_detector = ObjectDetector()
logger.info("✅ Object Detector initialized")

# Model 6: Currency Detector (for Blind users)
currency_detector = CurrencyDetector()
logger.info("✅ Currency Detector initialized")

# Model 7: Text Reader (for Blind users)
text_reader = TextReader()
logger.info("✅ Text Reader initialized")

logger.info("✅ All models initialized successfully")

# ==================== CREATE DEFAULT SENTENCES FILE ====================
if not os.path.exists(app.config['SENTENCES_FILE']):
    default_sentences = {
        "Basic": [
            "Hello",
            "How are you?",
            "Good morning",
            "Good afternoon",
            "Good evening",
            "Good night",
            "Thank you",
            "You're welcome",
            "Sorry",
            "Excuse me",
            "Please wait",
            "One minute please"
        ],
        "Needs": [
            "I need help",
            "Please help me",
            "Call someone",
            "Call my family",
            "Call a doctor",
            "Please stay with me",
            "I feel uncomfortable",
            "I am not feeling well",
            "I need assistance"
        ],
        "Food": [
            "I am hungry",
            "I want food",
            "I want water",
            "Please give me water",
            "Please give me food",
            "I want tea",
            "I want coffee",
            "I want juice",
            "I finished eating",
            "I don't want food"
        ],
        "Health": [
            "I feel sick",
            "I have a headache",
            "I have stomach pain",
            "I feel dizzy",
            "I need medicine",
            "Take me to the hospital",
            "Call an ambulance"
        ],
        "Daily": [
            "Yes",
            "No",
            "Maybe",
            "I agree",
            "I don't agree",
            "That is correct",
            "That is wrong",
            "Please repeat",
            "I didn't understand"
        ],
        "Location": [
            "I want to go home",
            "Take me home",
            "I want to go outside",
            "Where is the bathroom?",
            "Where is the hospital?",
            "Where is the bus stop?",
            "I want to sit",
            "I want to stand"
        ],
        "School": [
            "I completed my work",
            "I need more time",
            "Please explain again",
            "I understand",
            "I don't understand",
            "I will do it"
        ],
        "Emergency": [
            "Emergency",
            "Call the police",
            "Call an ambulance",
            "There is danger",
            "Please help immediately"
        ],
        "Emotions": [
            "I am happy",
            "I am sad",
            "I am angry",
            "I am scared",
            "I am tired",
            "I am excited"
        ]
    }
    with open(app.config['SENTENCES_FILE'], 'w', encoding='utf-8') as f:
        json.dump(default_sentences, f, indent=2, ensure_ascii=False)
    logger.info("✅ Created default sentences.json file")

# ==================== STORE MODELS IN APP CONFIG ====================
app.config['stt_model'] = stt_model
app.config['tts_model'] = tts_model
app.config['sign_model'] = sign_model
app.config['s2t_model'] = s2t_model
app.config['object_detector'] = object_detector
app.config['currency_detector'] = currency_detector
app.config['text_reader'] = text_reader
app.config['UPLOAD_FOLDER'] = 'uploads'

# ==================== BACKGROUND THREADS ====================
def stt_listening_thread():
    """Background thread for continuous speech recognition"""
    while True:
        if stt_model.is_listening:
            time.sleep(1)
        time.sleep(0.1)

# Start STT listening thread
stt_thread = threading.Thread(target=stt_listening_thread, daemon=True)
stt_thread.start()

# ==================== API ROUTES ====================

@app.route('/api/status', methods=['GET'])
def get_status():
    """Check system status and model availability"""
    return jsonify({
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'models': {
            'speech_to_text': {
                'available': stt_model.is_available(),
                'listening': stt_model.is_listening
            },
            'text_to_speech': {
                'available': tts_model.is_available(),
                'voices': len(tts_model.voices)
            },
            'text_to_sign': {
                'available': sign_model.is_available(),
                'gifs': len(sign_model.available_gifs)
            },
            'sign_to_text': {
                'available': s2t_model.model_loaded if hasattr(s2t_model, 'model_loaded') else False,
                'letters': 26
            },
            'object_detection': {
                'available': object_detector.model_loaded if hasattr(object_detector, 'model_loaded') else False
            },
            'currency_detection': {
                'available': len(currency_detector.denominations) > 0,
                'denominations': currency_detector.denominations
            },
            'text_reader': {
                'available': text_reader.available
            }
        },
        'server': 'running'
    })

# ==================== SENTENCE GENERATOR ROUTES ====================

@app.route('/api/sentences', methods=['GET'])
def get_all_sentences():
    """Get all sentence categories and sentences"""
    try:
        if os.path.exists(app.config['SENTENCES_FILE']):
            with open(app.config['SENTENCES_FILE'], 'r', encoding='utf-8') as f:
                sentences = json.load(f)
            return jsonify({
                'success': True,
                'sentences': sentences,
                'categories': list(sentences.keys())
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Sentences file not found'
            }), 404
    except Exception as e:
        logger.error(f"Error getting sentences: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sentences/categories', methods=['GET'])
def get_categories():
    """Get all category names"""
    try:
        if os.path.exists(app.config['SENTENCES_FILE']):
            with open(app.config['SENTENCES_FILE'], 'r', encoding='utf-8') as f:
                sentences = json.load(f)
            return jsonify({
                'success': True,
                'categories': list(sentences.keys())
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Sentences file not found'
            }), 404
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sentences/<category>', methods=['GET'])
def get_category_sentences(category):
    """Get sentences for a specific category"""
    try:
        if os.path.exists(app.config['SENTENCES_FILE']):
            with open(app.config['SENTENCES_FILE'], 'r', encoding='utf-8') as f:
                sentences = json.load(f)
            
            if category in sentences:
                return jsonify({
                    'success': True,
                    'category': category,
                    'sentences': sentences[category]
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Category "{category}" not found'
                }), 404
        else:
            return jsonify({
                'success': False,
                'error': 'Sentences file not found'
            }), 404
    except Exception as e:
        logger.error(f"Error getting category sentences: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sentences/add', methods=['POST'])
def add_sentence():
    """Add a new sentence to a category"""
    try:
        data = request.json
        category = data.get('category')
        sentence = data.get('sentence')
        
        if not category or not sentence:
            return jsonify({'success': False, 'error': 'Category and sentence required'}), 400
        
        if os.path.exists(app.config['SENTENCES_FILE']):
            with open(app.config['SENTENCES_FILE'], 'r', encoding='utf-8') as f:
                sentences = json.load(f)
            
            if category not in sentences:
                sentences[category] = []
            
            if sentence not in sentences[category]:
                sentences[category].append(sentence)
            
            with open(app.config['SENTENCES_FILE'], 'w', encoding='utf-8') as f:
                json.dump(sentences, f, indent=2, ensure_ascii=False)
            
            return jsonify({
                'success': True,
                'message': f'Sentence added to {category}'
            })
        else:
            return jsonify({'success': False, 'error': 'Sentences file not found'}), 404
    except Exception as e:
        logger.error(f"Error adding sentence: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== SPEECH-TO-TEXT ROUTES ====================

@app.route('/api/stt/start', methods=['POST'])
def start_listening():
    try:
        stt_model.start_listening()
        return jsonify({'success': True, 'message': 'Listening started'})
    except Exception as e:
        logger.error(f"Error starting listening: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stt/stop', methods=['POST'])
def stop_listening():
    try:
        stt_model.stop_listening()
        return jsonify({'success': True, 'message': 'Listening stopped'})
    except Exception as e:
        logger.error(f"Error stopping listening: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stt/latest', methods=['GET'])
def get_latest_text():
    try:
        latest = stt_model.get_latest_text()
        if latest:
            return jsonify({
                'success': True,
                'text': latest['text'],
                'confidence': latest['confidence'],
                'is_emergency': latest['is_emergency']
            })
        else:
            return jsonify({'success': True, 'text': None, 'confidence': 0, 'is_emergency': False})
    except Exception as e:
        logger.error(f"Error getting latest text: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stt/listen_once', methods=['POST'])
def listen_once():
    try:
        text, confidence = stt_model.listen_once(timeout=5)
        return jsonify({
            'success': True,
            'text': text,
            'confidence': confidence,
            'is_emergency': stt_model._check_emergency(text) if text else False
        })
    except Exception as e:
        logger.error(f"Error listening once: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stt/history', methods=['GET'])
def get_history():
    try:
        limit = request.args.get('limit', 10, type=int)
        history = stt_model.get_history(limit)
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# SocketIO for real-time captions
@socketio.on('start_captions')
def handle_start_captions():
    def caption_generator():
        last_text = ""
        while True:
            latest = stt_model.get_latest_text()
            if latest and latest['text'] != last_text:
                socketio.emit('new_caption', {
                    'text': latest['text'],
                    'confidence': latest['confidence'],
                    'is_emergency': latest['is_emergency'],
                    'timestamp': datetime.now().isoformat()
                })
                last_text = latest['text']
            socketio.sleep(1)
    
    socketio.start_background_task(caption_generator)
    emit('captions_started', {'message': 'Real-time captions enabled'})

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint to check if server is running"""
    return jsonify({
        'success': True,
        'message': 'Server is working!',
        'time': datetime.now().isoformat(),
        'ip': '192.168.0.120'
    })

# ==================== TEXT-TO-SPEECH ROUTES ====================

@app.route('/api/tts/voices', methods=['GET'])
def get_voices():
    try:
        voices = tts_model.get_available_voices()
        return jsonify({'success': True, 'voices': voices})
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tts/speak', methods=['POST'])
def speak_text():
    try:
        data = request.json
        text = data.get('text', '')
        voice_id = data.get('voice_id', 0)
        rate = data.get('rate', 170)
        volume = data.get('volume', 0.9)
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400
        
        filename = f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        result = tts_model.speak(text, voice_id, rate, volume, filepath)
        
        if result:
            return send_file(result, as_attachment=True, download_name=filename)
        else:
            return jsonify({'success': False, 'error': 'TTS failed'}), 500
            
    except Exception as e:
        logger.error(f"Error in TTS: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tts/save', methods=['POST'])
def save_audio():
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400
        
        filename = f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        from gtts import gTTS
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(filepath)
        
        return jsonify({'success': True, 'filename': filename, 'filepath': filepath})
        
    except Exception as e:
        logger.error(f"Error saving audio: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== TEXT-TO-SIGN ROUTES ====================

@app.route('/api/sign/convert', methods=['POST'])
def convert_to_sign():
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400
        
        result = sign_model.convert(text)
        
        return jsonify({'success': True, 'result': result})
        
    except Exception as e:
        logger.error(f"Error converting to sign: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sign/dictionary', methods=['GET'])
def get_sign_dictionary():
    try:
        dictionary = sign_model.get_dictionary()
        return jsonify({'success': True, 'dictionary': dictionary})
    except Exception as e:
        logger.error(f"Error getting dictionary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sign/image/<path:sign_name>', methods=['GET'])
def get_sign_image(sign_name):
    try:
        image_path = sign_model.get_sign_image(sign_name)
        if image_path and os.path.exists(image_path):
            return send_file(image_path)
        else:
            return jsonify({'success': False, 'error': 'Image not found'}), 404
    except Exception as e:
        logger.error(f"Error getting sign image: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== SIGN-TO-TEXT ROUTES ====================

@app.route('/api/s2t/detect', methods=['POST'])
def detect_sign():
    try:
        print("\n" + "="*60)
        print("🔴 SIGN DETECTION CALLED FROM MOBILE")
        print("="*60)
        
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        # Save temporarily
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_sign.jpg')
        file.save(temp_path)
        
        # Resize image to help MediaPipe detect hands better
        from PIL import Image
        img = Image.open(temp_path)
        
        # Resize to optimal size for MediaPipe (640x480)
        img = img.resize((640, 480), Image.Resampling.LANCZOS)
        img.save(temp_path)
        
        print(f"🖼️ Image resized to 640x480")
        
        # Process with the sign-to-text model
        result = s2t_model.process_image_file(temp_path)
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'result': {
                'mode': 'static',
                'current_word': result.get('current_word', ''),
                'sentence': result.get('sentence', ''),
                'has_hand': result.get('has_hand', False),
                'detected_letter': result.get('detected_letter', '')
            }
        })
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/s2t/clear', methods=['POST'])
def clear_sign_detection():
    """Clear current sign detection"""
    try:
        s2t_model.clear_sentence()
        return jsonify({
            'success': True,
            'message': 'Detection cleared',
            'sentence': ''
        })
    except Exception as e:
        logger.error(f"Error clearing: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/s2t/speak', methods=['POST'])
def speak_sign_sentence():
    """Speak the detected sign sentence"""
    try:
        sentence = s2t_model.get_full_text()
        if sentence:
            # Use TTS to speak
            from gtts import gTTS
            import io
            import base64
            
            tts = gTTS(text=sentence, lang='en', slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            audio_base64 = base64.b64encode(fp.read()).decode('utf-8')
            
            return jsonify({
                'success': True,
                'message': 'Speaking sentence',
                'sentence': sentence,
                'audio': audio_base64
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No sentence to speak'
            }), 400
    except Exception as e:
        logger.error(f"Error speaking: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== OBJECT DETECTION ROUTES ====================

@app.route('/api/object/status', methods=['GET'])
def object_status():
    """Get object detector status"""
    return jsonify({
        'success': True,
        'model_loaded': object_detector.model_loaded if hasattr(object_detector, 'model_loaded') else False,
        'available': object_detector.model_loaded if hasattr(object_detector, 'model_loaded') else False
    })

@app.route('/api/object/detect', methods=['POST'])
def detect_objects():
    """Detect objects in image - NO DEBUG IMAGES SAVED"""
    print("\n" + "="*60)
    print("🔴 OBJECT DETECTION CALLED FROM MOBILE")
    print("="*60)
    
    try:
        # Check if image is in request
        if 'image' not in request.files:
            print("❌ No image in request")
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        file = request.files['image']
        print(f"📁 File received: {file.filename}")
        print(f"📦 File size: {len(file.read())} bytes")
        file.seek(0)  # Reset file pointer
        
        if len(file.read()) == 0:
            print("❌ Empty file")
            return jsonify({'success': False, 'error': 'Empty file'}), 400
        file.seek(0)
        
        # Save temporarily (will be deleted after processing)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_object.jpg')
        file.save(temp_path)
        print(f"💾 Temp file saved")
        
        # Detect objects
        print("🔄 Running YOLO detection...")
        frame, objects, description = object_detector.detect_from_file(temp_path)
        
        print(f"✅ Detection complete")
        print(f"📊 Found {len(objects) if objects else 0} objects")
        
        # Clean up temp file - NO DEBUG COPY SAVED
        if os.path.exists(temp_path):
            os.remove(temp_path)
            print("🧹 Temp file deleted")
        
        return jsonify({
            'success': True,
            'objects': objects,
            'description': description,
            'count': len(objects) if objects else 0
        })
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== CURRENCY DETECTION ROUTES ====================

@app.route('/api/currency/detect', methods=['POST'])
def detect_currency():
    """Detect currency from uploaded image"""
    print("\n" + "="*60)
    print("💰 CURRENCY DETECTION CALLED FROM MOBILE")
    print("="*60)
    
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        file = request.files['image']
        print(f"📁 File received: {file.filename}")
        
        # Save temporarily
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_currency.jpg')
        file.save(temp_path)
        print(f"💾 Temp file saved: {temp_path}")
        
        # Detect currency
        print("🔄 Running currency detection...")
        result = currency_detector.detect_currency(temp_path)
        print(f"📊 Result: {result}")
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
            print("🧹 Temp file deleted")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/currency/status', methods=['GET'])
def currency_status():
    """Get currency detector status"""
    denominations = sorted(currency_detector.denominations)
    template_counts = {str(k): len(v) for k, v in currency_detector.templates.items()}
    
    return jsonify({
        'success': True,
        'denominations': denominations,
        'template_counts': template_counts,
        'total_templates': sum(len(v) for v in currency_detector.templates.values())
    })

# ==================== TEXT READER ROUTES ====================

@app.route('/api/text/detect', methods=['POST'])
def detect_text():
    """Detect text from uploaded image using OCR"""
    print("\n" + "="*60)
    print("📝 TEXT DETECTION CALLED FROM MOBILE")
    print("="*60)
    
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        file = request.files['image']
        print(f"📁 File received: {file.filename}")
        print(f"📦 File size: {len(file.read())} bytes")
        file.seek(0)
        
        # Save temporarily
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_text.jpg')
        file.save(temp_path)
        print(f"💾 Temp file saved: {temp_path}")
        
        # Detect text
        print("🔄 Running OCR text detection...")
        result = text_reader.detect_text(temp_path)
        print(f"📊 Result: {result}")
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
            print("🧹 Temp file deleted")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/text/status', methods=['GET'])
def text_status():
    """Get text reader status"""
    return jsonify({
        'success': True,
        'available': text_reader.available,
        'tesseract_version': str(text_reader.get_tesseract_version()) if hasattr(text_reader, 'get_tesseract_version') else None
    })

# ==================== EMERGENCY ROUTES ====================

@app.route('/api/emergency', methods=['POST'])
def send_emergency():
    try:
        data = request.json
        user_id = data.get('userId', 'unknown')
        location = data.get('location', {})
        emergency_type = data.get('type', 'general')
        
        logger.warning(f"🚨 EMERGENCY from {user_id}: {emergency_type} at {location}")
        
        return jsonify({
            'success': True,
            'message': 'Emergency alert sent',
            'alert_id': f"EMG_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error sending emergency: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== REGISTER BLUEPRINTS ====================
from routes.stt_routes import stt_bp
from routes.tts_routes import tts_bp
from routes.sign_routes import sign_bp
from routes.emergency_routes import emergency_bp

app.register_blueprint(stt_bp)
app.register_blueprint(tts_bp)
app.register_blueprint(sign_bp)
app.register_blueprint(emergency_bp)

# Register SocketIO handlers
from routes.stt_routes import register_socketio_handlers
register_socketio_handlers(socketio)

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

# ==================== MAIN ENTRY ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Starting server on port {port}")
    
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    logger.info(f"🌐 Local IP: {local_ip}")
    logger.info(f"📱 Use this IP in your React Native app: http://{local_ip}:{port}")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)