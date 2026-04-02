"""
Utility functions for the Universal Assistive Communication System
"""

import os
import re
import uuid
import base64
import socket
from datetime import datetime
import logging
import hashlib
import json

logger = logging.getLogger(__name__)

def validate_text(text, max_length=500):
    """
    Validate and sanitize input text
    
    Args:
        text (str): Input text to validate
        max_length (int): Maximum allowed length
    
    Returns:
        tuple: (is_valid, sanitized_text, error_message)
    """
    if not text:
        return False, None, "Text cannot be empty"
    
    if not isinstance(text, str):
        return False, None, "Text must be a string"
    
    if len(text) > max_length:
        return False, None, f"Text exceeds maximum length of {max_length} characters"
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>{}[\]\\]', '', text)
    sanitized = sanitized.strip()
    
    if not sanitized:
        return False, None, "Text contains no valid characters"
    
    return True, sanitized, None

def generate_unique_id(prefix=''):
    """
    Generate a unique ID
    
    Args:
        prefix (str): Optional prefix for the ID
    
    Returns:
        str: Unique ID
    """
    unique_id = str(uuid.uuid4()).replace('-', '')[:16]
    if prefix:
        return f"{prefix}_{unique_id}"
    return unique_id

def save_base64_image(base64_string, output_dir, filename=None):
    """
    Save a base64 encoded image to file
    
    Args:
        base64_string (str): Base64 encoded image data
        output_dir (str): Directory to save the image
        filename (str): Optional filename
    
    Returns:
        str: Path to saved image file
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract image data
        if ',' in base64_string:
            header, base64_data = base64_string.split(',', 1)
            # Get image type from header if possible
            image_type = header.split(';')[0].split('/')[-1] if '/' in header else 'jpg'
        else:
            base64_data = base64_string
            image_type = 'jpg'
        
        # Decode base64
        image_bytes = base64.b64decode(base64_data)
        
        # Generate filename if not provided
        if not filename:
            filename = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.{image_type}"
        
        # Ensure filename has extension
        if '.' not in filename:
            filename = f"{filename}.{image_type}"
        
        # Save file
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        logger.info(f"Image saved: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Error saving base64 image: {e}")
        return None

def get_local_ip():
    """
    Get the local IP address of the machine
    
    Returns:
        str: Local IP address
    """
    try:
        # Create a socket connection to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # Fallback to localhost
        return "127.0.0.1"

def format_timestamp(timestamp=None, format_str="%Y-%m-%d %H:%M:%S"):
    """
    Format a timestamp
    
    Args:
        timestamp (datetime): Optional timestamp (defaults to now)
        format_str (str): Format string
    
    Returns:
        str: Formatted timestamp
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    return timestamp.strftime(format_str)

def calculate_confidence(score, threshold=0.5):
    """
    Calculate confidence percentage from a score
    
    Args:
        score (float): Raw score (0-1)
        threshold (float): Minimum threshold for valid detection
    
    Returns:
        float: Confidence percentage (0-100)
    """
    if score < threshold:
        return 0.0
    
    # Scale to percentage
    confidence = ((score - threshold) / (1 - threshold)) * 100
    return min(100, max(0, confidence))

def check_emergency_keywords(text, keywords=None):
    """
    Check if text contains emergency keywords
    
    Args:
        text (str): Text to check
        keywords (list): Custom keywords list
    
    Returns:
        dict: Result with keyword matches
    """
    if keywords is None:
        keywords = [
            'help', 'emergency', 'danger', 'fire', 'police', 
            'ambulance', 'accident', 'hurt', 'pain', 'bleeding',
            'sos', 'save', 'rescue', 'thief', 'attack'
        ]
    
    if not text:
        return {'is_emergency': False, 'matches': []}
    
    text_lower = text.lower()
    matches = []
    
    for keyword in keywords:
        if keyword in text_lower:
            matches.append(keyword)
    
    return {
        'is_emergency': len(matches) > 0,
        'matches': matches,
        'severity': 'high' if len(matches) >= 2 else 'medium' if len(matches) == 1 else 'low'
    }

def log_activity(activity_type, user_id, details, log_file='activity.log'):
    """
    Log user activity
    
    Args:
        activity_type (str): Type of activity
        user_id (str): User identifier
        details (dict): Activity details
        log_file (str): Log file path
    """
    try:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': activity_type,
            'user_id': user_id,
            'details': details
        }
        
        # Log to file
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Also log to console
        logger.info(f"ACTIVITY: {activity_type} - User: {user_id}")
        
    except Exception as e:
        logger.error(f"Error logging activity: {e}")

def hash_text(text):
    """
    Create a hash of text (for caching)
    
    Args:
        text (str): Text to hash
    
    Returns:
        str: Hash string
    """
    return hashlib.md5(text.encode()).hexdigest()

def chunk_text(text, max_chunk_size=100):
    """
    Split text into chunks for processing
    
    Args:
        text (str): Text to split
        max_chunk_size (int): Maximum chunk size
    
    Returns:
        list: List of text chunks
    """
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        word_size = len(word) + 1  # +1 for space
        if current_size + word_size > max_chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_size = word_size
        else:
            current_chunk.append(word)
            current_size += word_size
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def get_file_extension(filename):
    """
    Get file extension from filename
    
    Args:
        filename (str): Filename
    
    Returns:
        str: File extension (lowercase)
    """
    if '.' in filename:
        return filename.rsplit('.', 1)[-1].lower()
    return ''

def create_response(success=True, data=None, error=None, status_code=200):
    """
    Create a standardized API response
    
    Args:
        success (bool): Success status
        data (dict): Response data
        error (str): Error message
        status_code (int): HTTP status code
    
    Returns:
        tuple: (response_dict, status_code)
    """
    response = {
        'success': success,
        'timestamp': datetime.now().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    
    if error is not None:
        response['error'] = error
    
    return response, status_code

def safe_float_convert(value, default=0.0):
    """
    Safely convert value to float
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        float: Converted value
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def safe_int_convert(value, default=0):
    """
    Safely convert value to int
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        int: Converted value
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default