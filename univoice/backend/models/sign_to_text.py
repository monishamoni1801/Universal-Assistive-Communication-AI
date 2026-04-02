# models/sign_to_text.py
import cv2
import numpy as np
import mediapipe as mp
import tensorflow as tf
import time
import os
import base64
from io import BytesIO
from PIL import Image
import logging
import json

logger = logging.getLogger(__name__)

class SignToTextConverter:
    def __init__(self):
        """Initialize the sign language to text converter"""
        # Load the letter model
        self.model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "letter_model.h5")
        self.mapping_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "letter_mapping.json")
        
        # Check if model exists
        if os.path.exists(self.model_path):
            try:
                self.model = tf.keras.models.load_model(self.model_path)
                logger.info("✅ Letter model loaded successfully")
                self.model_loaded = True
                print("✅ Letter model loaded successfully")
                
                # Get model output shape to determine number of classes
                self.num_classes = self.model.output_shape[-1]
                print(f"📊 Model outputs {self.num_classes} classes")
                
            except Exception as e:
                logger.error(f"❌ Error loading model: {e}")
                print(f"❌ Error loading model: {e}")
                self.model_loaded = False
        else:
            logger.warning(f"⚠️ Letter model not found at {self.model_path}. Using demo mode.")
            print(f"⚠️ Letter model not found at {self.model_path}. Using demo mode.")
            self.model_loaded = False
        
        # Labels for letters A-Z
        self.labels = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        print(f"📝 Default labels: {self.labels[:5]}... (total {len(self.labels)} letters)")
        
        # Load or create correction mapping
        self.correction_map = self.load_correction_mapping()
        
        # Initialize MediaPipe Hands with SIMPLE settings
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=True,
            max_num_hands=1,
            min_detection_confidence=0.3,
            min_tracking_confidence=0.3
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Detection state
        self.current_sentence = []
        self.current_word = ""
        self.current_letter = ""
        self.start_time = None
        self.detection_mode = "static"
        self.last_detection_time = time.time()
        self.detection_cooldown = 0.5
        
        # Frame counter for debugging
        self.frame_counter = 0
        
        # Confidence threshold
        self.confidence_threshold = 0.3
        
        logger.info("✅ SignToTextConverter initialized")
        print("✅ SignToTextConverter initialized")
    
    def load_correction_mapping(self):
        """Load correction mapping from file or create default"""
        mapping = {}
        
        # Default mapping based on your observed wrong outputs
        default_mapping = {
            24: 'Y',  # From your log: Class 24 was detected as 'Y'
        }
        
        # Try to load from file
        if os.path.exists(self.mapping_path):
            try:
                with open(self.mapping_path, 'r') as f:
                    loaded_map = json.load(f)
                    mapping = {int(k): v for k, v in loaded_map.items()}
                print(f"✅ Loaded {len(mapping)} correction mappings from file")
            except Exception as e:
                print(f"⚠️ Error loading mapping file: {e}")
                mapping = default_mapping
        else:
            print("📝 No mapping file found, using default mapping")
            mapping = default_mapping
            self.save_correction_mapping(mapping)
        
        return mapping
    
    def save_correction_mapping(self, mapping=None):
        """Save correction mapping to file"""
        if mapping is None:
            mapping = self.correction_map
        
        try:
            with open(self.mapping_path, 'w') as f:
                json.dump(mapping, f, indent=2)
            print(f"✅ Saved {len(mapping)} correction mappings to file")
        except Exception as e:
            print(f"⚠️ Error saving mapping file: {e}")
    
    def add_correction(self, wrong_class_id, correct_letter):
        """Add a new correction mapping"""
        self.correction_map[wrong_class_id] = correct_letter
        self.save_correction_mapping()
        print(f"✅ Added correction: Class {wrong_class_id} → '{correct_letter}'")
    
    def get_correct_letter(self, class_id, confidence):
        """Get correct letter using correction mapping"""
        if class_id in self.correction_map:
            corrected = self.correction_map[class_id]
            print(f"🔄 CORRECTED: Class {class_id} → '{corrected}'")
            return corrected
        
        if class_id < len(self.labels):
            return self.labels[class_id]
        
        return ''
    
    def process_frame(self, frame):
        """
        SIMPLIFIED version for better hand detection
        """
        print("\n--- Processing new frame ---")
        print(f"📸 Frame received - Shape: {frame.shape}")
        
        self.frame_counter += 1
        
        # STEP 1: SIMPLE RESIZE to size MediaPipe likes
        frame = cv2.resize(frame, (640, 480))
        print(f"📏 Resized to: 640x480")
        
        # Save original for debugging
        if self.frame_counter <= 5:
            cv2.imwrite(f"debug_original_{self.frame_counter}.jpg", frame)
        
        # STEP 2: Flip horizontally
        frame = cv2.flip(frame, 1)
        
        if self.frame_counter <= 5:
            cv2.imwrite(f"debug_flipped_{self.frame_counter}.jpg", frame)
        
        # STEP 3: Convert to RGB for MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # STEP 4: Process with MediaPipe
        result = self.hands.process(rgb)
        
        detected_letter = ""
        confidence = 0.0
        has_hand = False
        raw_class_id = -1
        
        if result.multi_hand_landmarks:
            has_hand = True
            print(f"✅ HAND DETECTED! Found {len(result.multi_hand_landmarks)} hands")
            
            # Get first hand
            hand_landmarks = result.multi_hand_landmarks[0]
            
            # Get bounding box
            h, w, _ = frame.shape
            x_list = [int(lm.x * w) for lm in hand_landmarks.landmark]
            y_list = [int(lm.y * h) for lm in hand_landmarks.landmark]
            
            # Add padding
            padding = 40
            x_min = max(min(x_list) - padding, 0)
            x_max = min(max(x_list) + padding, w)
            y_min = max(min(y_list) - padding, 0)
            y_max = min(max(y_list) + padding, h)
            
            print(f"    Bounding box: ({x_min},{y_min}) to ({x_max},{y_max})")
            
            # Draw bounding box for debugging
            debug_frame = frame.copy()
            cv2.rectangle(debug_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            
            if self.frame_counter <= 5:
                cv2.imwrite(f"debug_box_{self.frame_counter}.jpg", debug_frame)
            
            # Crop hand region
            crop = frame[y_min:y_max, x_min:x_max]
            
            if crop.size > 0:
                print(f"    Crop shape: {crop.shape}")
                
                if self.frame_counter <= 5:
                    cv2.imwrite(f"debug_crop_{self.frame_counter}.jpg", crop)
                
                if self.model_loaded:
                    # SIMPLE preprocessing
                    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                    
                    # Simple binary threshold
                    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
                    
                    # Resize to model input size
                    resized = cv2.resize(thresh, (28, 28))
                    
                    if self.frame_counter <= 5:
                        cv2.imwrite(f"debug_thresh_{self.frame_counter}.jpg", resized)
                    
                    # Normalize and reshape
                    normalized = resized / 255.0
                    img = normalized.reshape(1, 28, 28, 1)
                    
                    # Predict
                    pred = self.model.predict(img, verbose=0)
                    class_id = np.argmax(pred)
                    confidence = float(np.max(pred))
                    raw_class_id = class_id
                    
                    print(f"    Class: {class_id}, Confidence: {confidence:.4f}")
                    
                    if confidence > self.confidence_threshold:
                        detected_letter = self.get_correct_letter(class_id, confidence)
                        print(f"    ✅ Detected: {detected_letter}")
                    else:
                        print(f"    ⚠️ Low confidence: {confidence:.4f}")
                else:
                    print("    ⚠️ Model not loaded, using demo mode")
        else:
            print("❌ NO HAND DETECTED")
            
            # Save frame for debugging
            if self.frame_counter <= 5:
                cv2.imwrite(f"debug_no_hand_{self.frame_counter}.jpg", frame)
        
        # Apply hold detection logic
        current_time = time.time()
        
        if detected_letter and confidence > self.confidence_threshold:
            print(f"🔄 Processing letter: {detected_letter}")
            
            if detected_letter == self.current_letter:
                if self.start_time:
                    hold_duration = current_time - self.start_time
                    if hold_duration > 1.5:
                        self.current_word += detected_letter
                        print(f"✅ Added to word: {self.current_word}")
                        self.current_letter = ""
                        self.start_time = None
            else:
                self.current_letter = detected_letter
                self.start_time = current_time
        
        result_dict = {
            'has_hand': has_hand,
            'detected_letter': detected_letter,
            'confidence': confidence,
            'current_word': self.current_word,
            'sentence': ' '.join(self.current_sentence) + (' ' + self.current_word if self.current_word else ''),
            'raw_class_id': raw_class_id
        }
        
        print(f"📤 Returning: {result_dict}")
        return result_dict
    
    def add_word_to_sentence(self):
        """Add current word to sentence"""
        if self.current_word:
            self.current_sentence.append(self.current_word)
            print(f"📝 Added word to sentence: {self.current_word}")
            self.current_word = ""
            return True
        return False
    
    def clear_sentence(self):
        """Clear current sentence"""
        self.current_sentence = []
        self.current_word = ""
        self.current_letter = ""
        self.start_time = None
        print("🧹 Sentence cleared")
    
    def get_sentence(self):
        """Get current sentence"""
        return ' '.join(self.current_sentence)
    
    def get_full_text(self):
        """Get full text"""
        if self.current_word:
            return ' '.join(self.current_sentence) + ' ' + self.current_word
        return ' '.join(self.current_sentence)
    
    def process_image_file(self, image_path):
        """Process image file"""
        try:
            print(f"📂 Processing image file: {image_path}")
            
            if not os.path.exists(image_path):
                return {'success': False, 'error': 'File not found'}
            
            # Read image
            frame = cv2.imread(image_path)
            if frame is None:
                pil_image = Image.open(image_path)
                frame = np.array(pil_image)
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            if frame is None:
                return {'success': False, 'error': 'Could not read image'}
            
            print(f"✅ Image loaded: {frame.shape}")
            return self.process_frame(frame)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return {'success': False, 'error': str(e)}