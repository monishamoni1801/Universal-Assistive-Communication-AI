// screens/BlindScreen.js (without Slider - using only +/- buttons)
import React, { useState, useEffect, useRef } from 'react';
import { 
    View, 
    Text, 
    StyleSheet, 
    TouchableOpacity, 
    Alert,
    Vibration,
    SafeAreaView,
    StatusBar,
    ActivityIndicator,
    Modal,
    ScrollView,
    Dimensions
} from 'react-native';
import * as Speech from 'expo-speech';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from '@react-navigation/native';

const { height, width } = Dimensions.get('window');

export default function BlindScreen({ navigation }) {
    // Mode state: 'split', 'object', 'currency', or 'text'
    const [mode, setMode] = useState('split');
    
    // Object detection states
    const [objectDetectionActive, setObjectDetectionActive] = useState(false);
    const [objectDetectionResults, setObjectDetectionResults] = useState(null);
    const [isObjectDetecting, setIsObjectDetecting] = useState(false);
    
    // Currency detection states
    const [currencyItems, setCurrencyItems] = useState([]);
    const [totalCurrency, setTotalCurrency] = useState(0);
    const [showCurrencyModal, setShowCurrencyModal] = useState(false);
    const [isCurrencyDetecting, setIsCurrencyDetecting] = useState(false);
    
    // Text reader states
    const [detectedText, setDetectedText] = useState('');
    const [isTextDetecting, setIsTextDetecting] = useState(false);
    const [showTextModal, setShowTextModal] = useState(false);
    const [textScanMode, setTextScanMode] = useState('camera'); // 'camera' or 'gallery'
    
    // Voice control states
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [currentSpeechText, setCurrentSpeechText] = useState('');
    const [shouldStopSpeech, setShouldStopSpeech] = useState(false);
    const [speechRate, setSpeechRate] = useState(1.0); // 👈 Speech speed state (0.5 to 2.0)
    const [showSpeedControl, setShowSpeedControl] = useState(false); // 👈 Show/hide speed panel
    
    // Common states
    const [cameraPermission, requestCameraPermission] = useCameraPermissions();
    const [cameraActive, setCameraActive] = useState(false);
    const [facing, setFacing] = useState('back');
    const [serverStatus, setServerStatus] = useState(null);
    const [isCameraReady, setIsCameraReady] = useState(false);
    
    const cameraRef = useRef(null);
    const detectionInterval = useRef(null);
    const isActive = useRef(false);
    const speechQueue = useRef([]);

    // Server IP
    const SERVER_IP = '192.168.137.32';
    const SERVER_URL = `http://${SERVER_IP}:5000`;

    // Welcome speech
    useFocusEffect(
        React.useCallback(() => {
            console.log("🔵 Screen focused");
            
            testConnection().then((connected) => {
                if (connected) {
                    speakText("Welcome to Blind Assistance Mode. Tap top box for object detection, middle box for currency detection, bottom box for text reading.");
                } else {
                    speakText("Welcome to Blind Assistance Mode. Cannot connect to server.");
                }
            });
            
            return () => {
                console.log("🔵 Screen unfocused - cleaning up");
                stopAllSpeech(); // Stop all speech when leaving screen
                stopAllDetection();
                Speech.stop();
            };
        }, [])
    );

    // Enhanced speak function with adjustable speed
    const speakText = async (text, shouldQueue = false) => {
        if (!text) return;
        
        // Stop any ongoing speech
        await Speech.stop();
        
        setCurrentSpeechText(text);
        setIsSpeaking(true);
        setShouldStopSpeech(false);
        
        try {
            await Speech.speak(text, {
                language: 'en',
                pitch: 1,
                rate: speechRate, // 👈 Use adjustable rate from state
                onDone: () => {
                    if (!shouldStopSpeech) {
                        setIsSpeaking(false);
                        setCurrentSpeechText('');
                        
                        // Check if there's more in queue
                        if (speechQueue.current.length > 0 && !shouldStopSpeech) {
                            const nextText = speechQueue.current.shift();
                            speakText(nextText, false);
                        }
                    }
                },
                onError: () => {
                    setIsSpeaking(false);
                    setCurrentSpeechText('');
                },
                onStopped: () => {
                    // Speech was stopped manually
                    setIsSpeaking(false);
                    setCurrentSpeechText('');
                    speechQueue.current = []; // Clear queue
                }
            });
        } catch (error) {
            console.log('❌ Speech error:', error);
            setIsSpeaking(false);
            setCurrentSpeechText('');
        }
    };

    // Stop all speech immediately
    const stopAllSpeech = async () => {
        console.log("🔴 Stopping all speech");
        setShouldStopSpeech(true);
        await Speech.stop();
        setIsSpeaking(false);
        setCurrentSpeechText('');
        speechQueue.current = [];
    };

    const testConnection = async () => {
        try {
            const response = await fetch(`${SERVER_URL}/api/status`);
            const data = await response.json();
            setServerStatus('✅ Connected');
            console.log('✅ Server connected');
            return true;
        } catch (error) {
            setServerStatus('❌ Failed');
            console.log('❌ Server connection failed');
            return false;
        }
    };

    // ============ OBJECT DETECTION ============
    const detectObjects = async (isManual = false) => {
        if (!cameraRef.current || !isCameraReady) return;
        
        console.log(`🔴 ${isManual ? 'Manual' : 'Auto'} object detection...`);
        setIsObjectDetecting(true);
        
        try {
            const photo = await cameraRef.current.takePictureAsync({
                base64: false,
                quality: 0.8,
            });
            
            const formData = new FormData();
            formData.append('image', {
                uri: photo.uri,
                type: 'image/jpeg',
                name: 'detect.jpg',
            });
            
            const response = await fetch(`${SERVER_URL}/api/object/detect`, {
                method: 'POST',
                body: formData,
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log(`✅ Found ${data.count} objects`);
                setObjectDetectionResults({ 
                    description: data.description, 
                    count: data.count 
                });
                
                if (data.description) {
                    // Stop any ongoing speech before speaking new result
                    await stopAllSpeech();
                    speakText(data.description);
                }
            }
        } catch (error) {
            console.log('❌ Detection error:', error);
        } finally {
            setIsObjectDetecting(false);
        }
    };

    const handleObjectBoxPress = async () => {
        if (!cameraPermission?.granted) {
            const { status } = await requestCameraPermission();
            if (status !== 'granted') {
                speakText("Camera permission required");
                return;
            }
        }
        
        // Stop all speech when switching modes
        await stopAllSpeech();
        
        if (mode === 'object') {
            // If already in object mode, go back to split
            setMode('split');
            setObjectDetectionActive(false);
            setCameraActive(false);
            if (detectionInterval.current) {
                clearInterval(detectionInterval.current);
                detectionInterval.current = null;
            }
            speakText("Split screen mode");
        } else {
            // Switch to object detection mode
            setMode('object');
            setCameraActive(true);
            setObjectDetectionActive(true);
            speakText("Object detection mode");
            
            // Wait for camera then start auto detection
            setTimeout(() => {
                if (isCameraReady) {
                    detectObjects(false); // First detection
                    
                    // Auto detect every 60 seconds
                    detectionInterval.current = setInterval(() => {
                        if (isCameraReady) {
                            detectObjects(false);
                        }
                    }, 60000);
                }
            }, 2000);
        }
    };

    const handleManualObjectDetect = async () => {
        if (cameraActive && isCameraReady) {
            await detectObjects(true);
        }
    };

    // ============ CURRENCY DETECTION ============
    const detectCurrency = async () => {
        if (!cameraRef.current || !isCameraReady) {
            Alert.alert("Error", "Camera not ready");
            return;
        }
        
        setIsCurrencyDetecting(true);
        
        try {
            console.log("📸 Taking picture for currency...");
            const photo = await cameraRef.current.takePictureAsync({
                base64: false,
                quality: 0.9,
            });
            
            const formData = new FormData();
            const filename = photo.uri.split('/').pop() || 'currency.jpg';
            
            formData.append('image', {
                uri: photo.uri,
                type: 'image/jpeg',
                name: filename,
            });
            
            const response = await fetch(`${SERVER_URL}/api/currency/detect`, {
                method: 'POST',
                body: formData,
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            
            const data = await response.json();
            console.log("💰 Currency response:", data);
            
            if (data.success) {
                const newItem = {
                    id: Date.now().toString(),
                    value: data.value,
                    name: getCurrencyName(data.value),
                    timestamp: new Date().toLocaleTimeString()
                };
                
                setCurrencyItems(prev => [...prev, newItem]);
                setTotalCurrency(prev => prev + data.value);
                
                // Stop any ongoing speech before speaking
                await stopAllSpeech();
                speakText(`Detected ${getCurrencyName(data.value)} rupees`);
            } else {
                speakText("Could not detect currency");
                Alert.alert("Detection Failed", "No currency detected. Make sure the note is clearly visible.");
            }
        } catch (error) {
            console.log('❌ Currency error:', error);
            Alert.alert("Error", "Failed to detect currency");
        } finally {
            setIsCurrencyDetecting(false);
        }
    };

    const getCurrencyName = (value) => {
        const names = {
            10: 'Ten',
            20: 'Twenty',
            50: 'Fifty',
            100: 'Hundred',
            200: 'Two Hundred',
            500: 'Five Hundred'
        };
        return names[value] || `${value}`;
    };

    const handleCurrencyBoxPress = async () => {
        if (!cameraPermission?.granted) {
            const { status } = await requestCameraPermission();
            if (status !== 'granted') {
                speakText("Camera permission required");
                return;
            }
        }
        
        // Stop all speech when switching modes
        await stopAllSpeech();
        
        if (mode === 'currency') {
            // If already in currency mode, go back to split
            setMode('split');
            setCameraActive(false);
            setObjectDetectionActive(false);
            if (detectionInterval.current) {
                clearInterval(detectionInterval.current);
                detectionInterval.current = null;
            }
            speakText("Back to the main menu");
        } else {
            // Switch to currency detection mode
            setMode('currency');
            setCameraActive(true);
            setObjectDetectionActive(false);
            if (detectionInterval.current) {
                clearInterval(detectionInterval.current);
                detectionInterval.current = null;
            }
            speakText("Currency detection mode");
        }
    };

    // ============ TEXT READER ============
    const detectText = async (imageUri) => {
        setIsTextDetecting(true);
        
        try {
            console.log("📸 Processing text from:", imageUri);
            
            const formData = new FormData();
            const filename = imageUri.split('/').pop() || 'text.jpg';
            
            formData.append('image', {
                uri: imageUri,
                type: 'image/jpeg',
                name: filename,
            });
            
            const response = await fetch(`${SERVER_URL}/api/text/detect`, {
                method: 'POST',
                body: formData,
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            
            const data = await response.json();
            console.log("📝 Text response:", data);
            
            if (data.success && data.text) {
                setDetectedText(data.text);
                setShowTextModal(true);
                
                // Stop any ongoing speech before speaking new text
                await stopAllSpeech();
                
                // Split long text into smaller chunks for better control
                const sentences = data.text.split(/(?<=[.!?])\s+/);
                if (sentences.length > 1) {
                    // Queue multiple sentences
                    speechQueue.current = sentences.slice(1);
                    speakText(sentences[0], false);
                } else {
                    speakText(data.text);
                }
            } else {
                speakText("No text detected");
                Alert.alert("Info", "No text found in the image");
            }
        } catch (error) {
            console.log('❌ Text detection error:', error);
            Alert.alert("Error", "Failed to detect text");
        } finally {
            setIsTextDetecting(false);
        }
    };

    const scanTextWithCamera = async () => {
        if (!cameraRef.current || !isCameraReady) {
            Alert.alert("Error", "Camera not ready");
            return;
        }
        
        try {
            const photo = await cameraRef.current.takePictureAsync({
                base64: false,
                quality: 0.9,
            });
            
            await detectText(photo.uri);
            
        } catch (error) {
            console.log('❌ Camera error:', error);
            Alert.alert("Error", "Failed to capture image");
        }
    };

    const pickTextFromGallery = async () => {
        try {
            const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
            
            if (!permissionResult.granted) {
                Alert.alert("Permission Required", "Please grant gallery access");
                return;
            }

            const result = await ImagePicker.launchImageLibraryAsync({
                mediaTypes: ['images'],
                base64: false,
                quality: 0.9,
                allowsEditing: false,
            });

            if (!result.canceled && result.assets && result.assets.length > 0) {
                await detectText(result.assets[0].uri);
            }
        } catch (error) {
            console.log('❌ Gallery error:', error);
            Alert.alert("Error", "Failed to pick image");
        }
    };

    const handleTextBoxPress = async () => {
        if (!cameraPermission?.granted) {
            const { status } = await requestCameraPermission();
            if (status !== 'granted') {
                speakText("Camera permission required");
                return;
            }
        }
        
        // Stop all speech when switching modes
        await stopAllSpeech();
        
        if (mode === 'text') {
            // If already in text mode, go back to split
            setMode('split');
            setCameraActive(false);
            setObjectDetectionActive(false);
            if (detectionInterval.current) {
                clearInterval(detectionInterval.current);
                detectionInterval.current = null;
            }
            speakText("Split screen mode");
        } else {
            // Switch to text reader mode
            setMode('text');
            setCameraActive(true);
            setObjectDetectionActive(false);
            if (detectionInterval.current) {
                clearInterval(detectionInterval.current);
                detectionInterval.current = null;
            }
            speakText("Text reader mode");
        }
    };

    const removeCurrencyItem = (id, value) => {
        setCurrencyItems(prev => prev.filter(item => item.id !== id));
        setTotalCurrency(prev => prev - value);
        speakText(`Item removed`);
    };

    const clearAllCurrency = () => {
        setCurrencyItems([]);
        setTotalCurrency(0);
        speakText("All currency items cleared");
    };

    const stopAllDetection = () => {
        setObjectDetectionActive(false);
        setCameraActive(false);
        setObjectDetectionResults(null);
        
        if (detectionInterval.current) {
            clearInterval(detectionInterval.current);
            detectionInterval.current = null;
        }
    };

    const handleEmergency = () => {
        Vibration.vibrate([500, 500, 500]);
        speakText("EMERGENCY MODE ACTIVATED");
        Alert.alert('EMERGENCY', 'Help is on the way');
    };

    const onCameraReady = () => {
        console.log("📷 Camera is ready");
        setIsCameraReady(true);
    };

    const closeTextModal = async () => {
        // Stop all speech when closing modal
        await stopAllSpeech();
        setShowTextModal(false);
    };

    const closeCurrencyModal = async () => {
        setShowCurrencyModal(false);
        if (currencyItems.length > 0) {
            // Stop any ongoing speech before speaking total
            await stopAllSpeech();
            speakText(`Total amount is ${totalCurrency} rupees`);
        }
    };

    const replayText = async () => {
        // Stop current speech and replay
        await stopAllSpeech();
        const sentences = detectedText.split(/(?<=[.!?])\s+/);
        if (sentences.length > 1) {
            speechQueue.current = sentences.slice(1);
            speakText(sentences[0], false);
        } else {
            speakText(detectedText);
        }
    };

    // Speed control functions
    const increaseSpeed = () => {
        setSpeechRate(prev => Math.min(2.0, prev + 0.1));
    };

    const decreaseSpeed = () => {
        setSpeechRate(prev => Math.max(0.5, prev - 0.1));
    };

    return (
        <SafeAreaView style={styles.container}>
            <StatusBar barStyle="light-content" backgroundColor="#1E3A8A" />
            
            {/* Header with Speed Control Button */}
            <View style={styles.header}>
                <View>
                    <Text style={styles.title}>👨‍🦯 VISION ASSIST MODE </Text>
                    {serverStatus && (
                        <Text style={styles.serverStatus}>{serverStatus}</Text>
                    )}
                </View>
                <View style={styles.headerButtons}>
                    <TouchableOpacity 
                        style={styles.speedButton}
                        onPress={() => setShowSpeedControl(!showSpeedControl)}
                    >
                        <Ionicons name="speedometer" size={24} color="#F59E0B" />
                    </TouchableOpacity>
                    <TouchableOpacity onPress={handleEmergency} style={styles.emergencyIcon}>
                        <Ionicons name="warning" size={28} color="#F59E0B" />
                    </TouchableOpacity>
                </View>
            </View>

            {/* Speed Control Panel - Without Slider */}
            {showSpeedControl && (
                <View style={styles.speedControlPanel}>
                    <Text style={styles.speedTitle}>Speech Speed</Text>
                    <View style={styles.speedRow}>
                        <TouchableOpacity onPress={decreaseSpeed} style={styles.speedAdjustButton}>
                            <Text style={styles.speedAdjustText}>−</Text>
                        </TouchableOpacity>
                        <Text style={styles.speedValue}>{speechRate.toFixed(1)}x</Text>
                        <TouchableOpacity onPress={increaseSpeed} style={styles.speedAdjustButton}>
                            <Text style={styles.speedAdjustText}>+</Text>
                        </TouchableOpacity>
                    </View>
                    <View style={styles.speedSteps}>
                        <Text style={styles.speedStepText}>🐢 Slow</Text>
                        <Text style={styles.speedStepText}>🐇 Fast</Text>
                    </View>
                    <Text style={styles.speedHint}>Press + or - to adjust speed</Text>
                </View>
            )}

            {/* Mode Indicator */}
            <View style={styles.modeIndicator}>
                <Text style={styles.modeText}>
                    {mode === 'split' ? '🔀 Split Mode - Tap a box' : 
                     mode === 'object' ? '🔍 Object Detection Mode' : 
                     mode === 'currency' ? '💰 Currency Detection Mode' : 
                     '📝 Text Reader Mode'}
                </Text>
                <Text style={styles.modeHint}>
                    {mode === 'split' ? 'Tap box to enter mode' : 'Tap box again to return to split'}
                </Text>
            </View>

            {/* Voice Status with Stop Button and Speed Indicator */}
            {isSpeaking && (
                <View style={styles.speakingContainer}>
                    <Ionicons name="volume-high" size={20} color="#F59E0B" />
                    <Text style={styles.speakingText} numberOfLines={1}>
                        Speaking: {currentSpeechText.substring(0, 30)}...
                    </Text>
                    <Text style={styles.speedIndicator}>{speechRate.toFixed(1)}x</Text>
                    <TouchableOpacity 
                        style={styles.stopSpeechButton}
                        onPress={stopAllSpeech}
                    >
                        <Text style={styles.stopSpeechText}>STOP</Text>
                    </TouchableOpacity>
                </View>
            )}

            {/* Camera Preview */}
            {cameraActive && cameraPermission?.granted && (
                <View style={[
                    styles.cameraContainer,
                    mode !== 'split' && styles.cameraFullscreen
                ]}>
                    <CameraView 
                        style={styles.camera}
                        facing={facing}
                        ref={cameraRef}
                        ratio="16:9"
                        onCameraReady={onCameraReady}
                    />
                    
                    {/* Flip button */}
                    <TouchableOpacity 
                        style={styles.flipButton}
                        onPress={() => setFacing(facing === 'back' ? 'front' : 'back')}
                    >
                        <Ionicons name="camera-reverse" size={30} color="#FFF8E7" />
                    </TouchableOpacity>
                </View>
            )}

            {/* Content Area - BIG CLICKABLE BOXES */}
            <View style={styles.contentArea}>
                {/* TOP BIG BOX - Object Detection */}
                <TouchableOpacity 
                    style={[
                        styles.bigBox,
                        styles.objectBox,
                        mode === 'object' && styles.activeBox,
                        (mode === 'currency' || mode === 'text') && styles.hiddenBox
                    ]}
                    onPress={handleObjectBoxPress}
                    activeOpacity={0.7}
                >
                    <View style={styles.boxContent}>
                        <Ionicons 
                            name={mode === 'object' ? "eye" : "eye-outline"} 
                            size={mode === 'object' ? 50 : 40} 
                            color={mode === 'object' ? "#FFF8E7" : "#F59E0B"} 
                        />
                        <Text style={[
                            styles.boxTitle,
                            mode === 'object' && styles.activeBoxText
                        ]}>
                            {mode === 'object' ? 'OBJECT DETECTION ACTIVE' : 'OBJECT DETECTION'}
                        </Text>
                        
                        {mode === 'object' && (
                            <>
                                <TouchableOpacity 
                                    style={styles.actionButton}
                                    onPress={handleManualObjectDetect}
                                    disabled={isObjectDetecting}
                                >
                                    {isObjectDetecting ? (
                                        <ActivityIndicator color="#1E3A8A" size="small" />
                                    ) : (
                                        <>
                                            <Ionicons name="camera" size={20} color="#1E3A8A" />
                                            <Text style={styles.actionButtonText}>DETECT NOW</Text>
                                        </>
                                    )}
                                </TouchableOpacity>
                                
                                {objectDetectionResults && (
                                    <View style={styles.resultPreview}>
                                        <Text style={styles.resultPreviewText} numberOfLines={2}>
                                            {objectDetectionResults.description}
                                        </Text>
                                    </View>
                                )}
                            </>
                        )}
                        
                        {mode === 'split' && (
                            <Text style={styles.boxSubtitle}>Tap to enter</Text>
                        )}
                    </View>
                </TouchableOpacity>

                {/* MIDDLE BIG BOX - Currency Detection */}
                <TouchableOpacity 
                    style={[
                        styles.bigBox,
                        styles.currencyBox,
                        mode === 'currency' && styles.activeBox,
                        (mode === 'object' || mode === 'text') && styles.hiddenBox
                    ]}
                    onPress={handleCurrencyBoxPress}
                    activeOpacity={0.7}
                >
                    <View style={styles.boxContent}>
                        <Ionicons 
                            name={mode === 'currency' ? "cash" : "cash-outline"} 
                            size={mode === 'currency' ? 50 : 40} 
                            color={mode === 'currency' ? "#FFF8E7" : "#F59E0B"} 
                        />
                        <Text style={[
                            styles.boxTitle,
                            mode === 'currency' && styles.activeBoxText
                        ]}>
                            {mode === 'currency' ? 'CURRENCY ACTIVE' : 'CURRENCY DETECTION'}
                        </Text>
                        
                        {mode === 'currency' && (
                            <>
                                <TouchableOpacity 
                                    style={styles.actionButton}
                                    onPress={detectCurrency}
                                    disabled={isCurrencyDetecting}
                                >
                                    {isCurrencyDetecting ? (
                                        <ActivityIndicator color="#1E3A8A" size="small" />
                                    ) : (
                                        <>
                                            <Ionicons name="camera" size={20} color="#1E3A8A" />
                                            <Text style={styles.actionButtonText}>SCAN NOTE</Text>
                                        </>
                                    )}
                                </TouchableOpacity>
                                
                                {currencyItems.length > 0 && (
                                    <TouchableOpacity 
                                        style={styles.totalPreview}
                                        onPress={() => setShowCurrencyModal(true)}
                                    >
                                        <Text style={styles.totalPreviewText}>
                                            Total: ₹{totalCurrency}
                                        </Text>
                                    </TouchableOpacity>
                                )}
                            </>
                        )}
                        
                        {mode === 'split' && (
                            <Text style={styles.boxSubtitle}>Tap to enter</Text>
                        )}
                    </View>
                </TouchableOpacity>

                {/* BOTTOM BIG BOX - Text Reader */}
                <TouchableOpacity 
                    style={[
                        styles.bigBox,
                        styles.textBox,
                        mode === 'text' && styles.activeBox,
                        (mode === 'object' || mode === 'currency') && styles.hiddenBox
                    ]}
                    onPress={handleTextBoxPress}
                    activeOpacity={0.7}
                >
                    <View style={styles.boxContent}>
                        <Ionicons 
                            name={mode === 'text' ? "document-text" : "document-text-outline"} 
                            size={mode === 'text' ? 50 : 40} 
                            color={mode === 'text' ? "#FFF8E7" : "#F59E0B"} 
                        />
                        <Text style={[
                            styles.boxTitle,
                            mode === 'text' && styles.activeBoxText
                        ]}>
                            {mode === 'text' ? 'TEXT READER ACTIVE' : 'TEXT READER'}
                        </Text>
                        
                        {mode === 'text' && (
                            <>
                                <View style={styles.textOptionsRow}>
                                    <TouchableOpacity 
                                        style={styles.textOptionButton}
                                        onPress={scanTextWithCamera}
                                        disabled={isTextDetecting}
                                    >
                                        {isTextDetecting ? (
                                            <ActivityIndicator color="#1E3A8A" size="small" />
                                        ) : (
                                            <>
                                                <Ionicons name="camera" size={18} color="#1E3A8A" />
                                                <Text style={styles.textOptionText}>Camera</Text>
                                            </>
                                        )}
                                    </TouchableOpacity>
                                    
                                    <TouchableOpacity 
                                        style={styles.textOptionButton}
                                        onPress={pickTextFromGallery}
                                        disabled={isTextDetecting}
                                    >
                                        <Ionicons name="images" size={18} color="#1E3A8A" />
                                        <Text style={styles.textOptionText}>Gallery</Text>
                                    </TouchableOpacity>
                                </View>
                            </>
                        )}
                        
                        {mode === 'split' && (
                            <Text style={styles.boxSubtitle}>Tap to enter</Text>
                        )}
                    </View>
                </TouchableOpacity>
            </View>

            {/* Navigation Buttons */}
            <View style={styles.navContainer}>
                <TouchableOpacity 
                    style={styles.navButton}
                    onPress={() => {
                        stopAllSpeech();
                        stopAllDetection();
                        navigation.navigate('Normal');
                    }}
                >
                    <Ionicons name="home" size={20} color="#F59E0B" />
                    <Text style={styles.navText}>Home</Text>
                </TouchableOpacity>
                
                <TouchableOpacity 
                    style={styles.navButton}
                    onPress={() => {
                        stopAllSpeech();
                        stopAllDetection();
                        navigation.navigate('Deaf');
                    }}
                >
                    <Ionicons name="ear" size={20} color="#F59E0B" />
                    <Text style={styles.navText}>Deaf</Text>
                </TouchableOpacity>
                
                <TouchableOpacity 
                    style={styles.navButton}
                    onPress={() => {
                        stopAllSpeech();
                        stopAllDetection();
                        navigation.navigate('Mute');
                    }}
                >
                    <Ionicons name="mic-off" size={20} color="#F59E0B" />
                    <Text style={styles.navText}>Mute</Text>
                </TouchableOpacity>
            </View>

            {/* Currency Modal */}
            <Modal visible={showCurrencyModal} transparent animationType="slide">
                <View style={styles.modalOverlay}>
                    <View style={styles.modalContent}>
                        <Text style={styles.modalTitle}>💰 Total Amount</Text>
                        
                        <Text style={styles.modalTotal}>₹{totalCurrency}</Text>
                        
                        <ScrollView style={styles.modalList}>
                            {currencyItems.map((item) => (
                                <View key={item.id} style={styles.modalItem}>
                                    <View>
                                        <Text style={styles.modalItemName}>{item.name} Rupees</Text>
                                        <Text style={styles.modalItemTime}>{item.timestamp}</Text>
                                    </View>
                                    <View style={styles.modalItemActions}>
                                        <Text style={styles.modalItemValue}>₹{item.value}</Text>
                                        <TouchableOpacity 
                                            onPress={() => removeCurrencyItem(item.id, item.value)}
                                            style={styles.modalRemoveButton}
                                        >
                                            <Ionicons name="close-circle" size={24} color="#EF4444" />
                                        </TouchableOpacity>
                                    </View>
                                </View>
                            ))}
                        </ScrollView>
                        
                        <View style={styles.modalActions}>
                            <TouchableOpacity 
                                style={styles.modalClearButton}
                                onPress={clearAllCurrency}
                            >
                                <Text style={styles.modalClearText}>Clear All</Text>
                            </TouchableOpacity>
                            
                            <TouchableOpacity 
                                style={styles.modalCloseButton}
                                onPress={closeCurrencyModal}
                            >
                                <Text style={styles.modalCloseText}>Close</Text>
                            </TouchableOpacity>
                        </View>
                    </View>
                </View>
            </Modal>

            {/* Text Reader Modal */}
            <Modal visible={showTextModal} transparent animationType="slide">
                <View style={styles.modalOverlay}>
                    <View style={styles.modalContent}>
                        <Text style={styles.modalTitle}>📝 Detected Text</Text>
                        
                        {/* Stop Speech Button inside Modal */}
                        {isSpeaking && (
                            <TouchableOpacity 
                                style={styles.modalStopButton}
                                onPress={stopAllSpeech}
                            >
                                <Ionicons name="stop-circle" size={24} color="#FFF8E7" />
                                <Text style={styles.modalStopText}>STOP SPEAKING</Text>
                            </TouchableOpacity>
                        )}
                        
                        {/* Speed control in modal - Without Slider */}
                        <View style={styles.modalSpeedControl}>
                            <Text style={styles.modalSpeedLabel}>Speed: {speechRate.toFixed(1)}x</Text>
                            <View style={styles.modalSpeedRow}>
                                <TouchableOpacity onPress={decreaseSpeed} style={styles.modalSpeedButton}>
                                    <Text style={styles.modalSpeedButtonText}>−</Text>
                                </TouchableOpacity>
                                <Text style={styles.modalSpeedValue}>{speechRate.toFixed(1)}x</Text>
                                <TouchableOpacity onPress={increaseSpeed} style={styles.modalSpeedButton}>
                                    <Text style={styles.modalSpeedButtonText}>+</Text>
                                </TouchableOpacity>
                            </View>
                        </View>
                        
                        <ScrollView style={styles.textModalScroll}>
                            <Text style={styles.detectedText}>{detectedText}</Text>
                        </ScrollView>
                        
                        <View style={styles.modalActions}>
                            <TouchableOpacity 
                                style={styles.modalListenButton}
                                onPress={replayText}
                            >
                                <Ionicons name="volume-high" size={20} color="#FFF8E7" />
                                <Text style={styles.modalListenText}>Listen Again</Text>
                            </TouchableOpacity>
                            
                            <TouchableOpacity 
                                style={styles.modalCloseButton}
                                onPress={closeTextModal}
                            >
                                <Text style={styles.modalCloseText}>Close</Text>
                            </TouchableOpacity>
                        </View>
                    </View>
                </View>
            </Modal>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#1E3A8A',
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingHorizontal: 20,
        paddingVertical: 10,
        backgroundColor: '#1E3A8A',
        borderBottomWidth: 1,
        borderBottomColor: '#F59E0B',
    },
    headerButtons: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 10,
    },
    title: {
        fontSize: 20,
        color: '#FFF8E7',
        fontWeight: 'bold',
    },
    serverStatus: {
        fontSize: 10,
        color: '#F59E0B',
    },
    speedButton: {
        padding: 8,
        backgroundColor: '#FFF8E7',
        borderRadius: 25,
        borderWidth: 1,
        borderColor: '#F59E0B',
    },
    emergencyIcon: {
        padding: 8,
        backgroundColor: '#FFF8E7',
        borderRadius: 25,
        borderWidth: 1,
        borderColor: '#F59E0B',
    },
    speedControlPanel: {
        backgroundColor: '#FFF8E7',
        padding: 15,
        margin: 10,
        borderRadius: 15,
        borderWidth: 2,
        borderColor: '#F59E0B',
    },
    speedTitle: {
        color: '#1E3A8A',
        fontSize: 16,
        fontWeight: 'bold',
        textAlign: 'center',
        marginBottom: 10,
    },
    speedRow: {
        flexDirection: 'row',
        justifyContent: 'center',
        alignItems: 'center',
        gap: 20,
        marginBottom: 10,
    },
    speedAdjustButton: {
        backgroundColor: '#F59E0B',
        width: 50,
        height: 50,
        borderRadius: 25,
        justifyContent: 'center',
        alignItems: 'center',
    },
    speedAdjustText: {
        color: '#1E3A8A',
        fontSize: 28,
        fontWeight: 'bold',
    },
    speedValue: {
        color: '#1E3A8A',
        fontSize: 24,
        fontWeight: 'bold',
        minWidth: 70,
        textAlign: 'center',
    },
    speedSteps: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        paddingHorizontal: 20,
        marginBottom: 5,
    },
    speedStepText: {
        color: '#1E3A8A',
        fontSize: 12,
    },
    speedHint: {
        color: '#666',
        fontSize: 10,
        textAlign: 'center',
    },
    modeIndicator: {
        backgroundColor: '#F59E0B',
        padding: 5,
        alignItems: 'center',
    },
    modeText: {
        color: '#1E3A8A',
        fontSize: 14,
        fontWeight: 'bold',
    },
    modeHint: {
        color: '#1E3A8A',
        fontSize: 10,
        opacity: 0.8,
    },
    speakingContainer: {
        position: 'absolute',
        top: 100,
        left: 10,
        right: 10,
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#FFF8E7',
        paddingHorizontal: 10,
        paddingVertical: 8,
        borderRadius: 20,
        borderWidth: 1,
        borderColor: '#F59E0B',
        zIndex: 1000,
        elevation: 10,
    },
    speakingText: {
        color: '#1E3A8A',
        marginLeft: 5,
        fontSize: 12,
        flex: 1,
    },
    speedIndicator: {
        color: '#F59E0B',
        fontSize: 12,
        fontWeight: 'bold',
        marginHorizontal: 5,
        backgroundColor: '#1E3A8A',
        paddingHorizontal: 8,
        paddingVertical: 2,
        borderRadius: 10,
    },
    stopSpeechButton: {
        backgroundColor: '#EF4444',
        paddingHorizontal: 12,
        paddingVertical: 4,
        borderRadius: 15,
        marginLeft: 5,
    },
    stopSpeechText: {
        color: '#FFF8E7',
        fontSize: 10,
        fontWeight: 'bold',
    },
    cameraContainer: {
        height: height * 0.15,
        backgroundColor: '#000',
        position: 'relative',
    },
    cameraFullscreen: {
        height: height * 0.2,
    },
    camera: {
        flex: 1,
    },
    flipButton: {
        position: 'absolute',
        bottom: 10,
        right: 10,
        backgroundColor: '#1E3A8A',
        padding: 8,
        borderRadius: 25,
        borderWidth: 1,
        borderColor: '#F59E0B',
    },
    contentArea: {
        flex: 1,
        padding: 10,
        gap: 10,
    },
    bigBox: {
        flex: 1,
        borderRadius: 15,
        borderWidth: 2,
        overflow: 'hidden',
        elevation: 3,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.2,
        shadowRadius: 2,
    },
    objectBox: {
        backgroundColor: '#FFF8E7',
        borderColor: '#10B981',
    },
    currencyBox: {
        backgroundColor: '#FFF8E7',
        borderColor: '#F59E0B',
    },
    textBox: {
        backgroundColor: '#FFF8E7',
        borderColor: '#4A90E2',
    },
    activeBox: {
        borderWidth: 4,
        elevation: 8,
    },
    hiddenBox: {
        display: 'none',
    },
    boxContent: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 15,
    },
    boxTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#1E3A8A',
        marginTop: 5,
        textAlign: 'center',
    },
    activeBoxText: {
        color: '#1E3A8A',
        fontSize: 14,
    },
    boxSubtitle: {
        fontSize: 10,
        color: '#666',
        marginTop: 5,
    },
    actionButton: {
        backgroundColor: '#F59E0B',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 12,
        borderRadius: 25,
        marginTop: 10,
        gap: 8,
        width: '70%',
    },
    actionButtonText: {
        color: '#1E3A8A',
        fontSize: 12,
        fontWeight: 'bold',
    },
    textOptionsRow: {
        flexDirection: 'row',
        justifyContent: 'center',
        gap: 10,
        marginTop: 8,
    },
    textOptionButton: {
        backgroundColor: '#F59E0B',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 6,
        borderRadius: 15,
        gap: 3,
        width: '40%',
    },
    textOptionText: {
        color: '#1E3A8A',
        fontSize: 10,
        fontWeight: 'bold',
    },
    resultPreview: {
        backgroundColor: '#1E3A8A',
        padding: 5,
        borderRadius: 8,
        marginTop: 8,
        width: '80%',
    },
    resultPreviewText: {
        color: '#FFF8E7',
        fontSize: 10,
        textAlign: 'center',
    },
    totalPreview: {
        backgroundColor: '#1E3A8A',
        padding: 5,
        borderRadius: 8,
        marginTop: 8,
        width: '60%',
    },
    totalPreviewText: {
        color: '#F59E0B',
        fontSize: 12,
        fontWeight: 'bold',
        textAlign: 'center',
    },
    navContainer: {
        flexDirection: 'row',
        justifyContent: 'space-around',
        paddingHorizontal: 10,
        paddingVertical: 5,
        backgroundColor: '#1E3A8A',
        borderTopWidth: 1,
        borderTopColor: '#F59E0B',
    },
    navButton: {
        backgroundColor: '#FFF8E7',
        paddingVertical: 6,
        paddingHorizontal: 12,
        borderRadius: 20,
        flexDirection: 'row',
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#F59E0B',
    },
    navText: {
        color: '#1E3A8A',
        marginLeft: 3,
        fontSize: 10,
    },
    // Modal Styles
    modalOverlay: {
        flex: 1,
        backgroundColor: 'rgba(0,0,0,0.9)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    modalContent: {
        backgroundColor: '#1E3A8A',
        borderRadius: 20,
        padding: 20,
        width: '80%',
        maxHeight: '70%',
        borderWidth: 2,
        borderColor: '#F59E0B',
    },
    modalTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#F59E0B',
        textAlign: 'center',
        marginBottom: 10,
    },
    modalTotal: {
        fontSize: 32,
        fontWeight: 'bold',
        color: '#FFF8E7',
        textAlign: 'center',
        marginBottom: 15,
    },
    modalList: {
        maxHeight: 200,
        marginBottom: 10,
    },
    modalItem: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: '#FFF8E7',
        padding: 8,
        borderRadius: 6,
        marginBottom: 4,
    },
    modalItemName: {
        color: '#1E3A8A',
        fontSize: 12,
        fontWeight: 'bold',
    },
    modalItemTime: {
        color: '#666',
        fontSize: 8,
    },
    modalItemActions: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 5,
    },
    modalItemValue: {
        color: '#10B981',
        fontSize: 14,
        fontWeight: 'bold',
    },
    modalRemoveButton: {
        padding: 2,
    },
    modalActions: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        gap: 8,
        marginTop: 5,
    },
    modalClearButton: {
        backgroundColor: '#EF4444',
        padding: 8,
        borderRadius: 8,
        flex: 1,
        alignItems: 'center',
    },
    modalClearText: {
        color: '#FFF8E7',
        fontSize: 12,
        fontWeight: 'bold',
    },
    modalCloseButton: {
        backgroundColor: '#10B981',
        padding: 8,
        borderRadius: 8,
        flex: 1,
        alignItems: 'center',
    },
    modalCloseText: {
        color: '#FFF8E7',
        fontSize: 12,
        fontWeight: 'bold',
    },
    modalListenButton: {
        backgroundColor: '#4A90E2',
        padding: 8,
        borderRadius: 8,
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 5,
    },
    modalListenText: {
        color: '#FFF8E7',
        fontSize: 12,
        fontWeight: 'bold',
    },
    modalStopButton: {
        backgroundColor: '#EF4444',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 8,
        borderRadius: 8,
        marginBottom: 10,
        gap: 5,
    },
    modalStopText: {
        color: '#FFF8E7',
        fontSize: 12,
        fontWeight: 'bold',
    },
    modalSpeedControl: {
        marginBottom: 15,
        padding: 10,
        backgroundColor: '#0F3460',
        borderRadius: 10,
    },
    modalSpeedLabel: {
        color: '#F59E0B',
        fontSize: 14,
        fontWeight: 'bold',
        textAlign: 'center',
        marginBottom: 10,
    },
    modalSpeedRow: {
        flexDirection: 'row',
        justifyContent: 'center',
        alignItems: 'center',
        gap: 20,
    },
    modalSpeedButton: {
        backgroundColor: '#F59E0B',
        width: 40,
        height: 40,
        borderRadius: 20,
        justifyContent: 'center',
        alignItems: 'center',
    },
    modalSpeedButtonText: {
        color: '#1E3A8A',
        fontSize: 24,
        fontWeight: 'bold',
    },
    modalSpeedValue: {
        color: '#FFF8E7',
        fontSize: 20,
        fontWeight: 'bold',
        minWidth: 60,
        textAlign: 'center',
    },
    textModalScroll: {
        maxHeight: 300,
        marginBottom: 15,
    },
    detectedText: {
        color: '#FFF8E7',
        fontSize: 16,
        lineHeight: 24,
    },
});