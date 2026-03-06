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
  InputAccessoryView,
  Share,
} from 'react-native';
import {useFocusEffect} from '@react-navigation/native';
import PhotoMetadataManager, {
  PhotoAsset,
  PhotoLocation,
} from '../modules/PhotoMetadataManager';
import OpenAIService from '../services/OpenAIService';

const PhotoDetailScreen = ({route, navigation}: any) => {
  const {photo: initialPhoto} = route.params as {photo: PhotoAsset};
  const [photo] = useState<PhotoAsset>(initialPhoto);
  const [description, setDescription] = useState(initialPhoto.imageDescription || '');
  const [address, setAddress] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isResolvingLocation, setIsResolvingLocation] = useState(false);
  const [isPreparingAsset, setIsPreparingAsset] = useState(false);
  const [saveErrorDiagnostic, setSaveErrorDiagnostic] = useState<string | null>(null);

  const descriptionAccessoryId = 'descriptionAccessory';

  const formatCoordinatesFallback = (lat: number, lon: number) =>
    `${lat.toFixed(5)}, ${lon.toFixed(5)}`;

  const buildSaveDiagnostic = (error: any) => {
    const errorCode = error?.code || 'UNKNOWN';
    const nativeMessage =
      error?.message || error?.nativeStackIOS?.[0] || 'Sin detalle nativo';

    return [
      'Diagnóstico de guardado',
      `assetId: ${photo.id}`,
      `filename: ${photo.filename}`,
      `code: ${errorCode}`,
      `message: ${nativeMessage}`,
    ].join('\n');
  };

  const resolveFriendlyAddress = async (lat: number, lon: number) => {
    setIsResolvingLocation(true);
    try {
      const reverseAddress = await PhotoMetadataManager.reverseGeocodeLocation(
        lat,
        lon,
      );
      if (reverseAddress && reverseAddress.trim().length > 0) {
        setAddress(reverseAddress);
      } else {
        setAddress(formatCoordinatesFallback(lat, lon));
      }
    } catch {
      setAddress(formatCoordinatesFallback(lat, lon));
    } finally {
      setIsResolvingLocation(false);
    }
  };

  const prepareAssetForEditing = async () => {
    setIsPreparingAsset(true);
    try {
      await PhotoMetadataManager.prepareAssetForEditing(photo.id);
    } catch (error: any) {
      const diagnostic = buildSaveDiagnostic(error);
      setSaveErrorDiagnostic(diagnostic);
      Alert.alert(
        'No se pudo preparar la foto',
        'La foto no está lista para editar metadatos. Revisa conexión y que esté descargada desde iCloud.',
      );
    } finally {
      setIsPreparingAsset(false);
    }
  };

  const handleShareDiagnostic = async () => {
    if (!saveErrorDiagnostic) {
      return;
    }

    try {
      await Share.share({
        title: 'Diagnóstico FotoDesc',
        message: saveErrorDiagnostic,
      });
    } catch {
      Alert.alert('Error', 'No se pudo compartir el diagnóstico');
    }
  };

  const loadDescription = async () => {
    try {
      const desc = await PhotoMetadataManager.getImageDescription(photo.id);
      setDescription(desc || '');
    } catch (error) {
      console.error('Error loading description:', error);
    }
  };

  const loadLocation = async () => {
    try {
      const location = (await PhotoMetadataManager.getPhotoLocation(
        photo.id,
      )) as PhotoLocation | null;

      if (location) {
        await resolveFriendlyAddress(location.latitude, location.longitude);
      } else {
        setAddress('Sin datos de ubicación');
      }
    } catch (error) {
      console.error('Error loading location:', error);
      setAddress('No se pudo leer la ubicación');
    }
  };

  useEffect(() => {
    prepareAssetForEditing();
    loadDescription();
    loadLocation();
  }, []);

  useFocusEffect(
    React.useCallback(() => {
      loadDescription();
      loadLocation();
    }, []),
  );

  const handleSaveDescription = async () => {
    if (!description.trim()) {
      Alert.alert('Error', 'La descripción no puede estar vacía');
      return;
    }

    if (isPreparingAsset) {
      Alert.alert('Espera', 'La foto todavía se está preparando para edición.');
      return;
    }

    setIsSaving(true);
    setSaveErrorDiagnostic(null);
    try {
      const success = await PhotoMetadataManager.setImageDescription(
        photo.id,
        description.trim(),
      );

      if (success) {
        Alert.alert('Guardado', 'La descripción se ha guardado correctamente', [
          {
            text: 'OK',
            onPress: () => navigation.goBack(),
          },
        ]);
      } else {
        Alert.alert('Error', 'No se pudo guardar la descripción');
      }
    } catch (error: any) {
      const errorCode = error?.code ? ` (${error.code})` : '';
      const nativeMessage =
        error?.message ||
        error?.nativeStackIOS?.[0] ||
        'Error desconocido al guardar';
      const diagnostic = buildSaveDiagnostic(error);

      console.error('Error saving description', {
        assetId: photo.id,
        filename: photo.filename,
        error,
      });

      setSaveErrorDiagnostic(diagnostic);

      Alert.alert(
        'Error al guardar',
        `No se pudo guardar la descripción en la foto original${errorCode}.\n\nDetalle: ${nativeMessage}\n\nUsa el botón "Compartir diagnóstico" para enviarme el error completo.`,
      );
    } finally {
      setIsSaving(false);
    }
  };

  const generateDescription = async () => {
    setIsGenerating(true);
    try {
      const imageBase64 = await PhotoMetadataManager.getImageBase64(photo.id, 1024);
      const generatedDesc = await OpenAIService.generateImageDescription(
        imageBase64,
      );
      setDescription(generatedDesc);
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
          onPress: async () => {
            try {
              const success = await PhotoMetadataManager.deletePhoto(photo.id);
              if (success) {
                Alert.alert('Eliminada', 'La foto se ha eliminado correctamente', [
                  {text: 'OK', onPress: () => navigation.goBack()},
                ]);
              } else {
                Alert.alert('Error', 'No se pudo eliminar la foto');
              }
            } catch {
              Alert.alert('Error', 'Error al eliminar la foto');
            }
          },
        },
      ],
    );
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode={Platform.OS === 'ios' ? 'interactive' : 'on-drag'}>
        <Image
          source={{uri: photo.uri}}
          style={styles.image}
          accessibilityLabel={
            description && description.trim().length > 0
              ? `${description}. ${new Date(
                  photo.creationDate,
                ).toLocaleString('es-ES')}`
              : `Sin descripción. ${new Date(
                  photo.creationDate,
                ).toLocaleString('es-ES')}`
          }
        />

        <View style={styles.infoContainer}>
          {(isGenerating || isResolvingLocation || isPreparingAsset) && (
            <View style={styles.waitingBox}>
              <ActivityIndicator color="#007AFF" />
              <Text style={styles.waitingText}>
                {isPreparingAsset
                  ? 'Preparando foto para edición...'
                  : isGenerating
                  ? 'Generando descripción...'
                  : 'Resolviendo ubicación...'}
              </Text>
            </View>
          )}

          {saveErrorDiagnostic && (
            <View style={styles.diagnosticBox}>
              <Text style={styles.diagnosticTitle}>Se detectó un error al guardar</Text>
              <TouchableOpacity
                style={[styles.button, styles.buttonSecondary, styles.singleButton]}
                onPress={handleShareDiagnostic}
                accessibilityRole="button"
                accessibilityLabel="Compartir diagnóstico del error de guardado">
                <Text style={styles.buttonTextSecondary}>Compartir diagnóstico</Text>
              </TouchableOpacity>
            </View>
          )}

          <Text style={styles.label}>Fecha:</Text>
          <Text style={styles.value}>
            {new Date(photo.creationDate).toLocaleString('es-ES')}
          </Text>

          <Text style={styles.label}>Ubicación:</Text>
          <Text style={styles.value}>{address || 'Sin datos de ubicación'}</Text>
          <TouchableOpacity
            style={[styles.button, styles.buttonSecondary, styles.singleButton]}
            onPress={() => navigation.navigate('LocationEditor', {photo})}
            disabled={isPreparingAsset}
            accessibilityRole="button"
            accessibilityLabel="Editar ubicación">
            <Text style={styles.buttonTextSecondary}>Editar ubicación</Text>
          </TouchableOpacity>

          <Text style={styles.label}>Descripción accesible:</Text>
          <TextInput
            style={styles.textInput}
            multiline
            numberOfLines={4}
            value={description}
            onChangeText={setDescription}
            placeholder="Añade una descripción para VoiceOver..."
            placeholderTextColor="#999"
            editable={!isPreparingAsset}
            accessibilityLabel="Campo de descripción"
            accessibilityHint="Escribe la descripción de la imagen para accesibilidad"
            inputAccessoryViewID={
              Platform.OS === 'ios' ? descriptionAccessoryId : undefined
            }
          />

          <View style={styles.buttonContainer}>
            <TouchableOpacity
              style={[styles.button, styles.buttonPrimary]}
              onPress={handleSaveDescription}
              disabled={isSaving || isPreparingAsset}
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
              onPress={generateDescription}
              disabled={isGenerating || isPreparingAsset}
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

      {Platform.OS === 'ios' && (
        <InputAccessoryView nativeID={descriptionAccessoryId}>
          <View style={styles.accessoryBar}>
            <TouchableOpacity
              style={[styles.button, styles.buttonPrimary, styles.accessoryButton]}
              onPress={handleSaveDescription}
              disabled={isSaving || isPreparingAsset}
              accessibilityLabel="Guardar descripción"
              accessibilityRole="button">
              {isSaving ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>Guardar</Text>
              )}
            </TouchableOpacity>
          </View>
        </InputAccessoryView>
      )}
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
  singleButton: {
    marginTop: 10,
  },
  waitingBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#eef6ff',
    borderWidth: 1,
    borderColor: '#cfe5ff',
    borderRadius: 8,
    padding: 10,
    marginBottom: 10,
  },
  waitingText: {
    color: '#175ea8',
    fontSize: 14,
    fontWeight: '600',
  },
  diagnosticBox: {
    marginBottom: 12,
    padding: 12,
    backgroundColor: '#FFF4F4',
    borderColor: '#F5C2C2',
    borderWidth: 1,
    borderRadius: 8,
  },
  diagnosticTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8A1C1C',
    marginBottom: 8,
  },
  accessoryBar: {
    backgroundColor: '#f2f2f7',
    borderTopWidth: 1,
    borderTopColor: '#d9d9de',
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  accessoryButton: {
    minHeight: 42,
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
