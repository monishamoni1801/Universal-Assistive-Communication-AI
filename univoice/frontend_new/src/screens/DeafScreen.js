// src/screens/DeafScreen.js
import React, { useState, useEffect, useRef } from 'react';
import { 
    View, 
    Text, 
    StyleSheet, 
    TouchableOpacity, 
    ScrollView, 
    Alert,
    ActivityIndicator,
    RefreshControl,
    Modal,
    Vibration,
    Image,
    TextInput,
    FlatList,
    Dimensions,
    Switch,
    Keyboard,
    TouchableWithoutFeedback
} from 'react-native';
import { Audio } from 'expo-av';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as Speech from 'expo-speech';
import { sttAPI, statusAPI, emergencyAPI, signAPI, ttsAPI } from '../services/api';

const { width, height } = Dimensions.get('window');

export default function DeafScreen() {
    const [isListening, setIsListening] = useState(false);
    const [captions, setCaptions] = useState([]);
    const [serverConnected, setServerConnected] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [captionSettings, setCaptionSettings] = useState({
        size: 20,
        color: '#FFFFFF',
        background: '#000000',
    });
    
    // Text input for Text-to-Sign
    const [text, setText] = useState('');
    const [isKeyboardVisible, setKeyboardVisible] = useState(false);
    
    // Text-to-Sign states
    const [signResult, setSignResult] = useState(null);
    const [signDictionary, setSignDictionary] = useState([]);
    const [signLoading, setSignLoading] = useState(false);
    
    // Image preview modal states
    const [previewVisible, setPreviewVisible] = useState(false);
    const [selectedSign, setSelectedSign] = useState(null);
    const [selectedIndex, setSelectedIndex] = useState(0);
    
    // Server IP
    const SERVER_IP = '192.168.0.120';
    const SERVER_URL = `http://${SERVER_IP}:5000`;
    
    // Refs
    const pollingInterval = useRef(null);
    const sound = useRef(null);
    const scrollViewRef = useRef(null);
    const textInputRef = useRef(null);

    // ========== INITIALIZATION ==========
    useEffect(() => {
        checkServerConnection();
        loadSignDictionary();
        
        // Keyboard event listeners
        const keyboardDidShowListener = Keyboard.addListener(
            'keyboardDidShow',
            () => {
                setKeyboardVisible(true);
                // Scroll to bottom when keyboard opens
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
            if (pollingInterval.current) {
                clearInterval(pollingInterval.current);
            }
            if (isListening) {
                stopListening();
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

    const checkServerConnection = async () => {
        try {
            const response = await statusAPI.check();
            setServerConnected(response.data.success);
            console.log('Server connected:', response.data);
        } catch (error) {
            console.log('Server connection failed:', error.message);
            setServerConnected(false);
        }
    };

    // ========== SPEECH-TO-TEXT FUNCTIONS ==========
    const startListening = async () => {
        if (!serverConnected) {
            Alert.alert('Error', 'Cannot connect to Python server');
            return;
        }

        setIsLoading(true);
        try {
            const response = await sttAPI.startListening();
            if (response.data.success) {
                setIsListening(true);
                startPolling();
                Alert.alert('Success', 'Listening started');
            }
        } catch (error) {
            Alert.alert('Error', 'Failed to start listening: ' + error.message);
        } finally {
            setIsLoading(false);
        }
    };

    const stopListening = async () => {
        setIsLoading(true);
        try {
            const response = await sttAPI.stopListening();
            if (response.data.success) {
                setIsListening(false);
                if (pollingInterval.current) {
                    clearInterval(pollingInterval.current);
                }
            }
        } catch (error) {
            console.log('Error stopping:', error);
        } finally {
            setIsLoading(false);
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
                        isEmergency: response.data.is_emergency
                    };
                    
                    setCaptions(prev => [newCaption, ...prev].slice(0, 50));
                    
                    if (response.data.is_emergency) {
                        handleEmergency();
                    }
                }
            } catch (error) {
                console.log('Polling error:', error);
            }
        }, 2000);
    };

    const handleEmergency = () => {
        Vibration.vibrate([500, 500, 500]);
        
        Alert.alert(
            '🚨 EMERGENCY DETECTED',
            'Emergency keywords detected in speech!',
            [
                { text: 'OK' },
                { text: 'Send Alert', onPress: sendEmergencyAlert }
            ]
        );
    };

    const sendEmergencyAlert = async () => {
        try {
            await emergencyAPI.sendAlert('user123', { lat: 0, lng: 0 }, 'speech_emergency');
            Alert.alert('Alert Sent', 'Emergency contacts notified');
        } catch (error) {
            Alert.alert('Error', 'Failed to send alert');
        }
    };

    const toggleListening = () => {
        if (isListening) {
            stopListening();
        } else {
            startListening();
        }
    };

    const clearCaptions = () => {
        Alert.alert(
            'Clear Captions',
            'Clear all captions?',
            [
                { text: 'Cancel', style: 'cancel' },
                { text: 'Clear', onPress: () => setCaptions([]) }
            ]
        );
    };

    const onRefresh = async () => {
        setRefreshing(true);
        await checkServerConnection();
        setRefreshing(false);
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
            
            if (response.data.success) {
                setSignResult(response.data.result);
                // Auto scroll to results
                setTimeout(() => {
                    if (scrollViewRef.current) {
                        scrollViewRef.current.scrollToEnd({ animated: true });
                    }
                }, 100);
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

    // Dismiss keyboard
    const dismissKeyboard = () => {
        Keyboard.dismiss();
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

    return (
        <TouchableWithoutFeedback onPress={dismissKeyboard}>
            <View style={styles.container}>
                {/* Header */}
                <View style={styles.header}>
                    <Text style={styles.headerTitle}>🧏 HEARING ASSIST MODE</Text>
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

                {/* Top Half - Speech to Text */}
                <View style={styles.topHalf}>
                    <View style={styles.halfHeader}>
                        <Ionicons name="mic" size={24} color="#F59E0B" />
                        <Text style={styles.halfTitle}>Speech to Text</Text>
                    </View>

                    <View style={styles.controlPanel}>
                        <TouchableOpacity 
                            style={[
                                styles.listenButton,
                                isListening && styles.listeningActive,
                                (!serverConnected || isLoading) && styles.disabledButton
                            ]}
                            onPress={toggleListening}
                            disabled={!serverConnected || isLoading}
                        >
                            {isLoading ? (
                                <ActivityIndicator color="#1E3A8A" />
                            ) : (
                                <>
                                    <Ionicons 
                                        name={isListening ? 'mic' : 'mic-off'} 
                                        size={24} 
                                        color="#1E3A8A" 
                                    />
                                    <Text style={styles.listenButtonText}>
                                        {isListening ? 'Listening...' : 'Start Listening'}
                                    </Text>
                                </>
                            )}
                        </TouchableOpacity>

                        {captions.length > 0 && (
                            <TouchableOpacity 
                                style={styles.clearButton}
                                onPress={clearCaptions}
                            >
                                <Text style={styles.clearButtonText}>Clear</Text>
                            </TouchableOpacity>
                        )}
                    </View>

                    <ScrollView 
                        style={styles.captionsContainer}
                        ref={scrollViewRef}
                    >
                        {captions.length > 0 ? (
                            captions.map((caption) => (
                                <View 
                                    key={caption.id}
                                    style={[
                                        styles.captionBubble,
                                        caption.isEmergency && styles.emergencyBubble
                                    ]}
                                >
                                    <Text style={styles.captionText}>
                                        {caption.text}
                                    </Text>
                                    <View style={styles.captionFooter}>
                                        <Text style={styles.captionTime}>{caption.timestamp}</Text>
                                        {caption.confidence && (
                                            <Text style={styles.confidenceText}>
                                                {Math.round(caption.confidence * 100)}%
                                            </Text>
                                        )}
                                    </View>
                                </View>
                            ))
                        ) : (
                            <View style={styles.placeholderContainer}>
                                <Ionicons name="chatbubble-outline" size={40} color="#F59E0B" />
                                <Text style={styles.placeholderText}>
                                    {serverConnected 
                                        ? 'No captions yet. Start listening to begin.'
                                        : 'Connect to server first'}
                                </Text>
                            </View>
                        )}
                    </ScrollView>

                    {!serverConnected && (
                        <TouchableOpacity 
                            style={styles.connectPrompt}
                            onPress={checkServerConnection}
                        >
                            <Ionicons name="warning" size={20} color="#F59E0B" />
                            <Text style={styles.connectPromptText}>
                                Tap to reconnect to server
                            </Text>
                        </TouchableOpacity>
                    )}
                </View>

                {/* Bottom Half - Text to Sign */}
                <View style={[styles.bottomHalf, isKeyboardVisible && styles.bottomHalfKeyboard]}>
                    <View style={styles.halfHeader}>
                        <Ionicons name="hand-left" size={24} color="#F59E0B" />
                        <Text style={styles.halfTitle}>Text to Sign</Text>
                    </View>

                    <View style={styles.section}>
                        <View style={styles.inputContainer}>
                            <TextInput
                                ref={textInputRef}
                                style={styles.textInput}
                                multiline
                                numberOfLines={3}
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

                        <View style={styles.buttonRow}>
                            <TouchableOpacity 
                                style={[styles.convertButton, signLoading && styles.disabledButton]}
                                onPress={convertToSign}
                                disabled={signLoading}
                            >
                                {signLoading ? (
                                    <ActivityIndicator color="#1E3A8A" />
                                ) : (
                                    <>
                                        <Ionicons name="hand-left" size={20} color="#1E3A8A" />
                                        <Text style={styles.convertButtonText}>Convert</Text>
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
            </View>
        </TouchableWithoutFeedback>
    );
}

// All styles
const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#1E3A8A',
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 15,
        backgroundColor: '#1E3A8A',
        borderBottomWidth: 2,
        borderBottomColor: '#F59E0B',
    },
    headerTitle: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#FFF8E7',
    },
    statusBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#FFF8E7',
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
        color: '#1E3A8A',
        fontSize: 12,
        fontWeight: '600',
    },
    topHalf: {
        flex: 1,
        padding: 15,
    },
    bottomHalf: {
        flex: 1,
        padding: 15,
        paddingTop: 5,
    },
    bottomHalfKeyboard: {
        flex: 0.8, // Adjust when keyboard is open
    },
    halfHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 10,
        gap: 8,
    },
    halfTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#F59E0B',
    },
    // Speech-to-Text styles
    controlPanel: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 10,
    },
    listenButton: {
        backgroundColor: '#F59E0B',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 12,
        borderRadius: 25,
        flex: 1,
    },
    listeningActive: {
        backgroundColor: '#10B981',
    },
    disabledButton: {
        opacity: 0.5,
    },
    listenButtonText: {
        color: '#1E3A8A',
        fontSize: 14,
        fontWeight: 'bold',
        marginLeft: 8,
    },
    clearButton: {
        backgroundColor: '#FFF8E7',
        paddingHorizontal: 15,
        paddingVertical: 8,
        borderRadius: 20,
        marginLeft: 10,
        borderWidth: 1,
        borderColor: '#F59E0B',
    },
    clearButtonText: {
        color: '#1E3A8A',
        fontSize: 12,
        fontWeight: '600',
    },
    captionsContainer: {
        flex: 1,
        backgroundColor: '#FFF8E7',
        borderRadius: 10,
        padding: 10,
        marginBottom: 10,
    },
    captionBubble: {
        backgroundColor: '#1E3A8A',
        padding: 10,
        borderRadius: 8,
        marginBottom: 6,
    },
    emergencyBubble: {
        borderWidth: 2,
        borderColor: '#EF4444',
    },
    captionText: {
        color: '#FFF8E7',
        fontSize: 16,
        lineHeight: 22,
        marginBottom: 3,
    },
    captionFooter: {
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
    captionTime: {
        color: '#F59E0B',
        fontSize: 9,
    },
    confidenceText: {
        color: '#10B981',
        fontSize: 9,
    },
    placeholderContainer: {
        alignItems: 'center',
        justifyContent: 'center',
        padding: 20,
    },
    placeholderText: {
        color: '#1E3A8A',
        fontSize: 14,
        marginTop: 10,
        textAlign: 'center',
    },
    connectPrompt: {
        backgroundColor: '#FFF8E7',
        flexDirection: 'row',
        alignItems: 'center',
        padding: 10,
        borderRadius: 8,
        borderWidth: 1,
        borderColor: '#F59E0B',
    },
    connectPromptText: {
        color: '#F59E0B',
        marginLeft: 8,
        fontSize: 12,
    },
    // Text-to-Sign styles
    section: {
        backgroundColor: '#FFF8E7',
        borderRadius: 10,
        padding: 12,
        marginBottom: 10,
    },
    inputContainer: {
        position: 'relative',
        marginBottom: 10,
    },
    textInput: {
        backgroundColor: '#1E3A8A',
        color: '#FFF8E7',
        padding: 12,
        paddingRight: 40,
        borderRadius: 8,
        fontSize: 14,
        minHeight: 70,
        textAlignVertical: 'top',
    },
    clearTextButton: {
        position: 'absolute',
        right: 10,
        top: 10,
    },
    buttonRow: {
        flexDirection: 'row',
        gap: 10,
    },
    convertButton: {
        backgroundColor: '#F59E0B',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 10,
        borderRadius: 8,
        flex: 1,
        gap: 5,
    },
    convertButtonText: {
        color: '#1E3A8A',
        fontSize: 14,
        fontWeight: 'bold',
    },
    closeKeyboardButton: {
        backgroundColor: '#F59E0B',
        width: 44,
        justifyContent: 'center',
        alignItems: 'center',
        borderRadius: 8,
    },
    signResultContainer: {
        backgroundColor: '#FFF8E7',
        borderRadius: 10,
        padding: 12,
    },
    signScroll: {
        marginVertical: 8,
    },
    signsRow: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: 5,
    },
    signBox: {
        width: 70,
        height: 90,
        backgroundColor: '#1E3A8A',
        borderRadius: 8,
        justifyContent: 'center',
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#F59E0B',
        marginRight: 8,
        padding: 3,
    },
    signChar: {
        color: '#F59E0B',
        fontSize: 24,
        fontWeight: 'bold',
    },
    signLabel: {
        color: '#FFF8E7',
        fontSize: 8,
        marginTop: 3,
        textAlign: 'center',
    },
    signImage: {
        width: 50,
        height: 50,
        resizeMode: 'contain',
    },
    signInfo: {
        color: '#1E3A8A',
        fontSize: 12,
        marginBottom: 5,
    },
    signCount: {
        color: '#F59E0B',
        fontSize: 10,
        marginTop: 5,
        textAlign: 'right',
    },
    spaceBox: {
        width: 70,
        height: 90,
        backgroundColor: '#1E3A8A',
        borderRadius: 8,
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 8,
        borderWidth: 1,
        borderColor: '#F59E0B',
    },
    spaceText: {
        color: '#F59E0B',
        fontSize: 24,
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
        height: 250,
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
        fontSize: 60,
        color: '#F59E0B',
        fontWeight: 'bold',
        position: 'absolute',
        top: 10,
        left: 10,
    },
    previewEmoji: {
        fontSize: 60,
    },
    previewSpace: {
        fontSize: 60,
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
        padding: 8,
    },
    previewNavDisabled: {
        opacity: 0.3,
    },
    previewNavText: {
        color: '#F59E0B',
        fontSize: 14,
        marginHorizontal: 5,
    },
    previewNavTextDisabled: {
        color: '#A0A0A0',
    },
    previewCounter: {
        color: '#1E3A8A',
        fontSize: 14,
    },
    previewCloseButton: {
        backgroundColor: '#1E3A8A',
        paddingVertical: 10,
        paddingHorizontal: 30,
        borderRadius: 8,
    },
    previewCloseText: {
        color: '#FFF8E7',
        fontSize: 14,
        fontWeight: 'bold',
    },
});