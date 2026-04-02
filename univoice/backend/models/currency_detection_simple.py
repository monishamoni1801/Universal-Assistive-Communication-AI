# models/currency_detection_final.py
import cv2
import numpy as np
import os
import re
import logging
import glob

logger = logging.getLogger(__name__)

class CurrencyDetector:
    def __init__(self):
        """Initialize currency detector with multiple methods"""
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.dataset_path = os.path.join(self.base_dir, 'currency_dataset')
        self.templates = {}
        self.features = {}
        self.denominations = []
        self.orb = cv2.ORB_create(nfeatures=500)
        self.load_templates()
        
    def extract_denomination(self, filename):
        match = re.match(r'^(\d+)', filename)
        if match:
            return int(match.group(1))
        return None
        
    def load_templates(self):
        print("\n" + "="*60)
        print("💰 LOADING CURRENCY DATASET")
        print("="*60)
        print(f"📁 Dataset path: {self.dataset_path}")
        
        if not os.path.exists(self.dataset_path):
            print(f"❌ Dataset folder not found: {self.dataset_path}")
            return
        
        image_files = []
        for ext in ['*.jpeg', '*.jpg', '*.png']:
            image_files.extend(glob.glob(os.path.join(self.dataset_path, ext)))
        
        print(f"📸 Found {len(image_files)} total images")
        
        for img_path in image_files:
            filename = os.path.basename(img_path)
            value = self.extract_denomination(filename)
            
            if value:
                img = cv2.imread(img_path)
                if img is not None:
                    if value not in self.templates:
                        self.templates[value] = []
                        self.features[value] = []
                        if value not in self.denominations:
                            self.denominations.append(value)
                    
                    self.templates[value].append(img)
                    
                    # Extract ORB features
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    kp, des = self.orb.detectAndCompute(gray, None)
                    if des is not None:
                        self.features[value].append(des)
                    
                    print(f"  ✅ Loaded: ₹{value} from {filename}")
        
        print("\n📊 SUMMARY:")
        for value in sorted(self.denominations):
            print(f"  • ₹{value}: {len(self.templates[value])} images")
        print("="*60 + "\n")
    
    def enhance_image(self, img):
        """Enhance image for better matching"""
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE for better contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
        
        # Apply adaptive threshold
        binary = cv2.adaptiveThreshold(blurred, 255, 
                                      cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY, 11, 2)
        
        return binary
    
    def detect_currency(self, image_path):
        """
        Detect currency using multiple methods and voting
        """
        try:
            # Read input image
            img = cv2.imread(image_path)
            if img is None:
                return {'success': False, 'error': 'Cannot read image'}
            
            print(f"\n🔍 ANALYZING CURRENCY...")
            
            # Enhance image
            enhanced = self.enhance_image(img)
            
            # METHOD 1: Template Matching with multiple scales
            template_votes = {}
            scales = [0.5, 0.75, 1.0, 1.25, 1.5]
            
            for scale in scales:
                h, w = enhanced.shape
                scaled = cv2.resize(enhanced, (int(w*scale), int(h*scale)))
                
                for value, templates in self.templates.items():
                    for template in templates:
                        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                        template_resized = cv2.resize(template_gray, (200, 100))
                        
                        if scaled.shape[0] < 100 or scaled.shape[1] < 200:
                            continue
                        
                        # Try matching
                        result = cv2.matchTemplate(scaled, template_resized, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, _ = cv2.minMaxLoc(result)
                        
                        if max_val > 0.3:
                            if value not in template_votes:
                                template_votes[value] = 0
                            template_votes[value] += 1
            
            print(f"  📊 Template votes: {template_votes}")
            
            # METHOD 2: ORB Feature Matching
            orb_matches = {}
            query_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            kp_query, des_query = self.orb.detectAndCompute(query_gray, None)
            
            if des_query is not None:
                for value, descriptors_list in self.features.items():
                    best_match = 0
                    for des in descriptors_list:
                        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                        matches = bf.match(des_query, des)
                        good_matches = [m for m in matches if m.distance < 50]
                        if len(good_matches) > best_match:
                            best_match = len(good_matches)
                    if best_match > 5:
                        orb_matches[value] = best_match
            
            print(f"  📊 ORB matches: {orb_matches}")
            
            # METHOD 3: Aspect Ratio
            h, w = img.shape[:2]
            aspect_ratio = w / h
            print(f"  📏 Aspect ratio: {aspect_ratio:.2f}")
            
            # METHOD 4: Color Analysis
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            avg_hue = np.mean(hsv[:,:,0])
            avg_sat = np.mean(hsv[:,:,1])
            print(f"  🎨 Color - Hue: {avg_hue:.1f}, Saturation: {avg_sat:.1f}")
            
            # COMBINE ALL METHODS with weights
            final_scores = {}
            
            for value in self.denominations:
                score = 0
                
                # Template voting (30%)
                if value in template_votes:
                    score += min(30, template_votes[value] * 5)
                
                # ORB matching (40%)
                if value in orb_matches:
                    score += min(40, orb_matches[value] * 2)
                
                # Aspect ratio (15%)
                if value == 10:
                    if 1.4 < aspect_ratio < 1.6:
                        score += 15
                elif value == 20:
                    if 1.4 < aspect_ratio < 1.6:
                        score += 15
                elif value == 50:
                    if 1.5 < aspect_ratio < 1.7:
                        score += 15
                elif value == 100:
                    if 1.7 < aspect_ratio < 1.9:
                        score += 15
                elif value == 200:
                    if 1.7 < aspect_ratio < 1.9:
                        score += 15
                elif value == 500:
                    if 1.7 < aspect_ratio < 1.9:
                        score += 15
                
                # Color (15%)
                if value == 10:
                    if 20 < avg_hue < 40:  # Yellow-ish
                        score += 15
                elif value == 20:
                    if 30 < avg_hue < 50:
                        score += 15
                elif value == 50:
                    if 40 < avg_hue < 60:
                        score += 15
                elif value == 100:
                    if 10 < avg_hue < 30:  # Blue-ish
                        score += 15
                elif value == 200:
                    if 0 < avg_hue < 20:   # Red-ish
                        score += 15
                elif value == 500:
                    if 350 < avg_hue < 360 or 0 < avg_hue < 10:  # Purple-ish
                        score += 15
                
                final_scores[value] = score
                print(f"  ₹{value}: {score} points")
            
            # Find best match
            if final_scores:
                best_value = max(final_scores, key=final_scores.get)
                best_score = final_scores[best_value]
                
                # Need at least 40 points for confidence
                if best_score > 40:
                    confidence = min(1.0, best_score / 100)
                    result = {
                        'success': True,
                        'value': best_value,
                        'confidence': confidence,
                        'denomination': f"₹{best_value}",
                        'scores': final_scores,
                        'template_votes': template_votes,
                        'orb_matches': orb_matches
                    }
                    print(f"\n✅ DETECTED: {result['denomination']} (confidence: {confidence:.2f})")
                    return result
                else:
                    print(f"❌ Low confidence score: {best_score}")
                    return {'success': False, 'error': 'Low confidence'}
            
            return {'success': False, 'error': 'No matches found'}
            
        except Exception as e:
            logger.error(f"Currency detection error: {e}")
            return {'success': False, 'error': str(e)}
    
    def detect_from_base64(self, base64_string):
        import base64
        from io import BytesIO
        
        try:
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            image_bytes = base64.b64decode(base64_string)
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            temp_path = os.path.join(self.base_dir, 'uploads', 'temp_currency.jpg')
            cv2.imwrite(temp_path, img)
            
            result = self.detect_currency(temp_path)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}