# Universal-Assistive-Communication-AI

AI-based mobile application enabling communication between blind, deaf, and mute individuals using speech recognition, text-to-speech, and computer vision.

## Overview

Universal-Assistive-Communication-AI is a mobile application designed to **bridge communication gaps** for individuals with hearing, speech, or vision impairments. It leverages AI technologies such as:

- **Speech-to-Text (STT)** for converting spoken words into text.  
- **Text-to-Speech (TTS)** for converting typed or spoken text into audible voice.  
- **Text-to-Sign Language** for translating text into visual sign language.  

The app provides specialized modes for **blind, deaf, and mute users**, enabling independent communication in real-time.

## Features

### 1. Text-to-Speech (TTS)
- Convert typed text into natural voice using AI or device TTS.  
- Multiple voices available via the voice picker.  
- Adjustable pitch and rate for clarity.  

### 2. Speech-to-Text (STT)
- Real-time conversion of spoken words into text.  
- Live captions displayed on screen.  
- Microphone toggle to start/stop listening.  

### 3. Text-to-Sign Language
- Converts text into **visual sign language animations** or images.  
- Supports letters, words/phrases, and spaces.  
- Preview modal with navigation for multiple signs.  
- Scroll through all generated signs horizontally.  

### 4. Quick Access Modes
- **Blind Mode**: Optimized interface for visually impaired users.  
- **Deaf Mode**: Shows text-based messages and captions.  
- **Mute Mode**: Converts typed text into speech and sign language.  

### 5. Additional Features
- Live server connection status indicator.  
- Clear all text and captions with a single button.  
- Audio playback with Expo Audio module.  
- Responsive and accessible UI for all users.  

## Technology Stack

- **Frontend**: React Native, Expo, Expo Audio, Expo Speech, Expo Image Picker  
- **Backend**: Node.js, Express.js  
- **APIs**:
  - `ttsAPI`: Text-to-Speech API  
  - `sttAPI`: Speech-to-Text API  
  - `signAPI`: Text-to-Sign Language API  
  - `emergencyAPI`: Emergency alerts and services  
- **Database**: MongoDB  
- **Libraries**: Axios for HTTP requests, Expo Camera for image capture  

## Usage
Text-to-Speech
Enter text in the input box.
Tap the Text-to-Speech button to hear it aloud.
Speech-to-Text
Tap the Speech-to-Text button to start listening.
Speak clearly; captions appear in real-time.
Tap again to stop listening.
Text-to-Sign Language
Enter text in the input box.
Tap the Text-to-Sign button.
Scroll through sign previews or tap individual signs for full preview.
Quick Modes
Use Blind, Deaf, or Mute buttons to navigate to specialized interfaces.
Voice Picker
Tap the voice icon to select from available AI voices.

## Screenshots
<img width="738" height="1600" alt="image" src="https://github.com/user-attachments/assets/555946e9-9b13-48c0-b8b8-72515e3e3d93" />
<img width="738" height="1600" alt="image" src="https://github.com/user-attachments/assets/a23ee80b-d249-444a-9788-62cec17c23a9" />
<img width="738" height="1600" alt="image" src="https://github.com/user-attachments/assets/ed0113a2-b53d-45f7-967e-d1a82c04d69b" />
<img width="738" height="1600" alt="image" src="https://github.com/user-attachments/assets/29bb23de-56c4-473b-aed3-ccf0acc3e1be" />
<img width="738" height="1600" alt="image" src="https://github.com/user-attachments/assets/05952d6b-a3a4-420f-b378-fc18d7fffe94" />
## Installation

1. Clone the repository:  
```bash
git clone https://github.com/yourusername/Universal-Assistive-Communication-AI.git




