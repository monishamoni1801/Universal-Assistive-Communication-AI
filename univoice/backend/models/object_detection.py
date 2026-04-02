# models/object_detection.py
import cv2
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

# Try to import YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ ultralytics not installed. Run: pip install ultralytics")
    YOLO_AVAILABLE = False

class ObjectDetector:
    def __init__(self):
        """Initialize YOLO object detector"""
        self.model = None
        self.model_loaded = False
        
        # Check if model file exists
        self.model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "yolov8n.pt")
        
        if not YOLO_AVAILABLE:
            logger.error("❌ ultralytics package not installed")
            return
        
        if os.path.exists(self.model_path):
            try:
                logger.info("📥 Loading YOLOv8 model...")
                self.model = YOLO(self.model_path)
                self.model_loaded = True
                logger.info("✅ YOLOv8 model loaded successfully!")
                
                # Class names for YOLO (80 classes)
                self.class_names = [
                    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
                    'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
                    'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
                    'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
                    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
                    'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
                    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake',
                    'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
                    'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
                    'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
                ]
                
            except Exception as e:
                logger.error(f"❌ Error loading YOLO model: {e}")
        else:
            logger.warning(f"⚠️ YOLO model not found at {self.model_path}")
            logger.warning("Download from: https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt")
    
    def detect(self, frame, conf_threshold=0.45):
        """
        Detect objects in frame
        
        Args:
            frame: numpy array image
            conf_threshold: confidence threshold (0-1)
            
        Returns:
            tuple: (processed_frame, detected_objects_list, description)
        """
        if not self.model_loaded:
            # Demo mode - return fake detection
            return self._demo_detection(frame)
        
        try:
            # Run detection
            results = self.model(frame, conf=conf_threshold, verbose=False)[0]
            
            detected_objects = []
            height, width = frame.shape[:2]
            
            # Process results
            for box in results.boxes:
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                
                if class_id < len(self.class_names):
                    class_name = self.class_names[class_id]
                else:
                    class_name = "unknown"
                
                # Get bounding box
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # Ensure coordinates are within frame
                x1 = max(0, min(x1, width))
                y1 = max(0, min(y1, height))
                x2 = max(0, min(x2, width))
                y2 = max(0, min(y2, height))
                
                # Skip if box is too small
                if x2 - x1 < 30 or y2 - y1 < 30:
                    continue
                
                # Calculate position
                center_x = (x1 + x2) // 2
                if center_x < width // 3:
                    position = "left side"
                elif center_x > 2 * width // 3:
                    position = "right side"
                else:
                    position = "center"
                
                # Store detection
                obj = {
                    'name': class_name,
                    'confidence': confidence,
                    'position': position,
                    'box': (x1, y1, x2, y2)
                }
                
                detected_objects.append(obj)
                
                # Draw bounding box
                color = self._get_color(class_name)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                # Draw label
                label = f"{class_name}: {confidence:.0%}"
                cv2.putText(frame, label, (x1, y1-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Create description
            description = self._create_description(detected_objects)
            
            return frame, detected_objects, description
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return frame, [], None
    
    def _demo_detection(self, frame):
        """Demo mode - return fake detections"""
        import random
        
        demo_objects = ['person', 'chair', 'table', 'bottle', 'book', 'laptop']
        
        # Randomly select 0-3 objects
        num_objects = random.randint(0, 3)
        detected_objects = []
        
        height, width = frame.shape[:2]
        
        for i in range(num_objects):
            obj_name = random.choice(demo_objects)
            position = random.choice(['left', 'center', 'right'])
            
            obj = {
                'name': obj_name,
                'confidence': random.uniform(0.6, 0.95),
                'position': position + " side",
                'box': (50 + i*100, 50, 150 + i*100, 150)
            }
            detected_objects.append(obj)
            
            # Draw fake box
            color = self._get_color(obj_name)
            cv2.rectangle(frame, (50 + i*100, 50), (150 + i*100, 150), color, 2)
            cv2.putText(frame, f"{obj_name} (demo)", (50 + i*100, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        description = self._create_description(detected_objects)
        return frame, detected_objects, description
    
    def _get_color(self, class_name):
        """Get color based on object type"""
        colors = {
            'person': (0, 255, 0),      # Green
            'car': (255, 0, 0),         # Blue
            'truck': (255, 0, 0),       # Blue
            'bus': (255, 0, 0),         # Blue
            'dog': (255, 255, 0),       # Cyan
            'cat': (255, 255, 0),       # Cyan
            'bottle': (255, 0, 255),    # Purple
            'cup': (255, 0, 255),       # Purple
            'cell phone': (0, 255, 255), # Yellow
            'laptop': (0, 255, 255),    # Yellow
        }
        return colors.get(class_name, (0, 255, 0))
    
    def _create_description(self, objects):
        """Create natural language description"""
        if not objects:
            return None
        
        # Group objects by type
        object_counts = {}
        object_positions = {}
        
        for obj in objects:
            name = obj['name']
            if name not in object_counts:
                object_counts[name] = 0
                object_positions[name] = obj['position']
            object_counts[name] += 1
        
        # Create descriptions
        descriptions = []
        for name, count in object_counts.items():
            if count == 1:
                pos = object_positions.get(name, '')
                if name == 'person':
                    descriptions.append(f"a person on the {pos}")
                elif name in ['dog', 'cat']:
                    descriptions.append(f"a {name} on the {pos}")
                else:
                    descriptions.append(f"a {name} on the {pos}")
            else:
                descriptions.append(f"{count} {name}s")
        
        if not descriptions:
            return None
        
        # Combine descriptions
        if len(descriptions) == 1:
            return f"I see {descriptions[0]}"
        elif len(descriptions) == 2:
            return f"I see {descriptions[0]} and {descriptions[1]}"
        else:
            return f"I see {', '.join(descriptions[:-1])} and {descriptions[-1]}"
    
    def detect_from_file(self, image_path):
        """Detect objects from image file"""
        try:
            frame = cv2.imread(image_path)
            if frame is None:
                return None, None, None
            return self.detect(frame)
        except Exception as e:
            logger.error(f"Error detecting from file: {e}")
            return None, None, None