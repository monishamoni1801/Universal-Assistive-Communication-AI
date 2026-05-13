// src/services/api.js
import axios from 'axios';

// ✅ Your NEW IP address
//const BASE_URL = 'http://192.168.0.122:5000';
//const BASE_URL = 'http://192.168.176.157:5000';
//const BASE_URL = 'http://192.168.0.120:5000';
const BASE_URL = 'http://192.168.137.32:5000';


// Create axios instance
const api = axios.create({
    baseURL: BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Speech-to-Text APIs
export const sttAPI = {
    startListening: () => api.post('/api/stt/start'),
    stopListening: () => api.post('/api/stt/stop'),
    getLatestText: () => api.get('/api/stt/latest'),
    listenOnce: () => api.post('/api/stt/listen_once'),
    getHistory: (limit = 10) => api.get(`/api/stt/history?limit=${limit}`),
};

// Text-to-Speech APIs
export const ttsAPI = {
    speak: (text, voiceId = 0, rate = 170, volume = 0.9) => 
        api.post('/api/tts/speak', { text, voice_id: voiceId, rate, volume }, {
            responseType: 'blob'
        }),
    getVoices: () => api.get('/api/tts/voices'),
    saveAudio: (text) => api.post('/api/tts/save', { text }),
};

// Text-to-Sign APIs
export const signAPI = {
    convert: (text) => api.post('/api/sign/convert', { text }),
    getDictionary: () => api.get('/api/sign/dictionary'),
    getImage: (signName) => api.get(`/api/sign/image/${signName}`, { responseType: 'blob' }),
    
    // Sign-to-Text API functions
    startCameraDetection: () => api.post('/api/s2t/start_camera'),
    detectSign: (imageData) => {
        const formData = new FormData();
        formData.append('image', imageData);
        return api.post('/api/s2t/detect', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            timeout: 30000,
        });
    },
    addWordToSentence: () => api.post('/api/s2t/add_word'),
    clearDetection: () => api.post('/api/s2t/clear'),
    speakSentence: () => api.post('/api/s2t/speak'),
};

// Emergency API
export const emergencyAPI = {
    sendAlert: (userId, location, type = 'general') => 
        api.post('/api/emergency', { userId, location, type }),
    getHistory: (userId) => api.get(`/api/emergency/history?user_id=${userId}`),
    resolveAlert: (alertId) => api.post(`/api/emergency/resolve/${alertId}`),
};

// Status API
export const statusAPI = {
    check: () => api.get('/api/status'),
};

export default api;