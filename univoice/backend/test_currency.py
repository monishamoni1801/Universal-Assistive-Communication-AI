# test_currency.py
from models.currency_detection import CurrencyDetector
import cv2
import os

print("="*60)
print("💰 TESTING CURRENCY DETECTION")
print("="*60)

# Initialize detector
detector = CurrencyDetector()

print(f"\n📊 Loaded denominations: {sorted(detector.denominations)}")
print(f"📊 Total templates: {sum(len(v) for v in detector.templates.values())}")

# Test with each denomination image from dataset
print("\n🔍 Testing detection with dataset images:")
print("-" * 50)

for value in sorted(detector.denominations):
    if detector.templates[value]:
        # Get the first template (which is now a dictionary)
        template_data = detector.templates[value][0]
        
        # Extract the image from the dictionary
        test_img = template_data['image']
        
        # Save temporarily
        temp_path = "test_temp.jpg"
        cv2.imwrite(temp_path, test_img)
        
        # Detect
        result = detector.detect_currency(temp_path, threshold=0.2)
        
        print(f"Testing ₹{value} template → {result.get('denomination', 'Failed')} (confidence: {result.get('confidence', 0):.2f})")
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

print("\n" + "="*60)