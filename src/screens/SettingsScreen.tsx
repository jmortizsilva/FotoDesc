import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import OpenAIService from '../services/OpenAIService';

const SettingsScreen = () => {
  const [apiKey, setApiKey] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const key = await OpenAIService.loadApiKey();
      if (key) {
        setApiKey(key);
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveApiKey = async () => {
    if (!apiKey.trim()) {
      Alert.alert('Error', 'Por favor ingresa una API Key válida');
      return;
    }

    setIsSaving(true);
    try {
      await OpenAIService.saveApiKey(apiKey.trim());
      Alert.alert('Guardado', 'API Key guardada correctamente');
    } catch (error) {
      Alert.alert('Error', 'No se pudo guardar la API Key');
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestApiKey = async () => {
    if (!apiKey.trim()) {
      Alert.alert('Error', 'Por favor ingresa una API Key primero');
      return;
    }

    setIsTesting(true);
    try {
      await OpenAIService.saveApiKey(apiKey.trim());
      const isValid = await OpenAIService.testApiKey();
      
      if (isValid) {
        Alert.alert('✅ Conexión exitosa', 'La API Key es válida');
      } else {
        Alert.alert('❌ Error', 'La API Key no es válida');
      }
    } catch (error) {
      Alert.alert('Error', 'No se pudo verificar la API Key');
    } finally {
      setIsTesting(false);
    }
  };

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>OpenAI API Key</Text>
        <Text style={styles.description}>
          Para usar la función de generación automática de descripciones,
          necesitas una API Key de OpenAI.
        </Text>
        
        <TextInput
          style={styles.input}
          value={apiKey}
          onChangeText={setApiKey}
          placeholder="sk-..."
          placeholderTextColor="#999"
          secureTextEntry
          autoCapitalize="none"
          autoCorrect={false}
          accessibilityLabel="Campo de API Key de OpenAI"
        />

        <View style={styles.buttonContainer}>
          <TouchableOpacity
            style={[styles.button, styles.buttonPrimary]}
            onPress={handleSaveApiKey}
            disabled={isSaving}
            accessibilityLabel="Guardar API Key"
            accessibilityRole="button">
            {isSaving ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Guardar</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, styles.buttonSecondary]}
            onPress={handleTestApiKey}
            disabled={isTesting}
            accessibilityLabel="Probar conexión con OpenAI"
            accessibilityRole="button">
            {isTesting ? (
              <ActivityIndicator color="#007AFF" />
            ) : (
              <Text style={styles.buttonTextSecondary}>Probar</Text>
            )}
          </TouchableOpacity>
        </View>

        <Text style={styles.helpText}>
          📝 Obtén tu API Key en: https://platform.openai.com/api-keys
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Acerca de FotoDesc</Text>
        <Text style={styles.description}>
          FotoDesc te permite añadir descripciones accesibles a tus fotos
          guardándolas directamente en los metadatos EXIF (ImageDescription).
        </Text>
        <Text style={styles.description}>
          Las descripciones son leídas por VoiceOver tanto en esta aplicación
          como en la app Fotos nativa de iOS.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Accesibilidad</Text>
        <Text style={styles.description}>
          ✅ Compatible con VoiceOver{'\n'}
          ✅ Navegación por gestos{'\n'}
          ✅ Etiquetas descriptivas{'\n'}
          ✅ Feedback auditivo
        </Text>
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>Versión 1.0.0</Text>
        <Text style={styles.footerText}>
          Desarrollado con ❤️ para accesibilidad
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  content: {
    padding: 20,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  section: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  description: {
    fontSize: 16,
    color: '#666',
    lineHeight: 24,
    marginBottom: 15,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 15,
  },
  buttonContainer: {
    flexDirection: 'row',
    gap: 10,
  },
  button: {
    flex: 1,
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 50,
  },
  buttonPrimary: {
    backgroundColor: '#007AFF',
  },
  buttonSecondary: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  buttonTextSecondary: {
    color: '#007AFF',
    fontSize: 16,
    fontWeight: '600',
  },
  helpText: {
    fontSize: 14,
    color: '#666',
    marginTop: 15,
    fontStyle: 'italic',
  },
  footer: {
    alignItems: 'center',
    marginTop: 20,
    paddingVertical: 20,
  },
  footerText: {
    fontSize: 14,
    color: '#999',
    marginVertical: 2,
  },
});

export default SettingsScreen;
