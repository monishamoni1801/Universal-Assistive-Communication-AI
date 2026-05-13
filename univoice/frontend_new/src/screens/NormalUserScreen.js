// src/screens/NormalUserScreen.js
import React, { useState, useRef, useEffect } from 'react';
import { 
    View, 
    Text, 
    StyleSheet, 
    TouchableOpacity, 
    ScrollView,
    TextInput,
    Alert,
    ActivityIndicator,
    Modal,
    FlatList,
    Image,
    Dimensions
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Audio } from 'expo-av';
import * as Speech from 'expo-speech';
import * as ImagePicker from 'expo-image-picker';
import { CameraView, useCameraPermissions } from 'expo-camera';
import api, { sttAPI, ttsAPI, signAPI, emergencyAPI } from '../services/api';

const { width } = Dimensions.get('window');

export default function NormalUserScreen({ navigation }) {
    // ========== STATE VARIABLES ==========
    const [text, setText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [activeFeature, setActiveFeature] = useState(null);
    
    // Text-to-Speech states
    const [voices, setVoices] = useState([]);
    const [selectedVoice, setSelectedVoice] = useState(0);
    const [showVoicePicker, setShowVoicePicker] = useState(false);
    
    // Speech-to-Text states
    const [isListening, setIsListening] = useState(false);
    const [captions, setCaptions] = useState([]);
    const [serverConnected, setServerConnected] = useState(false);
    
    // Text-to-Sign states
    const [signResult, setSignResult] = useState(null);
    const [signLoading, setSignLoading] = useState(false);
    
    // Image preview modal for signs
    const [previewVisible, setPreviewVisible] = useState(false);
    const [selectedSign, setSelectedSign] = useState(null);
    const [selectedIndex, setSelectedIndex] = useState(0);
    
    // Refs
    const sound = useRef(null);
    const pollingInterval = useRef(null);

    // ========== INITIALIZATION ==========
    useEffect(() => {
        checkServerConnection();
        loadVoices();
        
        return () => {
            if (sound.current) {
                sound.current.unloadAsync();
            }
            if (pollingInterval.current) {
                clearInterval(pollingInterval.current);
            }
            if (isListening) {
                stopListening();
            }
        };
    }, []);

    const checkServerConnection = async () => {
        try {
            const response = await api.get('/api/status');
            setServerConnected(response.data.success);
            console.log('Server connected:', response.data);
        } catch (error) {
            console.log('Server connection failed:', error.message);
            setServerConnected(false);
        }
    };

    const loadVoices = async () => {
        try {
            const response = await ttsAPI.getVoices();
            setVoices(response.data.voices || []);
        } catch (error) {
            console.log('Error loading voices:', error);
        }
    };

    // ========== TEXT TO SPEECH ==========
    const speakText = async () => {
        if (!text.trim()) {
            Alert.alert('Error', 'Please enter some text');
            return;
        }

        setIsLoading(true);
        setActiveFeature('tts');
        try {
            await Speech.speak(text, {
                language: 'en',
                pitch: 1,
                rate: 0.9,
            });
            Alert.alert('Success', 'Speaking now...');
        } catch (error) {
            try {
                const response = await ttsAPI.speak(text, selectedVoice, 170, 0.9);
                const { sound: newSound } = await Audio.Sound.createAsync(
                    { uri: response.data.uri }
                );
                sound.current = newSound;
                await sound.current.playAsync();
                Alert.alert('Success', 'Playing audio...');
            } catch (e) {
                Alert.alert('Error', 'Could not play audio');
            }
        } finally {
            setIsLoading(false);
            setActiveFeature(null);
        }
    };

    // ========== SPEECH TO TEXT ==========
    const startListening = async () => {
        if (!serverConnected) {
            Alert.alert('Error', 'Cannot connect to server');
            return;
        }

        setIsLoading(true);
        setActiveFeature('stt');
        try {
            const response = await sttAPI.startListening();
            if (response.data.success) {
                setIsListening(true);
                startPolling();
                Alert.alert('Listening', 'Speak now...');
            }
        } catch (error) {
            Alert.alert('Error', 'Failed to start listening');
        } finally {
            setIsLoading(false);
        }
    };

    const stopListening = async () => {
        try {
            const response = await sttAPI.stopListening();
            if (response.data.success) {
                setIsListening(false);
                if (pollingInterval.current) {
                    clearInterval(pollingInterval.current);
                }
                Alert.alert('Stopped', 'Listening stopped');
            }
        } catch (error) {
            console.log('Error stopping:', error);
        }
    };

    const startPolling = () => {
        pollingInterval.current = setInterval(async () => {
            try {
                const response = await sttAPI.getLatestText();
                if (response.data.success && response.data.text) {
                    const newCaption = {
                        id: Date.now(),
                        text: response.data.text,
                        confidence: response.data.confidence,
                        timestamp: new Date().toLocaleTimeString(),
                    };
                    
                    setCaptions(prev => [newCaption, ...prev].slice(0, 10));
                    setText(response.data.text);
                }
            } catch (error) {
                console.log('Polling error:', error);
            }
        }, 2000);
    };

    // ========== TEXT TO SIGN ==========
    const convertToSign = async () => {
        if (!text.trim()) {
            Alert.alert('Error', 'Please enter some text');
            return;
        }

        setSignLoading(true);
        setActiveFeature('textToSign');
        try {
            const response = await signAPI.convert(text);
            
            if (response.data.success) {
                setSignResult(response.data.result);
                Alert.alert('Success', `Converted to ${response.data.result.type} sign language`);
            } else {
                Alert.alert('Error', response.data.error || 'Conversion failed');
            }
        } catch (error) {
            Alert.alert('Error', 'Failed to convert to sign language');
        } finally {
            setSignLoading(false);
            setActiveFeature(null);
        }
    };

    // Handle sign press for preview
    const handleSignPress = (sign, index) => {
        setSelectedSign(sign);
        setSelectedIndex(index);
        setPreviewVisible(true);
    };

    // Navigate through signs
    const goToPrevious = () => {
        if (signResult && selectedIndex > 0) {
            const newIndex = selectedIndex - 1;
            setSelectedIndex(newIndex);
            setSelectedSign(signResult.signs[newIndex]);
        }
    };

    const goToNext = () => {
        if (signResult && selectedIndex < signResult.signs.length - 1) {
            const newIndex = selectedIndex + 1;
            setSelectedIndex(newIndex);
            setSelectedSign(signResult.signs[newIndex]);
        }
    };

    // Render sign item
    const renderSign = (sign, index) => {
        const baseUrl = 'http://192.168.0.120:5000';
        
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
            </TouchableOpacity>
        );
    };

    // Clear all
    const clearAll = () => {
        setText('');
        setSignResult(null);
        setCaptions([]);
        Alert.alert('Cleared', 'All text cleared');
    };

    return (
        <ScrollView style={styles.container}>
            {/* Header with Server Status */}
            <View style={styles.header}>
                <View>
                    <Text style={styles.userName}>NORMAL USER MODE</Text>
                </View>
                <View style={styles.statusBadge}>
                    <View style={[
                        styles.statusDot,
                        { backgroundColor: serverConnected ? '#10B981' : '#EF4444' }
                    ]} />
                    <Text style={styles.statusText}>
                        {serverConnected ? 'Connected' : 'Disconnected'}
                    </Text>
                </View>
            </View>

            {/* Input Section */}
            <View style={styles.inputSection}>
                <Text style={styles.sectionTitle}>Enter Text</Text>
                <TextInput
                    style={styles.textInput}
                    placeholder="Type or speak here..."
                    placeholderTextColor="#A0A0A0"
                    value={text}
                    onChangeText={setText}
                    multiline
                />
                
                {/* Clear Button */}
                {text !== '' && (
                    <TouchableOpacity style={styles.clearButton} onPress={clearAll}>
                        <Ionicons name="close-circle" size={24} color="#EF4444" />
                    </TouchableOpacity>
                )}
            </View>

            {/* Main Communication Features */}
            <Text style={styles.sectionTitle}>Communication Tools</Text>
            <View style={styles.featuresGrid}>
                {/* Text to Speech */}
                <TouchableOpacity
                    style={[styles.featureCard, activeFeature === 'tts' && styles.activeFeature]}
                    onPress={speakText}
                    disabled={isLoading}
                >
                    {isLoading && activeFeature === 'tts' ? (
                        <ActivityIndicator color="#F59E0B" />
                    ) : (
                        <>
                            <Ionicons name="volume-high" size={32} color="#F59E0B" />
                            <Text style={styles.featureName}>Text to Speech</Text>
                            <Text style={styles.featureDesc}>Convert text to voice</Text>
                        </>
                    )}
                </TouchableOpacity>

                {/* Speech to Text */}
                <TouchableOpacity
                    style={[styles.featureCard, activeFeature === 'stt' && styles.activeFeature]}
                    onPress={isListening ? stopListening : startListening}
                    disabled={isLoading}
                >
                    {isLoading && activeFeature === 'stt' ? (
                        <ActivityIndicator color="#F59E0B" />
                    ) : (
                        <>
                            <Ionicons 
                                name={isListening ? 'mic' : 'mic-outline'} 
                                size={32} 
                                color="#F59E0B" 
                            />
                            <Text style={styles.featureName}>
                                {isListening ? 'Listening...' : 'Speech to Text'}
                            </Text>
                            <Text style={styles.featureDesc}>
                                {isListening ? 'Tap to stop' : 'Convert voice to text'}
                            </Text>
                        </>
                    )}
                </TouchableOpacity>

                {/* Text to Sign */}
                <TouchableOpacity
                    style={[styles.featureCard, activeFeature === 'textToSign' && styles.activeFeature]}
                    onPress={convertToSign}
                    disabled={signLoading}
                >
                    {signLoading ? (
                        <ActivityIndicator color="#F59E0B" />
                    ) : (
                        <>
                            <Ionicons name="hand-left" size={32} color="#F59E0B" />
                            <Text style={styles.featureName}>Text to Sign</Text>
                            <Text style={styles.featureDesc}>Convert text to sign language</Text>
                        </>
                    )}
                </TouchableOpacity>
            </View>

            {/* Live Captions (from Speech to Text) */}
            {captions.length > 0 && (
                <View style={styles.captionsContainer}>
                    <Text style={styles.sectionTitle}>Live Captions</Text>
                    {captions.map((caption) => (
                        <View key={caption.id} style={styles.captionBubble}>
                            <Text style={styles.captionText}>{caption.text}</Text>
                            <Text style={styles.captionTime}>{caption.timestamp}</Text>
                        </View>
                    ))}
                </View>
            )}

            {/* Sign Language Result */}
            {signResult && (
                <View style={styles.signResultContainer}>
                    <Text style={styles.sectionTitle}>Sign Language Result</Text>
                    <Text style={styles.signInfo}>Type: {signResult.type}</Text>
                    <Text style={styles.signInfo}>Original: "{signResult.original}"</Text>
                    
                    <ScrollView horizontal showsHorizontalScrollIndicator={true} style={styles.signScroll}>
                        <View style={styles.signsRow}>
                            {signResult.signs.map((sign, index) => renderSign(sign, index))}
                        </View>
                    </ScrollView>
                    
                    <Text style={styles.signCount}>Total signs: {signResult.signs.length}</Text>
                </View>
            )}

            {/* Quick Actions */}
            <Text style={styles.sectionTitle}>Quick Actions</Text>
            <View style={styles.actionsContainer}>
                <TouchableOpacity 
                    style={styles.actionButton}
                    onPress={() => navigation.navigate('Blind')}
                >
                    <Ionicons name="eye-off" size={24} color="#F59E0B" />
                    <Text style={styles.actionText}>Blind Mode</Text>
                </TouchableOpacity>

                <TouchableOpacity 
                    style={styles.actionButton}
                    onPress={() => navigation.navigate('Deaf')}
                >
                    <Ionicons name="ear" size={24} color="#F59E0B" />
                    <Text style={styles.actionText}>Deaf Mode</Text>
                </TouchableOpacity>

                <TouchableOpacity 
                    style={styles.actionButton}
                    onPress={() => navigation.navigate('Mute')}
                >
                    <Ionicons name="mic-off" size={24} color="#F59E0B" />
                    <Text style={styles.actionText}>Mute Mode</Text>
                </TouchableOpacity>
            </View>

            {/* Voice Picker Modal */}
            <Modal visible={showVoicePicker} transparent animationType="slide">
                <View style={styles.modalContainer}>
                    <View style={styles.modalContent}>
                        <Text style={styles.modalTitle}>Select Voice</Text>
                        
                        <FlatList
                            data={voices}
                            keyExtractor={(item, index) => index.toString()}
                            renderItem={({ item, index }) => (
                                <TouchableOpacity
                                    style={[
                                        styles.voiceItem,
                                        selectedVoice === index && styles.selectedVoiceItem
                                    ]}
                                    onPress={() => {
                                        setSelectedVoice(index);
                                        setShowVoicePicker(false);
                                    }}
                                >
                                    <Text style={styles.voiceItemText}>{item.name}</Text>
                                    <Text style={styles.voiceItemGender}>{item.gender}</Text>
                                </TouchableOpacity>
                            )}
                        />
                        
                        <TouchableOpacity
                            style={styles.closeButton}
                            onPress={() => setShowVoicePicker(false)}
                        >
                            <Text style={styles.closeButtonText}>Close</Text>
                        </TouchableOpacity>
                    </View>
                </View>
            </Modal>

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
                                        source={{ uri: `http://192.168.0.120:5000${selectedSign.url}` }}
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
                                            source={{ uri: `http://192.168.0.120:5000${selectedSign.url}` }}
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
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#1E3A8A', // Royal Blue
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 20,
        backgroundColor: '#1E3A8A', // Royal Blue
        borderBottomWidth: 1,
        borderBottomColor: '#F59E0B', // Golden Yellow
    },
    greeting: {
        fontSize: 16,
        color: '#FFF8E7', // Soft Cream
        opacity: 0.9,
    },
    userName: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#FFF8E7', // Soft Cream
    },
    statusBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#FFF8E7', // Soft Cream
        paddingHorizontal: 10,
        paddingVertical: 5,
        borderRadius: 15,
    },
    statusDot: {
        width: 8,
        height: 8,
        borderRadius: 4,
        marginRight: 5,
    },
    statusText: {
        color: '#1E3A8A', // Royal Blue
        fontSize: 12,
        fontWeight: '600',
    },
    inputSection: {
        padding: 15,
        position: 'relative',
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#F59E0B', // Golden Yellow
        marginHorizontal: 15,
        marginTop: 15,
        marginBottom: 10,
    },
    textInput: {
        backgroundColor: '#FFF8E7', // Soft Cream
        color: '#1E3A8A', // Royal Blue
        padding: 15,
        borderRadius: 10,
        fontSize: 16,
        minHeight: 100,
        textAlignVertical: 'top',
    },
    clearButton: {
        position: 'absolute',
        right: 25,
        top: 55,
    },
    featuresGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        paddingHorizontal: 15,
        justifyContent: 'space-between',
    },
    featureCard: {
        width: '48%',
        backgroundColor: '#FFF8E7', // Soft Cream
        padding: 15,
        borderRadius: 10,
        alignItems: 'center',
        marginBottom: 15,
        borderWidth: 2,
        borderColor: 'transparent',
    },
    activeFeature: {
        borderColor: '#F59E0B', // Golden Yellow
    },
    featureName: {
        color: '#1E3A8A', // Royal Blue
        marginTop: 10,
        fontSize: 14,
        fontWeight: 'bold',
        textAlign: 'center',
    },
    featureDesc: {
        color: '#1E3A8A', // Royal Blue
        opacity: 0.7,
        fontSize: 10,
        textAlign: 'center',
        marginTop: 5,
    },
    captionsContainer: {
        backgroundColor: '#FFF8E7', // Soft Cream
        margin: 15,
        padding: 15,
        borderRadius: 10,
    },
    captionBubble: {
        backgroundColor: '#1E3A8A', // Royal Blue
        padding: 10,
        borderRadius: 8,
        marginBottom: 5,
    },
    captionText: {
        color: '#FFF8E7', // Soft Cream
        fontSize: 14,
    },
    captionTime: {
        color: '#F59E0B', // Golden Yellow
        fontSize: 10,
        textAlign: 'right',
        marginTop: 5,
    },
    signResultContainer: {
        backgroundColor: '#FFF8E7', // Soft Cream
        margin: 15,
        padding: 15,
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
        backgroundColor: '#1E3A8A', // Royal Blue
        borderRadius: 10,
        justifyContent: 'center',
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#F59E0B', // Golden Yellow
        marginRight: 10,
        padding: 5,
    },
    signChar: {
        color: '#F59E0B', // Golden Yellow
        fontSize: 32,
        fontWeight: 'bold',
    },
    signLabel: {
        color: '#FFF8E7', // Soft Cream
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
        color: '#1E3A8A', // Royal Blue
        fontSize: 14,
        marginBottom: 5,
    },
    signCount: {
        color: '#F59E0B', // Golden Yellow
        fontSize: 12,
        marginTop: 10,
        textAlign: 'right',
    },
    spaceBox: {
        width: 100,
        height: 130,
        backgroundColor: '#1E3A8A', // Royal Blue
        borderRadius: 10,
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 10,
        borderWidth: 1,
        borderColor: '#F59E0B', // Golden Yellow
    },
    spaceText: {
        color: '#F59E0B', // Golden Yellow
        fontSize: 32,
    },
    actionsContainer: {
        paddingHorizontal: 15,
        gap: 10,
        marginBottom: 15,
    },
    actionButton: {
        backgroundColor: '#FFF8E7', // Soft Cream
        padding: 15,
        borderRadius: 10,
        flexDirection: 'row',
        alignItems: 'center',
        gap: 15,
        borderWidth: 1,
        borderColor: '#F59E0B', // Golden Yellow
    },
    actionText: {
        color: '#1E3A8A', // Royal Blue
        fontSize: 16,
        fontWeight: '500',
    },
    // Modal styles
    modalContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: 'rgba(30,58,138,0.9)', // Royal Blue with opacity
    },
    modalContent: {
        backgroundColor: '#FFF8E7', // Soft Cream
        borderRadius: 20,
        padding: 20,
        width: '80%',
        maxHeight: '70%',
    },
    modalTitle: {
        color: '#F59E0B', // Golden Yellow
        fontSize: 18,
        fontWeight: 'bold',
        marginBottom: 15,
        textAlign: 'center',
    },
    voiceItem: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 15,
        borderBottomWidth: 1,
        borderBottomColor: '#1E3A8A', // Royal Blue
    },
    selectedVoiceItem: {
        backgroundColor: '#F59E0B', // Golden Yellow
    },
    voiceItemText: {
        color: '#1E3A8A', // Royal Blue
        fontSize: 14,
    },
    voiceItemGender: {
        color: '#1E3A8A', // Royal Blue
        opacity: 0.7,
        fontSize: 12,
    },
    closeButton: {
        backgroundColor: '#1E3A8A', // Royal Blue
        padding: 15,
        borderRadius: 10,
        marginTop: 15,
        alignItems: 'center',
    },
    closeButtonText: {
        color: '#FFF8E7', // Soft Cream
        fontSize: 16,
        fontWeight: 'bold',
    },
    modalOverlay: {
        flex: 1,
        backgroundColor: 'rgba(30,58,138,0.95)', // Royal Blue with opacity
        justifyContent: 'center',
        alignItems: 'center',
    },
    previewContainer: {
        width: width * 0.9,
        backgroundColor: '#FFF8E7', // Soft Cream
        borderRadius: 20,
        padding: 20,
        alignItems: 'center',
    },
    previewTitle: {
        color: '#F59E0B', // Golden Yellow
        fontSize: 20,
        fontWeight: 'bold',
        marginBottom: 20,
    },
    previewImageContainer: {
        width: '100%',
        height: 300,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#1E3A8A', // Royal Blue
        borderRadius: 10,
        marginBottom: 20,
    },
    previewImage: {
        width: '100%',
        height: '100%',
    },
    previewLetter: {
        fontSize: 80,
        color: '#F59E0B', // Golden Yellow
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
        color: '#FFF8E7', // Soft Cream
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
        color: '#F59E0B', // Golden Yellow
        fontSize: 16,
        marginHorizontal: 5,
    },
    previewNavTextDisabled: {
        color: '#A0A0A0',
    },
    previewCounter: {
        color: '#1E3A8A', // Royal Blue
        fontSize: 16,
    },
    previewCloseButton: {
        backgroundColor: '#1E3A8A', // Royal Blue
        paddingVertical: 12,
        paddingHorizontal: 40,
        borderRadius: 10,
    },
    previewCloseText: {
        color: '#FFF8E7', // Soft Cream
        fontSize: 16,
        fontWeight: 'bold',
    },
});