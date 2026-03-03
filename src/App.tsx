import React from 'react';
import {NavigationContainer, useNavigation} from '@react-navigation/native';
import {createStackNavigator} from '@react-navigation/stack';
import {SafeAreaProvider} from 'react-native-safe-area-context';
import {TouchableOpacity, Text} from 'react-native';
import GalleryScreen from './screens/GalleryScreen';
import PhotoDetailScreen from './screens/PhotoDetailScreen';
import SettingsScreen from './screens/SettingsScreen';

const Stack = createStackNavigator();

const SettingsButton = () => {
  const navigation = useNavigation();
  return (
    <TouchableOpacity
      onPress={() => navigation.navigate('Settings' as never)}
      style={{marginRight: 15}}
      accessibilityLabel="Configuración"
      accessibilityRole="button">
      <Text style={{color: '#fff', fontSize: 18}}>⚙️</Text>
    </TouchableOpacity>
  );
};

const App = () => {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <Stack.Navigator
          initialRouteName="Gallery"
          screenOptions={{
            headerStyle: {
              backgroundColor: '#007AFF',
            },
            headerTintColor: '#fff',
            headerTitleStyle: {
              fontWeight: 'bold',
            },
          }}>
          <Stack.Screen
            name="Gallery"
            component={GalleryScreen}
            options={{
              title: 'Mis Fotos',
              headerRight: () => <SettingsButton />,
            }}
          />
          <Stack.Screen
            name="PhotoDetail"
            component={PhotoDetailScreen}
            options={{title: 'Detalle de Foto'}}
          />
          <Stack.Screen
            name="Settings"
            component={SettingsScreen}
            options={{title: 'Configuración'}}
          />
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
};

export default App;
