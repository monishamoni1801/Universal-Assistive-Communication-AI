# models/currency_detector_cnn.py
import cv2
import numpy as np
import os
import re
import logging
import glob
import pickle
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class CurrencyDetector:
    def __init__(self):
        """Initialize currency detector with ML model"""
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.dataset_path = os.path.join(self.base_dir, 'currency_dataset')
        self.model_path = os.path.join(self.base_dir, 'currency_model.pkl')
        self.scaler_path = os.path.join(self.base_dir, 'currency_scaler.pkl')
        self.denominations = []
        self.model = None
        self.scaler = None
        self.is_trained = False
        
        # Load or train model
        self.load_or_train_model()
        
    def extract_denomination(self, filename):
        match = re.match(r'^(\d+)', filename)
        if match:
            return int(match.group(1))
        return None
    
    def extract_features(self, img):
        """Extract comprehensive features from image"""
        features = []
        
        # Resize to standard size
        img = cv2.resize(img, (200, 100))
        
        # 1. Color histograms (HSV)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        for i in range(3):
            hist = cv2.calcHist([hsv], [i], None, [32], [0, 256])
            hist = cv2.normalize(hist, hist).flatten()
            features.extend(hist)
        
        # 2. Grayscale features
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 3. HOG-like features (simple gradients)
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag, ang = cv2.cartToPolar(gx, gy)
        
        # Divide into regions and compute stats
        h, w = gray.shape
        for i in range(4):
            for j in range(4):
                region = gray[i*h//4:(i+1)*h//4, j*w//4:(j+1)*w//4]
                features.append(np.mean(region))
                features.append(np.std(region))
                
                region_mag = mag[i*h//4:(i+1)*h//4, j*w//4:(j+1)*w//4]
                features.append(np.mean(region_mag))
        
        # 4. Edge features
        edges = cv2.Canny(gray, 50, 150)
        features.append(np.sum(edges > 0) / edges.size)
        
        # 5. Texture features (LBP-like)
        for i in range(4):
            for j in range(4):
                region = gray[i*h//4:(i+1)*h//4, j*w//4:(j+1)*w//4]
                lbp = np.zeros(256)
                for r in range(1, region.shape[0]-1):
                    for c in range(1, region.shape[1]-1):
                        center = region[r, c]
                        code = 0
                        code |= (region[r-1, c-1] > center) << 7
                        code |= (region[r-1, c] > center) << 6
                        code |= (region[r-1, c+1] > center) << 5
                        code |= (region[r, c+1] > center) << 4
                        code |= (region[r+1, c+1] > center) << 3
                        code |= (region[r+1, c] > center) << 2
                        code |= (region[r+1, c-1] > center) << 1
                        code |= (region[r, c-1] > center) << 0
                        lbp[code] += 1
                lbp = lbp / np.sum(lbp)
                features.extend(lbp[::8])  # Subsample to keep size manageable
        
        return np.array(features)
    
    def train_model(self):
        """Train SVM model on dataset"""
        print("\n" + "="*60)
        print("🧠 TRAINING CURRENCY DETECTION MODEL")
        print("="*60)
        
        X = []
        y = []
        
        for img_path in glob.glob(os.path.join(self.dataset_path, '*')):
            if not img_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
            
            filename = os.path.basename(img_path)
            value = self.extract_denomination(filename)
            
            if value is None:
                continue
            
            img = cv2.imread(img_path)
            if img is None:
                continue
            
            # Extract features
            features = self.extract_features(img)
            X.append(features)
            y.append(value)
            
            if value not in self.denominations:
                self.denominations.append(value)
            
            print(f"  📊 Processed: ₹{value} - {filename}")
        
        if len(X) == 0:
            print("❌ No training data found")
            return False
        
        X = np.array(X)
        y = np.array(y)
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train SVM
        self.model = SVC(kernel='rbf', C=10, gamma='scale', probability=True)
        self.model.fit(X_scaled, y)
        
        # Save model
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        with open(self.scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        # Test accuracy
        train_pred = self.model.predict(X_scaled)
        accuracy = np.mean(train_pred == y)
        
        print("\n" + "="*60)
        print(f"✅ Model trained successfully!")
        print(f"📊 Training accuracy: {accuracy:.2%}")
        print(f"💰 Denominations: {sorted(self.denominations)}")
        print("="*60 + "\n")
        
        self.is_trained = True
        return True
    
    def load_or_train_model(self):
        """Load existing model or train new one"""
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                self.denominations = sorted(set(self.model.classes_))
                self.is_trained = True
                print(f"✅ Loaded existing model with {len(self.denominations)} denominations")
                return
            except:
                print("⚠️ Failed to load model, training new one...")
        
        self.train_model()
    
    def detect_currency(self, image_path):
        """Detect currency using trained model"""
        try:
            if not self.is_trained:
                return {'success': False, 'error': 'Model not trained'}
            
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                return {'success': False, 'error': 'Cannot read image'}
            
            print(f"\n🔍 Analyzing currency with ML model...")
            
            # Extract features
            features = self.extract_features(img)
            features_scaled = self.scaler.transform([features])
            
            # Get prediction and probabilities
            pred = self.model.predict(features_scaled)[0]
            proba = self.model.predict_proba(features_scaled)[0]
            
            # Get confidence
            confidence = max(proba)
            pred_index = list(self.model.classes_).index(pred)
            
            # Get top 3 predictions
            top_indices = np.argsort(proba)[-3:][::-1]
            top_predictions = {
                self.model.classes_[i]: float(proba[i]) 
                for i in top_indices if proba[i] > 0.1
            }
            
            print(f"  📊 Top predictions:")
            for val, prob in top_predictions.items():
                print(f"    • ₹{val}: {prob:.2%} confidence")
            
            # Only accept if confidence is high enough
            if confidence < 0.6:
                print(f"❌ Low confidence ({confidence:.2%})")
                return {
                    'success': False,
                    'error': 'Low confidence',
                    'predictions': top_predictions
                }
            
            # Special handling for 100/500
            if pred in [100, 500] and confidence < 0.7:
                # Check if any smaller denomination has close probability
                for val in [10, 20, 50]:
                    if val in top_predictions and top_predictions[val] > confidence * 0.8:
                        print(f"  ⚠️ Possible misdetection, using ₹{val} instead")
                        pred = val
                        confidence = top_predictions[val]
                        break
            
            result = {
                'success': True,
                'value': pred,
                'confidence': float(confidence),
                'denomination': f"₹{pred}",
                'predictions': top_predictions
            }
            
            print(f"\n✅ DETECTED: {result['denomination']} (confidence: {confidence:.2%})")
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