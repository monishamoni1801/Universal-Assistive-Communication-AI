# models/text_reader.py
import cv2
import pytesseract
import numpy as np
import os
import logging
from PIL import Image
import re

logger = logging.getLogger(__name__)

# Set Tesseract path (update this to your Tesseract installation path)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class TextReader:
    def __init__(self):
        """Initialize text reader with OCR engine"""
        self.available = self.check_tesseract()
        if self.available:
            print("✅ Tesseract OCR initialized successfully")
        else:
            print("⚠️ Tesseract OCR not found. Please install Tesseract")
    
    def check_tesseract(self):
        """Check if Tesseract is available"""
        try:
            # Try to get version
            version = pytesseract.get_tesseract_version()
            print(f"📚 Tesseract version: {version}")
            return True
        except:
            return False
    
    def preprocess_image(self, image):
        """Preprocess image for better OCR results"""
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply Gaussian blur to remove noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply threshold to get binary image
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoise
        denoised = cv2.medianBlur(thresh, 3)
        
        # Increase contrast
        enhanced = cv2.equalizeHist(denoised)
        
        return enhanced
    
    def detect_text(self, image_path, lang='eng'):
        """
        Detect text from image using Tesseract OCR
        
        Args:
            image_path: Path to image file
            lang: Language for OCR (default: 'eng')
        
        Returns:
            dict: Detection result with text and confidence
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                return {'success': False, 'error': 'Cannot read image'}
            
            # Preprocess image
            processed = self.preprocess_image(img)
            
            # Configure Tesseract
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?-:; '
            
            # Perform OCR
            text = pytesseract.image_to_string(processed, config=custom_config, lang=lang)
            
            # Get confidence data
            try:
                data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if conf != '-1']
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            except:
                avg_confidence = 0
            
            # Clean up text
            text = text.strip()
            text = re.sub(r'\n+', '\n', text)  # Remove multiple newlines
            text = re.sub(r' +', ' ', text)    # Remove multiple spaces
            
            if text:
                print(f"✅ Detected text: {text[:50]}...")
                return {
                    'success': True,
                    'text': text,
                    'confidence': avg_confidence / 100.0,
                    'length': len(text),
                    'words': len(text.split())
                }
            else:
                print("❌ No text detected")
                return {
                    'success': False,
                    'error': 'No text detected',
                    'text': ''
                }
                
        except Exception as e:
            logger.error(f"Text detection error: {e}")
            return {'success': False, 'error': str(e)}
    
    def detect_text_from_base64(self, base64_string):
        """Process base64 encoded image"""
        import base64
        from io import BytesIO
        
        try:
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            image_bytes = base64.b64decode(base64_string)
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Save temporarily
            temp_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'temp_text.jpg')
            cv2.imwrite(temp_path, img)
            
            result = self.detect_text(temp_path)
            
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def detect_text_from_pil(self, pil_image):
        """Process PIL Image directly"""
        try:
            # Convert PIL to OpenCV
            img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # Save temporarily
            temp_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'temp_text.jpg')
            cv2.imwrite(temp_path, img)
            
            result = self.detect_text(temp_path)
            
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}