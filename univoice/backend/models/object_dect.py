"""
YOLOv8 Object Detection - Accurate detection of many objects
Detects 80+ common objects with high accuracy
"""

import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
import threading
import time
import pyttsx3
import os
import sys

# Install ultralytics if not present
try:
    from ultralytics import YOLO
except ImportError:
    print("Installing ultralytics...")
    os.system("pip install ultralytics")
    from ultralytics import YOLO

class YOLODetector:
    def __init__(self):
        print("\n" + "="*60)
        print("YOLOv8 OBJECT DETECTION SYSTEM")
        print("="*60)
        
        # Initialize speech
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 160)
        self.engine.setProperty('volume', 1.0)
        
        # Load YOLO model (nano version - fast and accurate)
        print("📥 Loading YOLOv8 model...")
        self.model = YOLO('yolov8n.pt')  # Nano model - smallest and fastest
        print("✅ Model loaded successfully!")
        
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
        
        # Common objects that people want to detect
        self.common_objects = [
            'person', 'car', 'truck', 'bus', 'dog', 'cat', 'bottle', 'cup', 
            'cell phone', 'laptop', 'tv', 'book', 'chair', 'table', 'bed',
            'bicycle', 'motorcycle', 'bird', 'backpack', 'handbag', 'suitcase'
        ]
        
        # Detection settings
        self.confidence_threshold = 0.45
        self.last_spoken = {}
        self.speak_cooldown = 3
        self.last_spoken_time = time.time()
        
        print(f"📊 Model can detect {len(self.class_names)} different objects")
        print("✅ Common objects: person, car, dog, cat, bottle, phone, laptop, etc.")
        
    def detect(self, frame):
        """Detect objects using YOLOv8"""
        # Run detection
        results = self.model(frame, conf=self.confidence_threshold, verbose=False)[0]
        
        detected_objects = []
        height, width = frame.shape[:2]
        
        # Process results
        for box in results.boxes:
            # Get detection info
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = self.class_names[class_id]
            
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
                position = "on the left"
            elif center_x > 2 * width // 3:
                position = "on the right"
            else:
                position = "in the center"
            
            # Calculate distance based on box size
            box_width = x2 - x1
            if box_width > width // 2:
                distance = "very close"
            elif box_width > width // 4:
                distance = "nearby"
            else:
                distance = "in the distance"
            
            # Store detection
            obj = {
                'name': class_name,
                'confidence': confidence,
                'position': position,
                'distance': distance,
                'box': (x1, y1, x2, y2)
            }
            
            detected_objects.append(obj)
            
            # Draw bounding box with color based on object type
            color = self.get_object_color(class_name)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
            
            # Draw label with background
            label = f"{class_name}: {confidence:.0%}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            
            # Draw background for text
            cv2.rectangle(frame, (x1, y1-30), (x1+label_size[0], y1), color, -1)
            
            # Draw text
            cv2.putText(frame, label, (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame, detected_objects
    
    def get_object_color(self, class_name):
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
            'tv': (0, 255, 255),        # Yellow
            'book': (128, 0, 128),      # Purple
            'chair': (128, 0, 128),     # Purple
            'bird': (255, 165, 0),      # Orange
        }
        return colors.get(class_name, (0, 255, 0))
    
    def get_description(self, objects):
        """Create natural language description"""
        if not objects:
            return None
        
        current_time = time.time()
        
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
                    descriptions.append(f"a person {pos}")
                elif name in ['dog', 'cat']:
                    descriptions.append(f"a {name} {pos}")
                else:
                    descriptions.append(f"a {name} {pos}")
            else:
                descriptions.append(f"{count} {name}s")
        
        if not descriptions:
            return None
        
        # Combine descriptions
        if len(descriptions) == 1:
            text = f"I see {descriptions[0]}"
        elif len(descriptions) == 2:
            text = f"I see {descriptions[0]} and {descriptions[1]}"
        else:
            text = f"I see {', '.join(descriptions[:-1])} and {descriptions[-1]}"
        
        # Check cooldown
        if text in self.last_spoken:
            if current_time - self.last_spoken[text] < self.speak_cooldown:
                return None
        
        self.last_spoken[text] = current_time
        return text
    
    def speak(self, text):
        """Speak text in background"""
        def _speak():
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"Speech error: {e}")
        
        thread = threading.Thread(target=_speak)
        thread.daemon = True
        thread.start()


class DetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLOv8 Object Detector")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a1a')
        
        # Initialize detector
        self.detector = YOLODetector()
        
        # Camera
        self.cap = None
        self.running = False
        
        # Statistics
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        
        # Setup UI
        self.setup_ui()
        
        # Start camera
        self.root.after(1000, self.start_camera)
    
    def setup_ui(self):
        # Title
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title = tk.Label(title_frame, text="🎯 YOLOv8 OBJECT DETECTION", 
                        font=("Arial", 20, "bold"), fg="white", bg='#2c3e50')
        title.pack(expand=True)
        
        # Main content
        main = tk.Frame(self.root, bg='#1a1a1a')
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left - Video
        left = tk.Frame(main, bg='black', relief=tk.RAISED, bd=2)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.video_label = tk.Label(left, bg='black')
        self.video_label.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # Right - Info panel
        right = tk.Frame(main, bg='#34495e', width=350)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10,0))
        right.pack_propagate(False)
        
        # Status
        status_frame = tk.Frame(right, bg='#34495e')
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.status_label = tk.Label(status_frame, text="⚫ Initializing...", 
                                     font=("Arial", 14, "bold"), 
                                     fg='yellow', bg='#34495e')
        self.status_label.pack()
        
        self.fps_label = tk.Label(status_frame, text="FPS: 0", 
                                  font=("Arial", 10), 
                                  fg='gray', bg='#34495e')
        self.fps_label.pack()
        
        # Current detection (large)
        current_frame = tk.Frame(right, bg='#34495e')
        current_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(current_frame, text="🔊 CURRENT DETECTION", 
                font=("Arial", 12, "bold"), fg='#3498db', bg='#34495e').pack()
        
        self.current_label = tk.Label(current_frame, text="Nothing detected", 
                                      font=("Arial", 16, "bold"), 
                                      fg='#2ecc71', bg='#34495e', wraplength=300)
        self.current_label.pack(pady=10)
        
        # Object list
        list_frame = tk.Frame(right, bg='#34495e')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(list_frame, text="📋 DETECTED OBJECTS", 
                font=("Arial", 12, "bold"), fg='#e74c3c', bg='#34495e').pack()
        
        self.list_text = tk.Text(list_frame, height=12, 
                                  font=("Arial", 11), 
                                  bg='#2c3e50', fg='white',
                                  wrap=tk.WORD)
        self.list_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Last spoken
        spoken_frame = tk.Frame(right, bg='#34495e')
        spoken_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(spoken_frame, text="🗣️ LAST SPOKEN", 
                font=("Arial", 10, "bold"), fg='#f39c12', bg='#34495e').pack()
        
        self.spoken_label = tk.Label(spoken_frame, text="None", 
                                      font=("Arial", 11), 
                                      fg='white', bg='#34495e', wraplength=300)
        self.spoken_label.pack(pady=5)
        
        # Instructions
        instr = tk.Label(right, 
                        text="System detects 80+ objects\nSpeaks every 3 seconds",
                        font=("Arial", 10), fg='gray', bg='#34495e')
        instr.pack(pady=5)
    
    def start_camera(self):
        """Start camera with best backend"""
        backends = [
            (cv2.CAP_DSHOW, "DirectShow"),
            (cv2.CAP_MSMF, "Media Foundation"),
            (0, "Default")
        ]
        
        for backend, name in backends:
            try:
                if backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF]:
                    self.cap = cv2.VideoCapture(0, backend)
                else:
                    self.cap = cv2.VideoCapture(0)
                
                if self.cap and self.cap.isOpened():
                    # Set resolution
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    
                    # Test read
                    ret, test = self.cap.read()
                    if ret:
                        print(f"✅ Camera started with {name}")
                        break
                    else:
                        self.cap.release()
            except:
                continue
        
        if not self.cap or not self.cap.isOpened():
            self.status_label.config(text="❌ Cannot open camera", fg='red')
            return
        
        self.running = True
        self.status_label.config(text="🟢 DETECTING OBJECTS...", fg='lime')
        
        # Start detection thread
        self.thread = threading.Thread(target=self.detection_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def detection_loop(self):
        """Main detection loop"""
        last_speak_time = time.time()
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            # Flip horizontally
            frame = cv2.flip(frame, 1)
            
            # Detect objects
            processed_frame, objects = self.detector.detect(frame)
            
            # Update FPS
            self.frame_count += 1
            if time.time() - self.last_fps_time >= 1:
                self.fps = self.frame_count
                self.frame_count = 0
                self.last_fps_time = time.time()
            
            # Get description
            description = self.detector.get_description(objects)
            
            # Speak periodically
            current_time = time.time()
            if description and (current_time - last_speak_time) >= 3:
                self.detector.speak(description)
                last_speak_time = current_time
                self.root.after(0, self.update_spoken, description)
            
            # Update UI
            self.root.after(0, self.update_display, processed_frame, objects)
            
            time.sleep(0.03)  # ~30 FPS
    
    def update_display(self, frame, objects):
        """Update GUI display"""
        # Update video
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = img.resize((800, 550))
        imgtk = ImageTk.PhotoImage(image=img)
        
        self.video_label.imgtk = imgtk
        self.video_label.config(image=imgtk)
        
        # Update FPS
        self.fps_label.config(text=f"FPS: {self.fps}")
        
        # Update object list
        self.list_text.delete(1.0, tk.END)
        
        if objects:
            # Group objects by type
            object_counts = {}
            for obj in objects:
                name = obj['name']
                if name not in object_counts:
                    object_counts[name] = 0
                object_counts[name] += 1
            
            # Display with details
            for name, count in object_counts.items():
                # Get first object of this type for position
                first_obj = next(obj for obj in objects if obj['name'] == name)
                position = first_obj['position']
                confidence = first_obj['confidence']
                
                line = f"• {count}x {name}"
                if count == 1:
                    line += f" {position}"
                line += f" ({confidence:.0%})\n"
                
                self.list_text.insert(tk.END, line)
            
            # Update current detection (most confident)
            most_confident = max(objects, key=lambda x: x['confidence'])
            self.current_label.config(text=f"{most_confident['name']} {most_confident['position']}")
        else:
            self.list_text.insert(tk.END, "No objects detected")
            self.current_label.config(text="Nothing detected")
    
    def update_spoken(self, description):
        """Update last spoken label"""
        self.spoken_label.config(text=description)


def main():
    print("\n" + "="*60)
    print("YOLOv8 OBJECT DETECTION SYSTEM")
    print("="*60)
    print("\n📌 This will download YOLOv8 model on first run (~6MB)")
    print("📌 Detects 80+ objects with high accuracy")
    print("📌 System speaks detected objects every 3 seconds\n")
    
    root = tk.Tk()
    app = DetectionApp(root)
    
    def on_closing():
        app.running = False
        if app.cap:
            app.cap.release()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()