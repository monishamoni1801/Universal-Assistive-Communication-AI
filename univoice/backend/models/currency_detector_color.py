# models/currency_detector_color.py
import cv2
import numpy as np
import os
import re
import logging
import glob

logger = logging.getLogger(__name__)

class CurrencyDetector:
    def __init__(self):
        """Initialize currency detector with color-based detection"""
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.dataset_path = os.path.join(self.base_dir, 'currency_dataset')
        
        # Define color ranges for each denomination (in HSV)
        # These are based on the dominant colors of Indian currency
        self.color_ranges = {
            10: {
                'name': 'Ten',
                'hue_range': (20, 40),      # Brown/Yellow
                'sat_range': (100, 255),
                'val_range': (100, 255),
                'dominant_color': 'brown'
            },
            20: {
                'name': 'Twenty',
                'hue_range': (30, 50),       # Green/Yellow
                'sat_range': (100, 255),
                'val_range': (100, 255),
                'dominant_color': 'green'
            },
            50: {
                'name': 'Fifty',
                'hue_range': (40, 60),       # Violet/Purple
                'sat_range': (100, 255),
                'val_range': (100, 255),
                'dominant_color': 'violet'
            },
            100: {
                'name': 'Hundred',
                'hue_range': (90, 120),      # Blue/Green
                'sat_range': (100, 255),
                'val_range': (100, 255),
                'dominant_color': 'blue'
            },
            200: {
                'name': 'Two Hundred',
                'hue_range': (0, 20),        # Red/Orange
                'sat_range': (100, 255),
                'val_range': (100, 255),
                'dominant_color': 'orange'
            },
            500: {
                'name': 'Five Hundred',
                'hue_range': (140, 170),     # Grey/Blue
                'sat_range': (50, 150),
                'val_range': (100, 255),
                'dominant_color': 'grey'
            }
        }
        
        self.denominations = list(self.color_ranges.keys())
        print("\n" + "="*60)
        print("💰 COLOR-BASED CURRENCY DETECTOR")
        print("="*60)
        print(f"📊 Loaded color profiles for {len(self.denominations)} denominations")
        for d in sorted(self.denominations):
            print(f"  • ₹{d}: {self.color_ranges[d]['dominant_color']}")
        print("="*60 + "\n")
    
    def get_dominant_color(self, img):
        """Extract dominant color from image"""
        # Convert to HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Flatten the image
        hsv_flat = hsv.reshape(-1, 3)
        
        # Remove dark and bright outliers
        mask = (hsv_flat[:, 2] > 50) & (hsv_flat[:, 2] < 200)
        hsv_filtered = hsv_flat[mask]
        
        if len(hsv_filtered) == 0:
            return None
        
        # Calculate histogram of hues
        hist_h = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        
        # Find peak hue
        peak_hue = np.argmax(hist_h)
        
        # Calculate average saturation and value
        avg_sat = np.mean(hsv_filtered[:, 1])
        avg_val = np.mean(hsv_filtered[:, 2])
        
        return {
            'peak_hue': peak_hue,
            'avg_sat': avg_sat,
            'avg_val': avg_val,
            'histogram': hist_h.flatten()
        }
    
    def calculate_color_score(self, img, denomination):
        """Calculate how well image matches denomination's color profile"""
        color_info = self.get_dominant_color(img)
        if color_info is None:
            return 0
        
        profile = self.color_ranges[denomination]
        peak_hue = color_info['peak_hue']
        avg_sat = color_info['avg_sat']
        avg_val = color_info['avg_val']
        
        # Hue score (0-100)
        h_min, h_max = profile['hue_range']
        
        # Handle circular hue (0-180)
        if h_min <= h_max:
            if h_min <= peak_hue <= h_max:
                hue_score = 100
            else:
                # Distance from range
                dist = min(abs(peak_hue - h_min), abs(peak_hue - h_max))
                hue_score = max(0, 100 - dist * 2)
        else:
            # Range wraps around 180 (like red)
            if peak_hue >= h_min or peak_hue <= h_max:
                hue_score = 100
            else:
                dist = min(abs(peak_hue - h_min), abs(peak_hue - h_max))
                hue_score = max(0, 100 - dist * 2)
        
        # Saturation score (0-100)
        sat_min, sat_max = profile['sat_range']
        if sat_min <= avg_sat <= sat_max:
            sat_score = 100
        else:
            sat_score = max(0, 100 - min(abs(avg_sat - sat_min), abs(avg_sat - sat_max)))
        
        # Value score (0-100)
        val_min, val_max = profile['val_range']
        if val_min <= avg_val <= val_max:
            val_score = 100
        else:
            val_score = max(0, 100 - min(abs(avg_val - val_min), abs(avg_val - val_max)))
        
        # Combined score (weighted)
        total_score = (hue_score * 0.6) + (sat_score * 0.2) + (val_score * 0.2)
        
        return total_score
    
    def detect_currency(self, image_path):
        """
        Detect currency based on color
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                return {'success': False, 'error': 'Cannot read image'}
            
            print(f"\n🔍 ANALYZING CURRENCY COLOR...")
            
            # Get color info
            color_info = self.get_dominant_color(img)
            if color_info is None:
                return {'success': False, 'error': 'Cannot analyze colors'}
            
            print(f"  📊 Color analysis:")
            print(f"    • Peak hue: {color_info['peak_hue']}")
            print(f"    • Avg saturation: {color_info['avg_sat']:.1f}")
            print(f"    • Avg value: {color_info['avg_val']:.1f}")
            
            # Calculate scores for each denomination
            scores = {}
            for denom in self.denominations:
                score = self.calculate_color_score(img, denom)
                scores[denom] = score
                print(f"    • ₹{denom}: {score:.1f}% match")
            
            # Find best match
            best_denom = max(scores, key=scores.get)
            best_score = scores[best_denom]
            
            # Need at least 70% match
            if best_score < 70:
                print(f"❌ No confident match (best: {best_score:.1f}%)")
                return {
                    'success': False,
                    'error': 'No confident match',
                    'scores': scores
                }
            
            # Special check for confusing denominations
            if best_denom in [100, 500]:
                # Check if any other denomination has close score
                for denom in [10, 20, 50]:
                    if denom in scores and scores[denom] > best_score * 0.8:
                        print(f"  ⚠️ Confusion between ₹{best_denom} and ₹{denom}")
                        # Use additional check: brightness
                        if color_info['avg_val'] < 100:
                            # Darker notes are usually 500
                            if best_denom == 500:
                                pass
                            else:
                                best_denom = 500
                        break
            
            result = {
                'success': True,
                'value': best_denom,
                'confidence': best_score / 100,
                'denomination': f"₹{best_denom}",
                'color': self.color_ranges[best_denom]['dominant_color'],
                'scores': scores
            }
            
            print(f"\n✅ DETECTED: ₹{best_denom} ({result['color']}) with {best_score:.1f}% confidence")
            return result
            
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