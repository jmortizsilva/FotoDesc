import React, {useState, useEffect} from 'react';
import {
  View,
  Image,
  TextInput,
  TouchableOpacity,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import PhotoMetadataManager, {PhotoAsset} from '../modules/PhotoMetadataManager';
import OpenAIService from '../services/OpenAIService';

const PhotoDetailScreen = ({route, navigation}: any) => {
  const {photo: initialPhoto} = route.params as {photo: PhotoAsset};
  const [photo, setPhoto] = useState<PhotoAsset>(initialPhoto);
  const [description, setDescription] = useState(initialPhoto.imageDescription || '');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    // Cargar la descripción actualizada al entrar
    loadDescription();
  }, []);

  const loadDescription = async () => {
    try {
      const desc = await PhotoMetadataManager.getImageDescription(photo.id);
      if (desc) {
        setDescription(desc);
      }
    } catch (error) {
      console.error('Error loading description:', error);
    }
  };

  const handleSaveDescription = async () => {
    if (!description.trim()) {
      Alert.alert('Error', 'La descripción no puede estar vacía');
      return;
    }

    setIsSaving(true);
    try {
      const success = await PhotoMetadataManager.setImageDescription(
        photo.id,
        description.trim(),
      );

      if (success) {
        Alert.alert(
          'Guardado',
          'La descripción se ha guardado correctamente',
          [
            {
              text: 'OK',
              onPress: () => navigation.goBack(),
            },
          ],
        );
      } else {
        Alert.alert('Error', 'No se pudo guardar la descripción');
      }
    } catch (error) {
      Alert.alert('Error', 'Error al guardar la descripción');
    } finally {
      setIsSaving(false);
    }
  };

  const handleGenerateWithAI = async () => {
    Alert.alert(
      'Generar con IA',
      '¿Deseas generar una descripción automática con OpenAI? Esto consumirá créditos de tu API.',
      [
        {text: 'Cancelar', style: 'cancel'},
        {text: 'Generar', onPress: generateDescription},
      ],
    );
  };

  const generateDescription = async () => {
    setIsGenerating(true);
    try {
      // Obtener la imagen en base64 (tamaño máximo 1MB para la API)
      const imageBase64 = await PhotoMetadataManager.getImageBase64(
        photo.id,
        1024,
      );

      const generatedDesc = await OpenAIService.generateImageDescription(
        imageBase64,
      );

      setDescription(generatedDesc);
      Alert.alert(
        'Descripción generada',
        'Puedes revisar y editar la descripción antes de guardar',
      );
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Error al generar descripción');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDeletePhoto = () => {
    Alert.alert(
      'Eliminar foto',
      '¿Estás seguro de que deseas eliminar esta foto? Esta acción no se puede deshacer.',
      [
        {text: 'Cancelar', style: 'cancel'},
        {
          text: 'Eliminar',
          style: 'destructive',
          onPress: confirmDelete,
        },
      ],
    );
  };

  const confirmDelete = async () => {
    try {
      const success = await PhotoMetadataManager.deletePhoto(photo.id);
      if (success) {
        Alert.alert('Eliminada', 'La foto se ha eliminado correctamente', [
          {
            text: 'OK',
            onPress: () => navigation.goBack(),
          },
        ]);
      } else {
        Alert.alert('Error', 'No se pudo eliminar la foto');
      }
    } catch (error) {
      Alert.alert('Error', 'Error al eliminar la foto');
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Image
          source={{uri: photo.uri}}
          style={styles.image}
          accessibilityLabel={description || 'Imagen sin descripción'}
        />

        <View style={styles.infoContainer}>
          <Text style={styles.label}>Nombre del archivo:</Text>
          <Text style={styles.value}>{photo.filename}</Text>

          <Text style={styles.label}>Fecha:</Text>
          <Text style={styles.value}>
            {new Date(photo.creationDate).toLocaleDateString('es-ES')}
          </Text>

          <Text style={styles.label}>Descripción accesible:</Text>
          <TextInput
            style={styles.textInput}
            multiline
            numberOfLines={4}
            value={description}
            onChangeText={setDescription}
            placeholder="Añade una descripción para VoiceOver..."
            placeholderTextColor="#999"
            accessibilityLabel="Campo de descripción"
            accessibilityHint="Escribe la descripción de la imagen para accesibilidad"
          />

          <View style={styles.buttonContainer}>
            <TouchableOpacity
              style={[styles.button, styles.buttonPrimary]}
              onPress={handleSaveDescription}
              disabled={isSaving}
              accessibilityLabel="Guardar descripción"
              accessibilityRole="button">
              {isSaving ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>💾 Guardar</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.button, styles.buttonSecondary]}
              onPress={handleGenerateWithAI}
              disabled={isGenerating}
              accessibilityLabel="Generar descripción con inteligencia artificial"
              accessibilityRole="button">
              {isGenerating ? (
                <ActivityIndicator color="#007AFF" />
              ) : (
                <Text style={styles.buttonTextSecondary}>🤖 Generar con IA</Text>
              )}
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={[styles.button, styles.buttonDanger]}
            onPress={handleDeletePhoto}
            accessibilityLabel="Eliminar foto de la galería"
            accessibilityRole="button">
            <Text style={styles.buttonText}>🗑️ Eliminar foto</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  scrollContent: {
    paddingBottom: 20,
  },
  image: {
    width: '100%',
    height: 300,
    resizeMode: 'contain',
    backgroundColor: '#f5f5f5',
  },
  infoContainer: {
    padding: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    marginTop: 15,
    marginBottom: 5,
  },
  value: {
    fontSize: 16,
    color: '#333',
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    minHeight: 100,
    textAlignVertical: 'top',
    marginTop: 5,
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 20,
    gap: 10,
  },
  button: {
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 50,
  },
  buttonPrimary: {
    backgroundColor: '#007AFF',
    flex: 1,
  },
  buttonSecondary: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#007AFF',
    flex: 1,
  },
  buttonDanger: {
    backgroundColor: '#FF3B30',
    marginTop: 10,
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
});

export default PhotoDetailScreen;
