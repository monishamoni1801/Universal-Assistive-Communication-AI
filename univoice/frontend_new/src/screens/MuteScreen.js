// src/screens/MuteScreen.js (without Slider - using only +/- buttons)
import React, { useState, useRef, useEffect } from 'react';
import { 
    View, 
    Text, 
    StyleSheet, 
    TouchableOpacity, 
    TextInput, 
    Alert,
    ScrollView,
    ActivityIndicator,
    Vibration,
    Modal,
    SafeAreaView,
    FlatList,
    Image,
    Dimensions,
    Keyboard,
    TouchableWithoutFeedback
} from 'react-native';
import { Audio } from 'expo-av';
import * as Speech from 'expo-speech';
import { Ionicons } from '@expo/vector-icons';
import { ttsAPI, signAPI, emergencyAPI } from '../services/api';

const { width } = Dimensions.get('window');

export default function MuteScreen() {
    // ========== STATE VARIABLES ==========
    // Text input state
    const [text, setText] = useState('');
    const [isKeyboardVisible, setKeyboardVisible] = useState(false);
    
    // TTS states
    const [isLoading, setIsLoading] = useState(false);
    const [speechRate, setSpeechRate] = useState(0.9); // Speech speed (0.5 to 1.5)
    const [showSpeedControl, setShowSpeedControl] = useState(false);
    
    // Buzzer states
    const [isBuzzerActive, setIsBuzzerActive] = useState(false);
    
    // Harassment sound state
    const [isHarassmentActive, setIsHarassmentActive] = useState(false);
    
    // Sign language states (Text-to-Sign)
    const [signResult, setSignResult] = useState(null);
    const [signDictionary, setSignDictionary] = useState([]);
    const [signLoading, setSignLoading] = useState(false);
    
    // Image preview modal states
    const [previewVisible, setPreviewVisible] = useState(false);
    const [selectedSign, setSelectedSign] = useState(null);
    const [selectedIndex, setSelectedIndex] = useState(0);
    
    // Auto Sentence Generator states
    const [showSentenceGenerator, setShowSentenceGenerator] = useState(false);
    const [selectedCategory, setSelectedCategory] = useState('Basic');
    const [sentenceCategories, setSentenceCategories] = useState({});
    const [loadingSentences, setLoadingSentences] = useState(false);
    
    // Server IP
    const SERVER_IP = '192.168.0.120';
    const SERVER_URL = `http://${SERVER_IP}:5000`;
    
    // Refs
    const sound = useRef(null);
    const buzzerSound = useRef(null);
    const harassmentSound = useRef(null);
    const scrollViewRef = useRef(null);
    const textInputRef = useRef(null);

    // ========== INITIALIZATION ==========
    useEffect(() => {
        loadSignDictionary();
        fetchSentences();
        
        // Keyboard event listeners
        const keyboardDidShowListener = Keyboard.addListener(
            'keyboardDidShow',
            () => {
                setKeyboardVisible(true);
                setTimeout(() => {
                    if (scrollViewRef.current) {
                        scrollViewRef.current.scrollToEnd({ animated: true });
                    }
                }, 100);
            }
        );
        const keyboardDidHideListener = Keyboard.addListener(
            'keyboardDidHide',
            () => {
                setKeyboardVisible(false);
            }
        );
        
        return () => {
            if (buzzerSound.current) {
                buzzerSound.current.unloadAsync();
            }
            if (harassmentSound.current) {
                harassmentSound.current.unloadAsync();
            }
            keyboardDidShowListener.remove();
            keyboardDidHideListener.remove();
        };
    }, []);

    const loadSignDictionary = async () => {
        try {
            const response = await signAPI.getDictionary();
            setSignDictionary(response.data.dictionary || []);
        } catch (error) {
            console.log('Error loading dictionary:', error);
        }
    };

    const fetchSentences = async () => {
        setLoadingSentences(true);
        try {
            const response = await fetch(`${SERVER_URL}/api/sentences`);
            const data = await response.json();
            if (data.success) {
                setSentenceCategories(data.sentences);
                if (data.categories && data.categories.length > 0) {
                    setSelectedCategory(data.categories[0]);
                }
            } else {
                // Fallback to hardcoded sentences if API fails
                setSentenceCategories(fallbackSentences);
            }
        } catch (error) {
            console.log('Error fetching sentences:', error);
            // Fallback to hardcoded sentences
            setSentenceCategories(fallbackSentences);
        } finally {
            setLoadingSentences(false);
        }
    };

    // Fallback sentences in case API fails
    const fallbackSentences = {
        "Basic": [
            "Hello",
            "How are you?",
            "Good morning",
            "Good afternoon",
            "Good evening",
            "Good night",
            "Thank you",
            "You're welcome",
            "Sorry",
            "Excuse me",
            "Please wait",
            "One minute please"
        ],
        "Needs": [
            "I need help",
            "Please help me",
            "Call someone",
            "Call my family",
            "Call a doctor",
            "Please stay with me",
            "I feel uncomfortable",
            "I am not feeling well",
            "I need assistance"
        ],
        "Food": [
            "I am hungry",
            "I want food",
            "I want water",
            "Please give me water",
            "Please give me food",
            "I want tea",
            "I want coffee",
            "I want juice",
            "I finished eating",
            "I don't want food"
        ],
        "Health": [
            "I feel sick",
            "I have a headache",
            "I have stomach pain",
            "I feel dizzy",
            "I need medicine",
            "Take me to the hospital",
            "Call an ambulance"
        ],
        "Daily": [
            "Yes",
            "No",
            "Maybe",
            "I agree",
            "I don't agree",
            "That is correct",
            "That is wrong",
            "Please repeat",
            "I didn't understand"
        ],
        "Location": [
            "I want to go home",
            "Take me home",
            "I want to go outside",
            "Where is the bathroom?",
            "Where is the hospital?",
            "Where is the bus stop?",
            "I want to sit",
            "I want to stand"
        ],
        "School": [
            "I completed my work",
            "I need more time",
            "Please explain again",
            "I understand",
            "I don't understand",
            "I will do it"
        ],
        "Emergency": [
            "Emergency",
            "Call the police",
            "Call an ambulance",
            "There is danger",
            "Please help immediately"
        ],
        "Emotions": [
            "I am happy",
            "I am sad",
            "I am angry",
            "I am scared",
            "I am tired",
            "I am excited"
        ]
    };

    // ========== TEXT TO SPEECH FUNCTIONS ==========
    const speakText = async (customText = null) => {
        const textToSpeak = customText || text;
        if (!textToSpeak.trim()) {
            Alert.alert('Error', 'Please enter some text');
            return;
        }

        setIsLoading(true);
        try {
            await Speech.speak(textToSpeak, {
                language: 'en',
                pitch: 1,
                rate: speechRate, // Use the slider value
            });
        } catch (error) {
            Alert.alert('Error', 'Could not play audio');
        } finally {
            setIsLoading(false);
        }
    };

    // Speed control functions
    const increaseSpeed = () => {
        setSpeechRate(prev => Math.min(1.5, prev + 0.1));
    };

    const decreaseSpeed = () => {
        setSpeechRate(prev => Math.max(0.5, prev - 0.1));
    };

    // ========== TEXT TO SIGN FUNCTIONS ==========
    const convertToSign = async () => {
        if (!text.trim()) {
            Alert.alert('Error', 'Please enter some text');
            return;
        }

        setSignLoading(true);
        try {
            console.log("Converting to sign:", text);
            const response = await signAPI.convert(text);
            console.log("Sign response:", JSON.stringify(response.data, null, 2));
            
            if (response.data.success) {
                setSignResult(response.data.result);
                Alert.alert('Success', `Converted to ${response.data.result.type} sign language`);
            } else {
                Alert.alert('Error', response.data.error || 'Conversion failed');
            }
        } catch (error) {
            console.error('Sign conversion error:', error);
            Alert.alert('Error', 'Failed to convert to sign language: ' + error.message);
        } finally {
            setSignLoading(false);
        }
    };

    // Handle sign press for preview
    const handleSignPress = (sign, index) => {
        setSelectedSign(sign);
        setSelectedIndex(index);
        setPreviewVisible(true);
    };

    // Navigate to previous sign
    const goToPrevious = () => {
        if (signResult && selectedIndex > 0) {
            const newIndex = selectedIndex - 1;
            setSelectedIndex(newIndex);
            setSelectedSign(signResult.signs[newIndex]);
        }
    };

    // Navigate to next sign
    const goToNext = () => {
        if (signResult && selectedIndex < signResult.signs.length - 1) {
            const newIndex = selectedIndex + 1;
            setSelectedIndex(newIndex);
            setSelectedSign(signResult.signs[newIndex]);
        }
    };

    // Render sign item for Text-to-Sign with press handler
    const renderSign = (sign, index) => {
        const baseUrl = SERVER_URL;
        
        return (
            <TouchableOpacity 
                key={index} 
                style={styles.signBox}
                onPress={() => handleSignPress(sign, index)}
                activeOpacity={0.7}
            >
                {sign.type === 'gif' && (
                    <>
                        <Text style={styles.signLabel}>{sign.phrase}</Text>
                        {sign.data ? (
                            <Image 
                                source={{ uri: `data:image/gif;base64,${sign.data}` }}
                                style={styles.signImage}
                                resizeMode="contain"
                            />
                        ) : sign.url ? (
                            <Image 
                                source={{ uri: `${baseUrl}${sign.url}` }}
                                style={styles.signImage}
                                resizeMode="contain"
                            />
                        ) : (
                            <Text style={styles.signChar}>🎬</Text>
                        )}
                    </>
                )}
                
                {sign.type === 'letter' && (
                    <>
                        <Text style={styles.signChar}>{sign.character?.toUpperCase() || '?'}</Text>
                        {sign.data ? (
                            <Image 
                                source={{ uri: `data:image/jpg;base64,${sign.data}` }}
                                style={styles.signImage}
                                resizeMode="contain"
                            />
                        ) : sign.url ? (
                            <Image 
                                source={{ uri: `${baseUrl}${sign.url}` }}
                                style={styles.signImage}
                                resizeMode="contain"
                            />
                        ) : null}
                        <Text style={styles.signLabel}>Letter</Text>
                    </>
                )}
                
                {sign.type === 'space' && (
                    <>
                        <Text style={styles.spaceText}>␣</Text>
                        <Text style={styles.signLabel}>SPACE</Text>
                    </>
                )}
                
                {sign.type !== 'gif' && sign.type !== 'letter' && sign.type !== 'space' && (
                    <>
                        <Text style={styles.signChar}>❓</Text>
                    </>
                )}
            </TouchableOpacity>
        );
    };

    // ========== AUTO SENTENCE GENERATOR FUNCTIONS ==========
    const selectSentence = (sentence) => {
        setText(sentence);
        setShowSentenceGenerator(false);
        speakText(sentence);
    };

    const selectCategory = (category) => {
        setSelectedCategory(category);
    };

    // Dismiss keyboard
    const dismissKeyboard = () => {
        Keyboard.dismiss();
    };

    // ========== BUZZER FUNCTIONS ==========
    const playBuzzer = async () => {
        try {
            if (isBuzzerActive) {
                if (buzzerSound.current) {
                    await buzzerSound.current.stopAsync();
                    await buzzerSound.current.unloadAsync();
                    buzzerSound.current = null;
                }
                setIsBuzzerActive(false);
                Vibration.cancel();
            } else {
                const { sound: newSound } = await Audio.Sound.createAsync(
                    { uri: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3' },
                    { shouldPlay: true, isLooping: true }
                );
                
                buzzerSound.current = newSound;
                setIsBuzzerActive(true);
                Vibration.vibrate([500, 200, 500, 200, 500], true);
            }
        } catch (error) {
            console.error('Buzzer error:', error);
        }
    };

    const stopBuzzer = async () => {
        if (buzzerSound.current) {
            await buzzerSound.current.stopAsync();
            await buzzerSound.current.unloadAsync();
            buzzerSound.current = null;
        }
        setIsBuzzerActive(false);
        Vibration.cancel();
    };

    // Harassment sound toggle
    const toggleHarassmentSound = async () => {
        try {
            if (isHarassmentActive) {
                if (harassmentSound.current) {
                    await harassmentSound.current.stopAsync();
                    await harassmentSound.current.unloadAsync();
                    harassmentSound.current = null;
                }
                setIsHarassmentActive(false);
                Vibration.cancel();
                Alert.alert('Stopped', 'Harassment alert stopped');
            } else {
                const { sound: newSound } = await Audio.Sound.createAsync(
                    { uri: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3' },
                    { shouldPlay: true, isLooping: true, volume: 1.0 }
                );
                
                harassmentSound.current = newSound;
                setIsHarassmentActive(true);
                Vibration.vibrate([300, 200, 300, 200, 300, 200, 300], true);
                speakText("Help! I am being harassed. Please call security.");
            }
        } catch (error) {
            console.error('Harassment sound error:', error);
        }
    };

    const sendEmergency = async (type) => {
        try {
            await emergencyAPI.sendAlert('user123', { lat: 0, lng: 0 }, type);
            Alert.alert('Emergency', `${type} alert sent`);
        } catch (error) {
            Alert.alert('Error', 'Failed to send alert');
        }
    };

    // Enhanced emergency functions with speech
    const handleBusStop = () => {
        const message = "My stop has arrived. Please stop the bus.";
        speakText(message);
        Vibration.vibrate(200);
    };

    const handleMovePlease = () => {
        const message = "Move please, I need to get through.";
        speakText(message);
        Vibration.vibrate(200);
    };

    const handleEmergency = () => {
        const message = "Emergency! I need help immediately.";
        speakText(message);
        Vibration.vibrate([500, 500, 500, 500, 500]);
    };

    const handleWater = () => {
        const message = "Can I have some water, please?";
        speakText(message);
    };

    const handleFood = () => {
        const message = "Can I have some food, please?";
        speakText(message);
    };

    const handleYes = () => {
        const message = "Yes";
        speakText(message);
    };

    const handleNo = () => {
        const message = "No";
        speakText(message);
    };

    const handleThankYou = () => {
        const message = "Thank you very much";
        speakText(message);
    };

    const handleHelp = () => {
        const message = "Help me, please";
        speakText(message);
    };

    const handleBathroom = () => {
        const message = "Where is the bathroom?";
        speakText(message);
    };

    const handleDoctor = () => {
        const message = "I need to see a doctor";
        speakText(message);
    };

    const handlePolice = () => {
        const message = "Please call the police";
        speakText(message);
    };

    const handleLost = () => {
        const message = "I am lost. Can you help me find my way?";
        speakText(message);
    };

    const handlePayment = () => {
        const message = "How much does this cost?";
        speakText(message);
    };

    return (
        <TouchableWithoutFeedback onPress={dismissKeyboard}>
            <SafeAreaView style={styles.container}>
                <ScrollView ref={scrollViewRef}>
                    <Text style={styles.header}>🤐 SPEECH ASSIST MODE</Text>

                    {/* Harassment Active Banner */}
                    {isHarassmentActive && (
                        <View style={styles.harassmentActive}>
                            <Ionicons name="alert" size={24} color="#FFF8E7" />
                            <Text style={styles.harassmentActiveText}>🔴 HARASSMENT ALERT ACTIVE</Text>
                            <TouchableOpacity onPress={toggleHarassmentSound}>
                                <Text style={styles.stopHarassmentText}>STOP</Text>
                            </TouchableOpacity>
                        </View>
                    )}

                    {/* Buzzer Status */}
                    {isBuzzerActive && (
                        <View style={styles.buzzerActive}>
                            <Ionicons name="alert" size={24} color="#FFF8E7" />
                            <Text style={styles.buzzerActiveText}>🔔 BUZZER ACTIVE</Text>
                            <TouchableOpacity onPress={stopBuzzer}>
                                <Text style={styles.stopBuzzerText}>STOP</Text>
                            </TouchableOpacity>
                        </View>
                    )}

                    {/* Speed Control Button */}
                    <View style={styles.speedHeader}>
                        <TouchableOpacity 
                            style={styles.speedButton}
                            onPress={() => setShowSpeedControl(!showSpeedControl)}
                        >
                            <Ionicons name="speedometer" size={24} color="#F59E0B" />
                            <Text style={styles.speedButtonText}>
                                {showSpeedControl ? 'Hide Speed Control' : 'Show Speed Control'}
                            </Text>
                        </TouchableOpacity>
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
                            <Text style={styles.speedHint}>Use + / - buttons to adjust speed</Text>
                        </View>
                    )}

                    {/* 1️⃣ QUICK PHRASES SECTION */}
                    <View style={styles.section}>
                        <Text style={styles.sectionTitle}> Quick Phrases</Text>
                        <View style={styles.phraseGrid}>
                            <TouchableOpacity style={styles.phraseButton} onPress={() => { setText('Hello'); speakText('Hello'); }}>
                                <Text style={styles.phraseText}>👋 Hello</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={styles.phraseButton} onPress={handleThankYou}>
                                <Text style={styles.phraseText}>🙏 Thank you</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={styles.phraseButton} onPress={handleHelp}>
                                <Text style={styles.phraseText}>🆘 Help</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={styles.phraseButton} onPress={handleEmergency}>
                                <Text style={styles.phraseText}>🚨 Emergency</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={styles.phraseButton} onPress={handleWater}>
                                <Text style={styles.phraseText}>💧 Water</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={styles.phraseButton} onPress={handleFood}>
                                <Text style={styles.phraseText}>🍔 Food</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={styles.phraseButton} onPress={handleYes}>
                                <Text style={styles.phraseText}>✅ Yes</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={styles.phraseButton} onPress={handleNo}>
                                <Text style={styles.phraseText}>❌ No</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={styles.phraseButton} onPress={handleBathroom}>
                                <Text style={styles.phraseText}>🚽 Bathroom</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={styles.phraseButton} onPress={handleDoctor}>
                                <Text style={styles.phraseText}>👨‍⚕️ Doctor</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={styles.phraseButton} onPress={handlePolice}>
                                <Text style={styles.phraseText}>👮 Police</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={styles.phraseButton} onPress={handleLost}>
                                <Text style={styles.phraseText}>🗺️ I'm lost</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={styles.phraseButton} onPress={handlePayment}>
                                <Text style={styles.phraseText}>💰 How much?</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={styles.phraseButton} onPress={() => speakText('I need a wheelchair')}>
                                <Text style={styles.phraseText}>♿ Wheelchair</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={styles.phraseButton} onPress={() => speakText('Please speak slowly')}>
                                <Text style={styles.phraseText}>🐢 Speak slowly</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={styles.phraseButton} onPress={() => speakText('I cannot speak')}>
                                <Text style={styles.phraseText}>🔇 Cannot speak</Text>
                            </TouchableOpacity>
                        </View>
                    </View>

                    {/* 2️⃣ AUTO SENTENCE GENERATOR SECTION */}
                    <View style={styles.section}>
                        <Text style={styles.sectionTitle}> Auto Sentence Generator</Text>
                        
                        <TouchableOpacity 
                            style={styles.generatorButton}
                            onPress={() => setShowSentenceGenerator(!showSentenceGenerator)}
                        >
                            <Ionicons name="document-text" size={24} color="#1E3A8A" />
                            <Text style={styles.generatorButtonText}>
                                {showSentenceGenerator ? 'Hide Sentences' : 'Show Sentences'}
                            </Text>
                        </TouchableOpacity>

                        {showSentenceGenerator && (
                            <View>
                                {loadingSentences ? (
                                    <ActivityIndicator size="large" color="#F59E0B" style={styles.loader} />
                                ) : (
                                    <>
                                        {/* Category Buttons */}
                                        <ScrollView horizontal showsHorizontalScrollIndicator={true} style={styles.categoryScroll}>
                                            {Object.keys(sentenceCategories).map((category) => (
                                                <TouchableOpacity
                                                    key={category}
                                                    style={[
                                                        styles.categoryButton,
                                                        selectedCategory === category && styles.categoryButtonActive
                                                    ]}
                                                    onPress={() => selectCategory(category)}
                                                >
                                                    <Text style={[
                                                        styles.categoryButtonText,
                                                        selectedCategory === category && styles.categoryButtonTextActive
                                                    ]}>{category}</Text>
                                                </TouchableOpacity>
                                            ))}
                                        </ScrollView>

                                        {/* Sentence Buttons */}
                                        <View style={styles.sentenceContainer}>
                                            {sentenceCategories[selectedCategory]?.map((sentence, index) => (
                                                <TouchableOpacity
                                                    key={index}
                                                    style={styles.sentenceButton}
                                                    onPress={() => selectSentence(sentence)}
                                                >
                                                    <Text style={styles.sentenceButtonText}>{sentence}</Text>
                                                    <Ionicons name="volume-high" size={16} color="#F59E0B" />
                                                </TouchableOpacity>
                                            ))}
                                        </View>
                                    </>
                                )}
                            </View>
                        )}
                    </View>

                    {/* 3️⃣ TEXT TO SPEECH SECTION */}
                    <View style={styles.section}>
                        <Text style={styles.sectionTitle}> Text to Speech</Text>
                        
                        <View style={styles.inputContainer}>
                            <TextInput
                                ref={textInputRef}
                                style={styles.textInput}
                                multiline
                                numberOfLines={4}
                                value={text}
                                onChangeText={setText}
                                placeholder="Type your message here..."
                                placeholderTextColor="#A0A0A0"
                                returnKeyType="done"
                                onSubmitEditing={dismissKeyboard}
                            />
                            {text.length > 0 && (
                                <TouchableOpacity 
                                    style={styles.clearTextButton}
                                    onPress={() => setText('')}
                                >
                                    <Ionicons name="close-circle" size={24} color="#F59E0B" />
                                </TouchableOpacity>
                            )}
                        </View>

                        <View style={styles.actionRow}>
                            <TouchableOpacity 
                                style={[styles.speakButton, isLoading && styles.disabledButton]}
                                onPress={() => speakText()}
                                disabled={isLoading}
                            >
                                {isLoading ? (
                                    <ActivityIndicator color="#1E3A8A" />
                                ) : (
                                    <>
                                        <Ionicons name="volume-high" size={24} color="#1E3A8A" />
                                        <Text style={styles.speakButtonText}>Speak ({speechRate.toFixed(1)}x)</Text>
                                    </>
                                )}
                            </TouchableOpacity>

                            {isKeyboardVisible && (
                                <TouchableOpacity 
                                    style={styles.closeKeyboardButton}
                                    onPress={dismissKeyboard}
                                >
                                    <Ionicons name="chevron-down" size={24} color="#1E3A8A" />
                                </TouchableOpacity>
                            )}
                        </View>
                    </View>

                    {/* 4️⃣ TEXT TO SIGN SECTION */}
                    <View style={styles.section}>
                        <Text style={styles.sectionTitle}> Text to Sign</Text>
                        
                        <TextInput
                            style={styles.textInput}
                            multiline
                            numberOfLines={3}
                            value={text}
                            onChangeText={setText}
                            placeholder="Type your message here..."
                            placeholderTextColor="#A0A0A0"
                        />

                        <TouchableOpacity 
                            style={[styles.signButton, signLoading && styles.disabledButton]}
                            onPress={convertToSign}
                            disabled={signLoading}
                        >
                            {signLoading ? (
                                <ActivityIndicator color="#1E3A8A" />
                            ) : (
                                <>
                                    <Ionicons name="hand-left" size={24} color="#1E3A8A" />
                                    <Text style={styles.signButtonText}>Convert to Sign</Text>
                                </>
                            )}
                        </TouchableOpacity>

                        {signResult && (
                            <View style={styles.signResultContainer}>
                                <Text style={styles.signInfo}>Original: "{signResult.original}"</Text>
                                
                                <ScrollView horizontal showsHorizontalScrollIndicator={true} style={styles.signScroll}>
                                    <View style={styles.signsRow}>
                                        {signResult.signs.map((sign, index) => renderSign(sign, index))}
                                    </View>
                                </ScrollView>
                                
                                <Text style={styles.signCount}>Total: {signResult.signs.length}</Text>
                            </View>
                        )}
                    </View>

                    {/* 5️⃣ SIGN DICTIONARY SECTION */}
                    {signDictionary.length > 0 && (
                        <View style={styles.section}>
                            <Text style={styles.sectionTitle}> Sign Dictionary</Text>
                            <ScrollView horizontal style={styles.dictionaryScroll}>
                                {signDictionary.slice(0, 15).map((item, index) => (
                                    <TouchableOpacity 
                                        key={index}
                                        style={styles.dictionaryItem}
                                        onPress={() => setText(item.word)}
                                    >
                                        <Text style={styles.dictionaryWord}>{item.word}</Text>
                                        <Text style={styles.dictionaryType}>{item.type}</Text>
                                    </TouchableOpacity>
                                ))}
                            </ScrollView>
                        </View>
                    )}

                    {/* 6️⃣ EMERGENCY BUZZER SECTION */}
                    <View style={styles.section}>
                        <Text style={styles.sectionTitle}> Emergency Buzzer</Text>
                        
                        <View style={styles.emergencyGrid}>
                            <TouchableOpacity 
                                style={[styles.emergencyButton, { backgroundColor: isHarassmentActive ? '#EF4444' : '#DC2626' }]}
                                onPress={toggleHarassmentSound}
                            >
                                <Ionicons 
                                    name={isHarassmentActive ? "stop-circle" : "warning"} 
                                    size={32} 
                                    color="#FFF8E7" 
                                />
                                <Text style={styles.emergencyText}>
                                    {isHarassmentActive ? 'STOP' : 'HARASSMENT'}
                                </Text>
                            </TouchableOpacity>

                            <TouchableOpacity 
                                style={[styles.emergencyButton, { backgroundColor: '#F59E0B' }]}
                                onPress={handleBusStop}
                            >
                                <Ionicons name="bus" size={32} color="#1E3A8A" />
                                <Text style={[styles.emergencyText, { color: '#1E3A8A' }]}>BUS STOP</Text>
                            </TouchableOpacity>

                            <TouchableOpacity 
                                style={[styles.emergencyButton, { backgroundColor: '#10B981' }]}
                                onPress={handleMovePlease}
                            >
                                <Ionicons name="walk" size={32} color="#1E3A8A" />
                                <Text style={[styles.emergencyText, { color: '#1E3A8A' }]}>MOVE PLEASE</Text>
                            </TouchableOpacity>

                            <TouchableOpacity 
                                style={[styles.emergencyButton, { backgroundColor: '#1E3A8A' }]}
                                onPress={handleEmergency}
                            >
                                <Ionicons name="alert-circle" size={32} color="#F59E0B" />
                                <Text style={styles.emergencyText}>EMERGENCY</Text>
                            </TouchableOpacity>
                        </View>
                    </View>
                </ScrollView>

                {/* Image Preview Modal */}
                <Modal visible={previewVisible} transparent animationType="fade">
                    <View style={styles.modalOverlay}>
                        <View style={styles.previewContainer}>
                            <Text style={styles.previewTitle}>
                                {selectedSign?.type === 'gif' ? selectedSign.phrase : 
                                 selectedSign?.type === 'letter' ? `Letter ${selectedSign.character?.toUpperCase()}` : 
                                 'Sign Preview'}
                            </Text>
                            
                            <View style={styles.previewImageContainer}>
                                {selectedSign?.type === 'gif' && (
                                    selectedSign?.data ? (
                                        <Image 
                                            source={{ uri: `data:image/gif;base64,${selectedSign.data}` }}
                                            style={styles.previewImage}
                                            resizeMode="contain"
                                        />
                                    ) : selectedSign?.url ? (
                                        <Image 
                                            source={{ uri: `${SERVER_URL}${selectedSign.url}` }}
                                            style={styles.previewImage}
                                            resizeMode="contain"
                                        />
                                    ) : (
                                        <Text style={styles.previewEmoji}>🎬</Text>
                                    )
                                )}
                                
                                {selectedSign?.type === 'letter' && (
                                    <>
                                        <Text style={styles.previewLetter}>{selectedSign.character?.toUpperCase()}</Text>
                                        {selectedSign?.data ? (
                                            <Image 
                                                source={{ uri: `data:image/jpg;base64,${selectedSign.data}` }}
                                                style={styles.previewImage}
                                                resizeMode="contain"
                                            />
                                        ) : selectedSign?.url ? (
                                            <Image 
                                                source={{ uri: `${SERVER_URL}${selectedSign.url}` }}
                                                style={styles.previewImage}
                                                resizeMode="contain"
                                            />
                                        ) : null}
                                    </>
                                )}
                                
                                {selectedSign?.type === 'space' && (
                                    <Text style={styles.previewSpace}>␣</Text>
                                )}
                            </View>
                            
                            <View style={styles.previewControls}>
                                <TouchableOpacity 
                                    style={[styles.previewNavButton, selectedIndex === 0 && styles.previewNavDisabled]}
                                    onPress={goToPrevious}
                                    disabled={selectedIndex === 0}
                                >
                                    <Ionicons name="chevron-back" size={30} color={selectedIndex === 0 ? '#A0A0A0' : '#F59E0B'} />
                                    <Text style={[styles.previewNavText, selectedIndex === 0 && styles.previewNavTextDisabled]}>Prev</Text>
                                </TouchableOpacity>
                                
                                <Text style={styles.previewCounter}>
                                    {selectedIndex + 1} / {signResult?.signs.length || 0}
                                </Text>
                                
                                <TouchableOpacity 
                                    style={[styles.previewNavButton, selectedIndex === (signResult?.signs.length - 1) && styles.previewNavDisabled]}
                                    onPress={goToNext}
                                    disabled={selectedIndex === (signResult?.signs.length - 1)}
                                >
                                    <Text style={[styles.previewNavText, selectedIndex === (signResult?.signs.length - 1) && styles.previewNavTextDisabled]}>Next</Text>
                                    <Ionicons name="chevron-forward" size={30} color={selectedIndex === (signResult?.signs.length - 1) ? '#A0A0A0' : '#F59E0B'} />
                                </TouchableOpacity>
                            </View>
                            
                            <TouchableOpacity 
                                style={styles.previewCloseButton}
                                onPress={() => setPreviewVisible(false)}
                            >
                                <Text style={styles.previewCloseText}>Close</Text>
                            </TouchableOpacity>
                        </View>
                    </View>
                </Modal>
            </SafeAreaView>
        </TouchableWithoutFeedback>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#1E3A8A', // Royal Blue
    },
    header: {
        fontSize: 22,
        fontWeight: 'bold',
        color: '#FFF8E7', // Soft Cream
        padding: 20,
        textAlign: 'center',
        backgroundColor: '#1E3A8A',
        borderBottomWidth: 2,
        borderBottomColor: '#F59E0B', // Golden Yellow
    },
    speedHeader: {
        paddingHorizontal: 15,
        marginTop: 10,
    },
    speedButton: {
        backgroundColor: '#FFF8E7',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 12,
        borderRadius: 25,
        gap: 8,
    },
    speedButtonText: {
        color: '#1E3A8A',
        fontSize: 14,
        fontWeight: 'bold',
    },
    speedControlPanel: {
        backgroundColor: '#FFF8E7',
        padding: 15,
        margin: 15,
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
        marginTop: 5,
    },
    section: {
        backgroundColor: '#FFF8E7', // Soft Cream
        margin: 15,
        padding: 15,
        borderRadius: 15,
    },
    sectionTitle: {
        color: '#F59E0B', // Golden Yellow
        fontSize: 18,
        fontWeight: 'bold',
        marginBottom: 15,
    },
    // Quick Phrases styles
    phraseGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
    },
    phraseButton: {
        backgroundColor: '#1E3A8A',
        paddingHorizontal: 15,
        paddingVertical: 8,
        borderRadius: 20,
        margin: 5,
        borderWidth: 1,
        borderColor: '#F59E0B',
    },
    phraseText: {
        color: '#FFF8E7',
        fontSize: 12,
    },
    // Auto Sentence Generator styles
    generatorButton: {
        backgroundColor: '#F59E0B',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 12,
        borderRadius: 10,
        marginBottom: 15,
        gap: 8,
    },
    generatorButtonText: {
        color: '#1E3A8A',
        fontSize: 16,
        fontWeight: 'bold',
    },
    loader: {
        marginVertical: 20,
    },
    categoryScroll: {
        flexDirection: 'row',
        marginBottom: 15,
    },
    categoryButton: {
        backgroundColor: '#1E3A8A',
        paddingHorizontal: 15,
        paddingVertical: 8,
        borderRadius: 20,
        marginRight: 8,
        borderWidth: 1,
        borderColor: '#F59E0B',
    },
    categoryButtonActive: {
        backgroundColor: '#F59E0B',
    },
    categoryButtonText: {
        color: '#FFF8E7',
        fontSize: 12,
        fontWeight: '500',
    },
    categoryButtonTextActive: {
        color: '#1E3A8A',
        fontWeight: 'bold',
    },
    sentenceContainer: {
        marginTop: 5,
    },
    sentenceButton: {
        backgroundColor: '#1E3A8A',
        padding: 12,
        borderRadius: 8,
        marginBottom: 8,
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    sentenceButtonText: {
        color: '#FFF8E7',
        fontSize: 14,
        flex: 1,
    },
    // Text to Speech styles
    inputContainer: {
        position: 'relative',
        marginBottom: 10,
    },
    textInput: {
        backgroundColor: '#1E3A8A',
        color: '#FFF8E7',
        padding: 15,
        borderRadius: 10,
        fontSize: 16,
        minHeight: 100,
        textAlignVertical: 'top',
        marginBottom: 10,
    },
    clearTextButton: {
        position: 'absolute',
        right: 10,
        top: 10,
    },
    actionRow: {
        flexDirection: 'row',
        gap: 10,
    },
    speakButton: {
        backgroundColor: '#F59E0B',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 15,
        borderRadius: 10,
        flex: 1,
        gap: 8,
    },
    speakButtonText: {
        color: '#1E3A8A',
        fontSize: 16,
        fontWeight: 'bold',
    },
    closeKeyboardButton: {
        backgroundColor: '#F59E0B',
        width: 50,
        justifyContent: 'center',
        alignItems: 'center',
        borderRadius: 10,
    },
    // Text to Sign styles
    signButton: {
        backgroundColor: '#F59E0B',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 15,
        borderRadius: 10,
        marginTop: 5,
        gap: 8,
    },
    signButtonText: {
        color: '#1E3A8A',
        fontSize: 16,
        fontWeight: 'bold',
    },
    disabledButton: {
        opacity: 0.5,
    },
    signResultContainer: {
        marginTop: 15,
        padding: 10,
        backgroundColor: '#1E3A8A',
        borderRadius: 10,
    },
    signScroll: {
        marginVertical: 10,
    },
    signsRow: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: 10,
    },
    signBox: {
        width: 100,
        height: 130,
        backgroundColor: '#1E3A8A',
        borderRadius: 10,
        justifyContent: 'center',
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#F59E0B',
        marginRight: 10,
        padding: 5,
    },
    signChar: {
        color: '#F59E0B',
        fontSize: 32,
        fontWeight: 'bold',
    },
    signLabel: {
        color: '#FFF8E7',
        fontSize: 10,
        marginTop: 5,
        textAlign: 'center',
    },
    signImage: {
        width: 70,
        height: 70,
        resizeMode: 'contain',
    },
    signInfo: {
        color: '#F59E0B',
        fontSize: 14,
        marginBottom: 5,
    },
    signCount: {
        color: '#F59E0B',
        fontSize: 12,
        marginTop: 5,
        textAlign: 'right',
    },
    spaceBox: {
        width: 100,
        height: 130,
        backgroundColor: '#1E3A8A',
        borderRadius: 10,
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 10,
        borderWidth: 1,
        borderColor: '#F59E0B',
    },
    spaceText: {
        color: '#F59E0B',
        fontSize: 32,
    },
    // Sign Dictionary styles
    dictionaryScroll: {
        flexDirection: 'row',
    },
    dictionaryItem: {
        backgroundColor: '#F59E0B',
        padding: 10,
        borderRadius: 5,
        marginRight: 10,
        minWidth: 80,
        alignItems: 'center',
    },
    dictionaryWord: {
        color: '#1E3A8A',
        fontSize: 14,
        fontWeight: 'bold',
    },
    dictionaryType: {
        color: '#1E3A8A',
        fontSize: 10,
        marginTop: 2,
    },
    // Emergency Buzzer styles
    emergencyGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
    },
    emergencyButton: {
        width: '48%',
        padding: 20,
        borderRadius: 10,
        alignItems: 'center',
        marginBottom: 10,
        borderWidth: 1,
        borderColor: '#1E3A8A',
    },
    emergencyText: {
        color: '#FFF8E7',
        fontSize: 12,
        fontWeight: 'bold',
        marginTop: 5,
        textAlign: 'center',
    },
    // Status banners
    harassmentActive: {
        backgroundColor: '#DC2626',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: 15,
        margin: 15,
        borderRadius: 10,
        borderWidth: 2,
        borderColor: '#F59E0B',
    },
    harassmentActiveText: {
        color: '#FFF8E7',
        fontSize: 16,
        fontWeight: 'bold',
    },
    stopHarassmentText: {
        color: '#FFF8E7',
        fontSize: 14,
        fontWeight: 'bold',
        backgroundColor: '#1E3A8A',
        paddingHorizontal: 15,
        paddingVertical: 5,
        borderRadius: 5,
    },
    buzzerActive: {
        backgroundColor: '#EF4444',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: 15,
        margin: 15,
        borderRadius: 10,
        borderWidth: 2,
        borderColor: '#F59E0B',
    },
    buzzerActiveText: {
        color: '#FFF8E7',
        fontSize: 16,
        fontWeight: 'bold',
    },
    stopBuzzerText: {
        color: '#FFF8E7',
        fontSize: 14,
        fontWeight: 'bold',
        backgroundColor: '#1E3A8A',
        paddingHorizontal: 15,
        paddingVertical: 5,
        borderRadius: 5,
    },
    // Modal styles
    modalOverlay: {
        flex: 1,
        backgroundColor: 'rgba(30,58,138,0.9)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    previewContainer: {
        width: width * 0.9,
        backgroundColor: '#FFF8E7',
        borderRadius: 20,
        padding: 20,
        alignItems: 'center',
    },
    previewTitle: {
        color: '#F59E0B',
        fontSize: 20,
        fontWeight: 'bold',
        marginBottom: 20,
    },
    previewImageContainer: {
        width: '100%',
        height: 300,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#1E3A8A',
        borderRadius: 10,
        marginBottom: 20,
    },
    previewImage: {
        width: '100%',
        height: '100%',
    },
    previewLetter: {
        fontSize: 80,
        color: '#F59E0B',
        fontWeight: 'bold',
        position: 'absolute',
        top: 20,
        left: 20,
    },
    previewEmoji: {
        fontSize: 80,
    },
    previewSpace: {
        fontSize: 80,
        color: '#FFF8E7',
    },
    previewControls: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        width: '100%',
        marginBottom: 20,
    },
    previewNavButton: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 10,
    },
    previewNavDisabled: {
        opacity: 0.3,
    },
    previewNavText: {
        color: '#F59E0B',
        fontSize: 16,
        marginHorizontal: 5,
    },
    previewNavTextDisabled: {
        color: '#A0A0A0',
    },
    previewCounter: {
        color: '#1E3A8A',
        fontSize: 16,
    },
    previewCloseButton: {
        backgroundColor: '#1E3A8A',
        paddingVertical: 12,
        paddingHorizontal: 40,
        borderRadius: 10,
    },
    previewCloseText: {
        color: '#FFF8E7',
        fontSize: 16,
        fontWeight: 'bold',
    },
});