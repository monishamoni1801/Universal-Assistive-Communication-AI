# models/currency_detector_simple.py
import cv2
import numpy as np
import os
import re
import logging
import glob

logger = logging.getLogger(__name__)

class CurrencyDetector:
    def __init__(self):
        """Initialize currency detector with simple rules"""
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.dataset_path = os.path.join(self.base_dir, 'currency_dataset')
        
        # Define simple characteristics for each note
        self.note_properties = {
            10: {
                'name': 'Ten',
                'color_range': [(20, 40), (30, 50)],  # Brown/Yellow
                'aspect_ratio': (1.4, 1.6),
                'brightness': (100, 180),
                'has_gandhi': False,
                'size': 'small'
            },
            20: {
                'name': 'Twenty',
                'color_range': [(30, 50), (40, 60)],  # Green/Yellow
                'aspect_ratio': (1.4, 1.6),
                'brightness': (100, 180),
                'has_gandhi': False,
                'size': 'small'
            },
            50: {
                'name': 'Fifty',
                'color_range': [(40, 60), (50, 70)],  # Violet
                'aspect_ratio': (1.5, 1.7),
                'brightness': (90, 170),
                'has_gandhi': True,
                'size': 'medium'
            },
            100: {
                'name': 'Hundred',
                'color_range': [(90, 110), (100, 120)],  # Blue
                'aspect_ratio': (1.6, 1.8),
                'brightness': (80, 160),
                'has_gandhi': True,
                'size': 'medium'
            },
            200: {
                'name': 'Two Hundred',
                'color_range': [(0, 20), (350, 360)],  # Red/Orange
                'aspect_ratio': (1.6, 1.8),
                'brightness': (90, 170),
                'has_gandhi': True,
                'size': 'medium'
            },
            500: {
                'name': 'Five Hundred',
                'color_range': [(140, 160), (130, 150)],  # Grey/Blue
                'aspect_ratio': (1.7, 1.9),
                'brightness': (70, 150),
                'has_gandhi': True,
                'size': 'large'
            }
        }
        
        self.denominations = list(self.note_properties.keys())
        print("\n" + "="*60)
        print("💰 SIMPLE CURRENCY DETECTOR")
        print("="*60)
        for d in sorted(self.denominations):
            print(f"  • ₹{d}: {self.note_properties[d]['name']}")
        print("="*60 + "\n")
    
    def analyze_image(self, img):
        """Extract basic properties from image"""
        h, w = img.shape[:2]
        aspect_ratio = w / h
        
        # Convert to HSV for color analysis
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Get dominant color (average hue)
        # Remove dark and very bright pixels
        mask = (hsv[:,:,2] > 50) & (hsv[:,:,2] < 200)
        if np.sum(mask) > 0:
            avg_hue = np.mean(hsv[:,:,0][mask])
            avg_sat = np.mean(hsv[:,:,1][mask])
            avg_val = np.mean(hsv[:,:,2][mask])
        else:
            avg_hue = np.mean(hsv[:,:,0])
            avg_sat = np.mean(hsv[:,:,1])
            avg_val = np.mean(hsv[:,:,2])
        
        # Calculate brightness
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        
        # Check for Gandhi portrait (using template matching)
        has_gandhi = self.check_for_gandhi(gray)
        
        return {
            'aspect_ratio': aspect_ratio,
            'avg_hue': avg_hue,
            'avg_sat': avg_sat,
            'avg_val': avg_val,
            'brightness': brightness,
            'has_gandhi': has_gandhi
        }
    
    def check_for_gandhi(self, gray):
        """Simple check for Gandhi portrait (using edge density in center)"""
        h, w = gray.shape
        center_region = gray[h//3:2*h//3, w//3:2*w//3]
        
        # Check edge density in center (Gandhi portrait has many edges)
        edges = cv2.Canny(center_region, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        return edge_density > 0.15
    
    def detect_currency(self, image_path):
        """
        Detect currency using simple rules
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                return {'success': False, 'error': 'Cannot read image'}
            
            print(f"\n🔍 ANALYZING NOTE...")
            
            # Analyze image
            props = self.analyze_image(img)
            
            print(f"  📊 Properties:")
            print(f"    • Aspect ratio: {props['aspect_ratio']:.2f}")
            print(f"    • Avg hue: {props['avg_hue']:.1f}")
            print(f"    • Brightness: {props['brightness']:.1f}")
            print(f"    • Has Gandhi: {props['has_gandhi']}")
            
            # Score each denomination
            scores = {}
            
            for denom, props_dict in self.note_properties.items():
                score = 0
                reasons = []
                
                # Aspect ratio check
                ar_min, ar_max = props_dict['aspect_ratio']
                if ar_min <= props['aspect_ratio'] <= ar_max:
                    score += 30
                    reasons.append(f"aspect ratio matches")
                else:
                    score -= 10
                
                # Color check (hue)
                color_matched = False
                for hue_range in props_dict['color_range']:
                    h_min, h_max = hue_range
                    if h_min <= h_max:
                        if h_min <= props['avg_hue'] <= h_max:
                            score += 40
                            color_matched = True
                            reasons.append(f"color matches")
                            break
                    else:
                        # Handle wrap-around (like red)
                        if props['avg_hue'] >= h_min or props['avg_hue'] <= h_max:
                            score += 40
                            color_matched = True
                            reasons.append(f"color matches")
                            break
                
                if not color_matched:
                    score -= 20
                
                # Brightness check
                b_min, b_max = props_dict['brightness']
                if b_min <= props['brightness'] <= b_max:
                    score += 20
                    reasons.append(f"brightness matches")
                else:
                    score -= 10
                
                # Gandhi check
                if props_dict['has_gandhi'] == props['has_gandhi']:
                    score += 10
                    reasons.append(f"Gandhi {'present' if props['has_gandhi'] else 'absent'} matches")
                else:
                    score -= 5
                
                scores[denom] = {
                    'score': score,
                    'reasons': reasons
                }
                
                print(f"  • ₹{denom}: {score} points - {', '.join(reasons)}")
            
            # Find best match
            best_denom = max(scores, key=lambda x: scores[x]['score'])
            best_score = scores[best_denom]['score']
            
            # Need at least 70 points for confidence
            if best_score < 70:
                print(f"❌ No confident match (best: {best_score} points)")
                return {
                    'success': False,
                    'error': 'No confident match',
                    'scores': {k: v['score'] for k, v in scores.items()}
                }
            
            # Special handling for 10 and 20 (they have similar properties)
            if best_denom in [10, 20] and best_score < 90:
                # Use aspect ratio to distinguish
                if props['aspect_ratio'] < 1.5:
                    best_denom = 10
                else:
                    best_denom = 20
            
            # Special handling for 100 and 500
            if best_denom in [100, 500]:
                # 500 is darker and has different texture
                if props['brightness'] < 100:
                    best_denom = 500
                else:
                    best_denom = 100
            
            result = {
                'success': True,
                'value': best_denom,
                'confidence': best_score / 100,
                'denomination': f"₹{best_denom}",
                'properties': props,
                'scores': {k: v['score'] for k, v in scores.items()}
            }
            
            print(f"\n✅ DETECTED: {result['denomination']} (confidence: {best_score}%)")
            return result
            
        except Exception as e:
            logger.error(f"Currency detection error: {e}")
            import traceback
            traceback.print_exc()
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