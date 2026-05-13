// App.js
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

// Screens
import DashboardScreen from './src/screens/DashboardScreen';
import DeafScreen from './src/screens/DeafScreen';
import MuteScreen from './src/screens/MuteScreen';
import BlindScreen from './src/screens/BlindScreen';
import NormalUserScreen from './src/screens/NormalUserScreen';

const Tab = createBottomTabNavigator();

export default function App() {
    return (
        <SafeAreaProvider>
            <NavigationContainer>
                <Tab.Navigator
                    screenOptions={({ route }) => ({
                        headerStyle: { backgroundColor: '#1A1A2E' },
                        headerTintColor: '#FFD700',
                        tabBarStyle: { backgroundColor: '#1A1A2E', height: 60 },
                        tabBarActiveTintColor: '#E94560',
                        tabBarInactiveTintColor: '#B8CBD0',
                        tabBarIcon: ({ focused, color, size }) => {
                            let iconName;
                            if (route.name === 'Home') iconName = focused ? 'home' : 'home-outline';
                            else if (route.name === 'Normal') iconName = focused ? 'person' : 'person-outline';
                            else if (route.name === 'Blind') iconName = focused ? 'eye-off' : 'eye-off-outline';
                            else if (route.name === 'Deaf') iconName = focused ? 'ear' : 'ear-outline';
                            else if (route.name === 'Mute') iconName = focused ? 'mic-off' : 'mic-off-outline';
                            return <Ionicons name={iconName} size={size} color={color} />;
                        },
                    })}
                >
                    <Tab.Screen name="Home" component={DashboardScreen} />
                    <Tab.Screen name="Normal" component={NormalUserScreen} />
                    <Tab.Screen name="Blind" component={BlindScreen} />
                    <Tab.Screen name="Deaf" component={DeafScreen} />
                    <Tab.Screen name="Mute" component={MuteScreen} />
                </Tab.Navigator>
            </NavigationContainer>
        </SafeAreaProvider>
    );
}