import React, { useState } from 'react';
import { 
    View, 
    Text, 
    StyleSheet, 
    TouchableOpacity, 
    Alert, 
    ScrollView,
    Vibration,
    ActivityIndicator,
    Linking,
    Platform
} from 'react-native';
import api from '../services/api';

export default function DashboardScreen({ navigation }) {
    const [loading, setLoading] = useState(false);
    const [emergencyActive, setEmergencyActive] = useState(false);

    // Make emergency call
    const makeEmergencyCall = () => {
        const emergencyNumber = Platform.OS === 'ios' ? '911' : '112';
        const url = Platform.OS === 'ios' 
            ? `telprompt:${emergencyNumber}` 
            : `tel:${emergencyNumber}`;
        
        Linking.openURL(url).catch(err => {
            Alert.alert('Error', 'Could not make emergency call');
        });
    };

    // Main emergency handler - NO SOUND, only vibration
    const handleEmergency = async () => {
        setLoading(true);
        
        try {
            // Simple vibration pattern (3 short pulses)
            Vibration.vibrate([300, 200, 300, 200, 300]);
            setEmergencyActive(true);

            // Show alert with options
            Alert.alert(
                '🚨 EMERGENCY',
                'What would you like to do?',
                [
                    { 
                        text: '📞 CALL 911/112', 
                        onPress: () => {
                            makeEmergencyCall();
                            Vibration.cancel();
                            setEmergencyActive(false);
                        },
                        style: 'destructive'
                    },
                    { 
                        text: '✅ OK', 
                        onPress: () => {
                            Vibration.cancel();
                            setEmergencyActive(false);
                        }
                    }
                ],
                { cancelable: true }
            );

            // Send to backend if available
            try {
                await api.post('/emergency-alert', {
                    userId: '123',
                    message: 'Emergency alert triggered'
                });
            } catch (error) {
                console.log('Backend alert failed:', error);
            }

        } catch (error) {
            Alert.alert('Error', 'Failed to process emergency alert');
            setEmergencyActive(false);
        } finally {
            setLoading(false);
        }
    };

    return (
        <ScrollView contentContainerStyle={styles.container}>
            <Text style={styles.title}>UniVoice</Text>
            <Text style={styles.subtitle}>Communication Without Limits</Text>

            <View style={styles.grid}>
                {/* Normal User - All Features */}
                <TouchableOpacity 
                    style={styles.card} 
                    onPress={() => navigation.navigate('Normal')}
                >
                    <Text style={styles.cardIcon}>👤</Text>
                    <Text style={styles.cardTitle}>Normal User</Text>
                    <Text style={styles.tagline}>Smart features for seamless everyday interaction</Text>
                </TouchableOpacity>

                {/* Blind User - 4 Features */}
                <TouchableOpacity 
                    style={styles.card} 
                    onPress={() => navigation.navigate('Blind')}
                >
                    <Text style={styles.cardIcon}>🦯</Text>
                    <Text style={styles.cardTitle}>Blind User</Text>
                    <Text style={styles.tagline}>Navigate the world through the power of voice</Text>
                </TouchableOpacity>

                {/* Deaf User - 2 Features */}
                <TouchableOpacity 
                    style={styles.card} 
                    onPress={() => navigation.navigate('Deaf')}
                >
                    <Text style={styles.cardIcon}>🧏</Text>
                    <Text style={styles.cardTitle}>Deaf User</Text>
                    <Text style={styles.tagline}>Turning speech into clear visual communication</Text>
                </TouchableOpacity>

                {/* Mute User - 6 Features */}
                <TouchableOpacity 
                    style={styles.card} 
                    onPress={() => navigation.navigate('Mute')}
                >
                    <Text style={styles.cardIcon}>🤐</Text>
                    <Text style={styles.cardTitle}>Mute User</Text>
                    <Text style={styles.tagline}>Express your voice through technology</Text>
                </TouchableOpacity>
            </View>

            {/* Emergency Button */}
            <TouchableOpacity 
                style={styles.emergencyBtn} 
                onPress={handleEmergency}
                disabled={loading}
            >
                {loading ? (
                    <ActivityIndicator color="#FFF8E7" size="large" />
                ) : (
                    <>
                        <Text style={styles.emergencyText}>🚨 EMERGENCY ALERT</Text>
                        <Text style={styles.emergencySubText}>Tap for options (vibration only)</Text>
                    </>
                )}
            </TouchableOpacity>

        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { 
        flexGrow: 1, 
        backgroundColor: '#1E3A8A',
        padding: 20 
    },
    title: { 
        fontSize: 32, 
        fontWeight: 'bold', 
        color: '#FFF8E7',
        textAlign: 'center',
        marginTop: 20,
        marginBottom: 5
    },
    subtitle: { 
        fontSize: 16, 
        color: '#FFF8E7',
        opacity: 0.9,
        textAlign: 'center',
        marginBottom: 30
    },
    grid: {
        width: '100%',
        gap: 15
    },
    card: {
        padding: 20,
        borderRadius: 15,
        alignItems: 'center',
        elevation: 5,
        marginBottom: 10,
        backgroundColor: '#FFF8E7',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
    },
    cardIcon: {
        fontSize: 40,
        marginBottom: 10,
        color: '#F59E0B',
    },
    cardTitle: {
        fontSize: 22,
        color: '#1E3A8A',
        fontWeight: 'bold',
        marginBottom: 8,
    },
    tagline: {
        fontSize: 13,
        color: '#1E3A8A',
        opacity: 0.8,
        textAlign: 'center',
        fontStyle: 'italic',
        paddingHorizontal: 5,
    },
    emergencyBtn: { 
        marginTop: 30, 
        backgroundColor: '#F59E0B',
        padding: 20, 
        borderRadius: 10, 
        alignItems: 'center',
        elevation: 10,
        borderWidth: 0
    },
    emergencyText: { 
        color: '#1E3A8A',
        fontSize: 20, 
        fontWeight: 'bold' 
    },
    emergencySubText: {
        color: '#1E3A8A',
        fontSize: 12,
        marginTop: 5,
        opacity: 0.8
    },
    statsContainer: {
        marginTop: 20,
        padding: 15,
        backgroundColor: '#FFF8E7',
        borderRadius: 10,
        flexDirection: 'row',
        justifyContent: 'space-around',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
    },
    statsText: {
        color: '#1E3A8A',
        fontSize: 13,
        fontWeight: 'bold',
    },
});