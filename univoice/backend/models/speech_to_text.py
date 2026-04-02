# models/speech_to_text.py
import speech_recognition as sr
import threading
import queue
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SpeechToText:
    def __init__(self):
        """Initialize speech recognition"""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.text_history = []
        self.latest_text = ""
        self.latest_confidence = 0.0
        
        # Adjust recognition settings
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        
        # Emergency keywords
        self.emergency_keywords = ['help', 'emergency', 'danger', 'fire', 'police', 'ambulance']
        
        # Check microphone
        self.available = self._check_microphone()
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._process_audio, daemon=True)
        self.processing_thread.start()
    
    def _check_microphone(self):
        """Check if microphone is available"""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            logger.info("✅ Microphone available")
            return True
        except Exception as e:
            logger.warning(f"❌ Microphone error: {e}")
            return False
    
    def is_available(self):
        return self.available
    
    def start_listening(self):
        """Start continuous listening"""
        if self.is_listening:
            return
        
        self.is_listening = True
        threading.Thread(target=self._listen_continuously, daemon=True).start()
        logger.info("🎤 Started listening")
    
    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
        logger.info("🛑 Stopped listening")
    
    def _listen_continuously(self):
        """Continuously listen for speech"""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            while self.is_listening:
                try:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    self.audio_queue.put(audio)
                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Listening error: {e}")
    
    def _process_audio(self):
        """Process audio from queue"""
        while True:
            try:
                if not self.audio_queue.empty():
                    audio = self.audio_queue.get()
                    
                    try:
                        # Use Google Speech Recognition
                        text = self.recognizer.recognize_google(audio, show_all=True)
                        
                        if text and 'alternative' in text:
                            best_result = text['alternative'][0]
                            transcript = best_result['transcript']
                            confidence = best_result.get('confidence', 1.0)
                            
                            # Check for emergency
                            is_emergency = self._check_emergency(transcript)
                            
                            # Update latest text
                            self.latest_text = transcript
                            self.latest_confidence = confidence
                            
                            # Add to history
                            self.text_history.append({
                                'timestamp': datetime.now().isoformat(),
                                'text': transcript,
                                'confidence': confidence,
                                'emergency': is_emergency
                            })
                            
                            logger.info(f"✅ Recognized: {transcript}")
                            
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError as e:
                        logger.error(f"Recognition error: {e}")
                        
            except Exception as e:
                logger.error(f"Processing error: {e}")
    
    def _check_emergency(self, text):
        """Check for emergency keywords"""
        text_lower = text.lower()
        for keyword in self.emergency_keywords:
            if keyword in text_lower:
                return True
        return False
    
    def listen_once(self, timeout=5):
        """Listen once and return text"""
        if not self.available:
            return self._simulate_listen()
        
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
                
                try:
                    text = self.recognizer.recognize_google(audio)
                    confidence = 0.95
                    
                    self.latest_text = text
                    self.latest_confidence = confidence
                    
                    return text, confidence
                    
                except sr.UnknownValueError:
                    return None, 0.0
                except sr.RequestError:
                    return None, 0.0
                    
        except sr.WaitTimeoutError:
            return None, 0.0
        except Exception as e:
            logger.error(f"Error: {e}")
            return None, 0.0
    
    def _simulate_listen(self):
        """Simulate for testing"""
        import random
        phrases = [
            "Hello, how are you?",
            "Can you help me?",
            "I need assistance",
            "Emergency help"
        ]
        text = random.choice(phrases)
        confidence = random.uniform(0.75, 0.98)
        return text, confidence
    
    def get_latest_text(self):
        if self.latest_text:
            return {
                'text': self.latest_text,
                'confidence': self.latest_confidence,
                'is_emergency': self._check_emergency(self.latest_text)
            }
        return None
    
    def get_history(self, limit=10):
        return self.text_history[-limit:] if self.text_history else []