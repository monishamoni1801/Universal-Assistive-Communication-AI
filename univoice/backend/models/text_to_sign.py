# models/text_to_sign.py
import os
import string
import base64
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class TextToSign:
    def __init__(self, base_dir=None):
        """Initialize sign language converter"""
        if base_dir is None:
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        else:
            self.base_dir = base_dir
        
        # Paths for sign resources (YOUR existing folders)
        self.gif_dir = os.path.join(self.base_dir, 'models', 'ISL_Gifs')
        self.letters_dir = os.path.join(self.base_dir, 'models', 'letters')
        
        # Create directories if they don't exist
        os.makedirs(self.gif_dir, exist_ok=True)
        os.makedirs(self.letters_dir, exist_ok=True)
        
        # YOUR GIF phrases list
        self.isl_gifs = [
            'any questions', 'are you angry', 'are you busy', 'are you hungry', 
            'are you sick', 'be careful', 'can we meet tomorrow', 'did you book tickets',
            'did you finish homework', 'do you go to office', 'do you have money',
            'do you want something to drink', 'do you want tea or coffee', 'do you watch TV',
            'dont worry', 'flower is beautiful', 'good afternoon', 'good evening',
            'good morning', 'good night'
        ]
        
        # Letters
        self.letters = list(string.ascii_lowercase)
        
        # Scan available GIFs
        self.available_gifs = self._scan_gifs()
        logger.info(f"✅ TextToSign initialized with {len(self.available_gifs)} GIFs")
    
    def _scan_gifs(self):
        """Scan for available GIF files"""
        gifs = []
        if os.path.exists(self.gif_dir):
            for file in os.listdir(self.gif_dir):
                if file.endswith('.gif'):
                    gifs.append(file.replace('.gif', '').lower())
        return gifs
    
    def is_available(self):
        return len(self.available_gifs) > 0 or os.path.exists(self.letters_dir)
    
    def convert(self, text):
        """Convert text to sign language representation"""
        text = text.lower().strip()
        text = ''.join(ch for ch in text if ch.isalnum() or ch.isspace())
        
        result = {
            'original': text,
            'signs': [],
            'type': 'unknown'
        }
        
        # Check for GIF phrase match
        for phrase in self.isl_gifs:
            if phrase in text:
                gif_path = os.path.join(self.gif_dir, f'{phrase}.gif')
                if os.path.exists(gif_path):
                    gif_base64 = self._image_to_base64(gif_path)
                    result['signs'].append({
                        'type': 'gif',
                        'phrase': phrase,
                        'data': gif_base64,
                        'url': f'/models/ISL_Gifs/{phrase}.gif'
                    })
                    result['type'] = 'gif'
                    return result
        
        # Letter fallback
        for char in text:
            if char == ' ':
                result['signs'].append({'type': 'space', 'character': ' '})
                continue
                
            if char in self.letters:
                img_path = os.path.join(self.letters_dir, f'{char}.jpg')
                if os.path.exists(img_path):
                    img_base64 = self._image_to_base64(img_path)
                    result['signs'].append({
                        'type': 'letter',
                        'character': char,
                        'data': img_base64,
                        'url': f'/models/letters/{char}.jpg'
                    })
                else:
                    result['signs'].append({'type': 'missing', 'character': char})
        
        result['type'] = 'letters' if result['signs'] else 'none'
        return result
    
    def _image_to_base64(self, image_path):
        """Convert image to base64"""
        try:
            with open(image_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Image error: {e}")
            return None
    
    def get_dictionary(self):
        """Get dictionary of signs"""
        dictionary = []
        
        for phrase in self.isl_gifs:
            dictionary.append({
                'word': phrase,
                'type': 'gif',
                'url': f'/models/ISL_Gifs/{phrase}.gif'
            })
        
        for letter in self.letters:
            img_path = os.path.join(self.letters_dir, f'{letter}.jpg')
            dictionary.append({
                'word': letter,
                'type': 'letter',
                'url': f'/models/letters/{letter}.jpg' if os.path.exists(img_path) else None
            })
        
        return dictionary
    
    def get_sign_image(self, sign_name):
        """Get image path for sign"""
        gif_path = os.path.join(self.gif_dir, f'{sign_name}.gif')
        if os.path.exists(gif_path):
            return gif_path
        
        letter_path = os.path.join(self.letters_dir, f'{sign_name}.jpg')
        if os.path.exists(letter_path):
            return letter_path
        
        return None