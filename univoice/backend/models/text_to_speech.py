# models/text_to_speech.py
import pyttsx3
import os
import base64
from io import BytesIO
from gtts import gTTS
import logging

logger = logging.getLogger(__name__)

class TextToSpeech:
    def __init__(self):
        """Initialize TTS engine"""
        self.rate = 170
        self.volume = 0.9
        self.voice_id = None
        self.voices = []
        self.available = False
        self._init_engine()
    
    def _init_engine(self):
        """Initialize pyttsx3 engine"""
        try:
            engine = pyttsx3.init()
            self.voices = engine.getProperty('voices')
            engine.stop()
            
            if self.voices:
                self.voice_id = self.voices[0].id
            
            self.available = True
            logger.info(f"✅ TTS initialized with {len(self.voices)} voices")
        except Exception as e:
            logger.warning(f"❌ TTS init error: {e}")
            self.available = False
    
    def is_available(self):
        return self.available
    
    def get_available_voices(self):
        """Get list of available voices"""
        voices_list = []
        for i, voice in enumerate(self.voices):
            voices_list.append({
                'id': i,
                'name': voice.name,
                'gender': 'Male' if 'male' in voice.name.lower() else 'Female'
            })
        return voices_list
    
    def speak(self, text, voice_id=0, rate=170, volume=0.9, output_file=None):
        """Convert text to speech"""
        if not text:
            return None
        
        if output_file:
            return self._save_to_file(text, voice_id, rate, volume, output_file)
        
        return self._play_direct(text, voice_id, rate, volume)
    
    def _play_direct(self, text, voice_id, rate, volume):
        """Play speech directly"""
        try:
            engine = pyttsx3.init()
            
            if 0 <= voice_id < len(self.voices):
                engine.setProperty('voice', self.voices[voice_id].id)
            
            engine.setProperty('rate', rate)
            engine.setProperty('volume', volume)
            
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            
            logger.info(f"🔊 Spoke: {text[:30]}...")
            return True
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return False
    
    def _save_to_file(self, text, voice_id, rate, volume, output_file):
        """Save speech to file"""
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Try gTTS first
            try:
                tts = gTTS(text=text, lang='en', slow=False)
                tts.save(output_file)
                logger.info(f"💾 Saved to {output_file}")
                return output_file
            except:
                # Fallback to pyttsx3
                engine = pyttsx3.init()
                engine.setProperty('rate', rate)
                engine.setProperty('volume', volume)
                engine.save_to_file(text, output_file)
                engine.runAndWait()
                engine.stop()
                return output_file
                
        except Exception as e:
            logger.error(f"Save error: {e}")
            return None
    
    def speak_to_base64(self, text):
        """Convert to base64"""
        try:
            tts = gTTS(text=text, lang='en', slow=False)
            fp = BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return base64.b64encode(fp.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Base64 error: {e}")
            return None