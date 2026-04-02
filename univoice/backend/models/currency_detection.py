# models/currency_detection.py
import cv2
import numpy as np
import os
import re
import logging
import glob

logger = logging.getLogger(__name__)

class CurrencyDetector:
    def __init__(self):
        """Initialize currency detector with template images"""
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.dataset_path = os.path.join(self.base_dir, 'currency_dataset')
        self.templates = {}  # Format: {value: [list_of_images]}
        self.denominations = []
        self.load_templates()
        
    def extract_denomination(self, filename):
        """Extract denomination from filename like '10_google.jpeg'"""
        match = re.match(r'^(\d+)', filename)
        if match:
            return int(match.group(1))
        return None
        
    def load_templates(self):
        """Load all currency template images from dataset folder"""
        print("\n" + "="*60)
        print("💰 LOADING CURRENCY DATASET")
        print("="*60)
        print(f"📁 Dataset path: {self.dataset_path}")
        
        if not os.path.exists(self.dataset_path):
            print(f"❌ Dataset folder not found: {self.dataset_path}")
            return
        
        # Get all image files
        image_files = []
        for ext in ['*.jpeg', '*.jpg', '*.png']:
            image_files.extend(glob.glob(os.path.join(self.dataset_path, ext)))
        
        print(f"📸 Found {len(image_files)} total images")
        
        # Group by denomination
        for img_path in image_files:
            filename = os.path.basename(img_path)
            value = self.extract_denomination(filename)
            
            if value:
                # Load image
                img = cv2.imread(img_path)
                if img is not None:
                    # Store both color and grayscale versions
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    
                    # Store multiple sizes for scale invariance
                    sizes = [(200, 100), (300, 150), (400, 200)]
                    for size in sizes:
                        resized = cv2.resize(gray, size)
                        
                        if value not in self.templates:
                            self.templates[value] = []
                            if value not in self.denominations:
                                self.denominations.append(value)
                        
                        self.templates[value].append({
                            'image': resized,
                            'size': size,
                            'source': filename
                        })
                    
                    print(f"  ✅ Loaded: ₹{value} from {filename}")
        
        print("\n" + "="*60)
        print("📊 DENOMINATION SUMMARY:")
        for value in sorted(self.denominations):
            count = len(self.templates.get(value, [])) // 3
            print(f"  • ₹{value}: {count} images, {len(self.templates.get(value, []))} templates")
        print("="*60 + "\n")
        
    def detect_currency(self, image_path, threshold=0.25):
        """
        Detect currency using enhanced template matching with stronger discrimination
        """
        try:
            # Read input image
            img = cv2.imread(image_path)
            if img is None:
                return {'success': False, 'error': 'Cannot read image'}
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply CLAHE for better contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            
            # Try multiple scales of the input image
            scales = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
            all_matches = []
            
            print(f"🔍 Searching for currency...")
            
            for scale in scales:
                # Resize input image
                if scale != 1.0:
                    width = int(gray.shape[1] * scale)
                    height = int(gray.shape[0] * scale)
                    if width < 50 or height < 50:
                        continue
                    scaled_img = cv2.resize(gray, (width, height))
                else:
                    scaled_img = gray
                
                # Try each denomination
                for value, templates in self.templates.items():
                    for template_data in templates:
                        template = template_data['image']
                        
                        # Skip if template is larger than scaled image
                        if template.shape[0] > scaled_img.shape[0] or template.shape[1] > scaled_img.shape[1]:
                            continue
                        
                        # Template matching
                        result = cv2.matchTemplate(scaled_img, template, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, max_loc = cv2.minMaxLoc(result)
                        
                        if max_val > threshold:
                            all_matches.append({
                                'value': value,
                                'confidence': float(max_val),
                                'scale': scale,
                                'location': max_loc
                            })
                            # Only print high confidence matches to reduce noise
                            if max_val > 0.3:
                                print(f"  ✓ ₹{value} at scale {scale:.2f} with confidence: {max_val:.2f}")
            
            # Group matches by value
            if all_matches:
                # Count matches per denomination
                match_counts = {}
                match_confidences = {}
                high_conf_matches = {}  # Matches with confidence > 0.35
                
                for match in all_matches:
                    val = match['value']
                    conf = match['confidence']
                    
                    if val not in match_counts:
                        match_counts[val] = 0
                        match_confidences[val] = []
                        high_conf_matches[val] = 0
                    
                    match_counts[val] += 1
                    match_confidences[val].append(conf)
                    
                    if conf > 0.35:
                        high_conf_matches[val] += 1
                
                # Calculate average confidence for each denomination
                avg_confidences = {
                    val: sum(confs)/len(confs) for val, confs in match_confidences.items()
                }
                
                # Calculate max confidence for each denomination
                max_confidences = {
                    val: max(confs) for val, confs in match_confidences.items()
                }
                
                print("\n📊 MATCH STATISTICS:")
                for val in sorted(match_counts.keys()):
                    print(f"  ₹{val}: {match_counts[val]} matches, "
                          f"avg conf: {avg_confidences[val]:.2f}, "
                          f"max conf: {max_confidences[val]:.2f}, "
                          f"high conf: {high_conf_matches[val]}")
                
                # Calculate weighted score with strong bias against problematic denominations
                # Based on your logs, ₹500 and ₹100 are over-detected
                scores = {}
                for val in match_counts:
                    # Base score: (high confidence matches * 0.5) + (max confidence * 0.3) + (avg confidence * 0.2)
                    base_score = (high_conf_matches[val] * 0.5) + (max_confidences[val] * 0.3) + (avg_confidences[val] * 0.2)
                    
                    # Apply strong bias adjustment
                    if val == 500:
                        bias = 0.5  # Reduce ₹500 score by 50%
                    elif val == 100:
                        bias = 0.7  # Reduce ₹100 score by 30%
                    elif val == 200:
                        bias = 0.9  # Slight reduction
                    elif val == 10:
                        bias = 1.5  # Boost ₹10 score
                    elif val == 20:
                        bias = 1.4  # Boost ₹20 score
                    elif val == 50:
                        bias = 1.3  # Boost ₹50 score
                    else:
                        bias = 1.0
                    
                    scores[val] = base_score * bias
                    
                    print(f"  ₹{val} base score: {base_score:.2f}, bias: {bias}, final: {scores[val]:.2f}")
                
                # Find denomination with highest score
                best_value = max(scores, key=scores.get)
                best_match = max([m for m in all_matches if m['value'] == best_value], 
                                key=lambda x: x['confidence'])
                
                # Final confidence with adjustment
                final_confidence = best_match['confidence']
                
                # Additional confidence boost for correctly detected small denominations
                if best_value in [10, 20, 50] and high_conf_matches[best_value] >= 2:
                    final_confidence = min(1.0, final_confidence * 1.2)
                
                # Require minimum matches
                min_matches_required = {
                    10: 2,
                    20: 2,
                    50: 2,
                    100: 3,
                    200: 3,
                    500: 4
                }
                
                required = min_matches_required.get(best_value, 2)
                
                if match_counts[best_value] >= required and final_confidence > threshold:
                    result = {
                        'success': True,
                        'value': best_value,
                        'confidence': final_confidence,
                        'denomination': f"₹{best_value}",
                        'scale': best_match['scale'],
                        'matches_found': len(all_matches),
                        'match_counts': match_counts,
                        'high_conf_matches': high_conf_matches[best_value]
                    }
                    print(f"\n✅ FINAL DETECTION: {result['denomination']} "
                          f"(confidence: {final_confidence:.2f}, "
                          f"matches: {match_counts[best_value]})")
                    return result
                else:
                    print(f"\n❌ Insufficient matches for ₹{best_value} "
                          f"(need {required}, got {match_counts.get(best_value, 0)})")
                    return {
                        'success': False,
                        'error': 'Insufficient matches',
                        'value': 0,
                        'confidence': 0
                    }
            else:
                print("❌ No currency detected")
                return {
                    'success': False,
                    'error': 'No currency detected',
                    'value': 0,
                    'confidence': 0
                }
                
        except Exception as e:
            logger.error(f"Currency detection error: {e}")
            return {'success': False, 'error': str(e)}
    
    def detect_from_base64(self, base64_string):
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
            temp_path = os.path.join(self.base_dir, 'uploads', 'temp_currency.jpg')
            cv2.imwrite(temp_path, img)
            
            result = self.detect_currency(temp_path)
            
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}