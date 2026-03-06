import React, {useEffect, useRef, useState} from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import PhotoMetadataManager, {
  PhotoAsset,
  PhotoLocation,
} from '../modules/PhotoMetadataManager';

interface SuggestionItem {
  address: string;
  latitude: number;
  longitude: number;
}

const LocationEditorScreen = ({route, navigation}: any) => {
  const {photo} = route.params as {photo: PhotoAsset};

  const [address, setAddress] = useState('');
  const [latitude, setLatitude] = useState(
    photo.locationLatitude?.toString() || '',
  );
  const [longitude, setLongitude] = useState(
    photo.locationLongitude?.toString() || '',
  );

  const [isLoadingLocation, setIsLoadingLocation] = useState(true);
  const [isPreparingAsset, setIsPreparingAsset] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isSearchingAddress, setIsSearchingAddress] = useState(false);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([]);
  const [isAddressFocused, setIsAddressFocused] = useState(false);

  const suggestionsTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const formatCoordinates = (lat: number, lon: number) =>
    `${lat.toFixed(5)}, ${lon.toFixed(5)}`;

  useEffect(() => {
    prepareAssetForEditing();
    loadCurrentLocation();

    return () => {
      if (suggestionsTimerRef.current) {
        clearTimeout(suggestionsTimerRef.current);
      }
    };
  }, []);

  const prepareAssetForEditing = async () => {
    setIsPreparingAsset(true);
    try {
      await PhotoMetadataManager.prepareAssetForEditing(photo.id);
    } catch {
      Alert.alert(
        'No se pudo preparar la foto',
        'No se pudo descargar/preparar la foto para edición. Comprueba la conexión e inténtalo de nuevo.',
      );
    } finally {
      setIsPreparingAsset(false);
    }
  };

  const loadCurrentLocation = async () => {
    setIsLoadingLocation(true);
    try {
      const current = (await PhotoMetadataManager.getPhotoLocation(
        photo.id,
      )) as PhotoLocation | null;

      if (!current) {
        setAddress('Sin datos de ubicación');
        setLatitude('');
        setLongitude('');
        return;
      }

      setLatitude(String(current.latitude));
      setLongitude(String(current.longitude));

      const reverse = await PhotoMetadataManager.reverseGeocodeLocation(
        current.latitude,
        current.longitude,
      );
      setAddress(reverse || formatCoordinates(current.latitude, current.longitude));
    } catch {
      setAddress('No se pudo leer la ubicación');
    } finally {
      setIsLoadingLocation(false);
    }
  };

  const fetchSuggestions = async (query: string) => {
    const q = query.trim();
    if (q.length < 3) {
      setSuggestions([]);
      return;
    }

    setIsLoadingSuggestions(true);
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=jsonv2&addressdetails=1&limit=6&q=${encodeURIComponent(
          q,
        )}`,
        {
          headers: {
            Accept: 'application/json',
            'Accept-Language': 'es',
            'User-Agent': 'FotoDesc/1.0',
          },
        },
      );

      if (!response.ok) {
        setSuggestions([]);
        return;
      }

      const data = (await response.json()) as Array<{
        display_name?: string;
        lat?: string;
        lon?: string;
      }>;

      const normalized: SuggestionItem[] = data
        .map(item => ({
          address: item.display_name || '',
          latitude: Number(item.lat),
          longitude: Number(item.lon),
        }))
        .filter(
          item =>
            item.address.length > 0 &&
            !Number.isNaN(item.latitude) &&
            !Number.isNaN(item.longitude),
        );

      setSuggestions(normalized);
    } catch {
      setSuggestions([]);
    } finally {
      setIsLoadingSuggestions(false);
    }
  };

  const handleAddressChange = (text: string) => {
    setAddress(text);
    if (suggestionsTimerRef.current) {
      clearTimeout(suggestionsTimerRef.current);
    }

    suggestionsTimerRef.current = setTimeout(() => {
      fetchSuggestions(text);
    }, 300);
  };

  const applySuggestion = (item: SuggestionItem) => {
    setAddress(item.address);
    setLatitude(String(item.latitude));
    setLongitude(String(item.longitude));
    setSuggestions([]);
    setIsAddressFocused(false);
  };

  const handleSearchAddress = async () => {
    if (isPreparingAsset) {
      Alert.alert('Espera', 'La foto todavía se está preparando para edición.');
      return;
    }

    const addressText = address.trim();
    if (!addressText) {
      Alert.alert('Dirección vacía', 'Escribe una dirección para buscar');
      return;
    }

    setIsSearchingAddress(true);
    try {
      const geocoded = await PhotoMetadataManager.geocodeAddress(addressText);
      setLatitude(String(geocoded.latitude));
      setLongitude(String(geocoded.longitude));
      if (geocoded.address) {
        setAddress(geocoded.address);
      }
      setSuggestions([]);
    } catch {
      Alert.alert('Error', 'No se pudo encontrar la dirección');
    } finally {
      setIsSearchingAddress(false);
    }
  };

  const handleClearLocation = async () => {
    if (isPreparingAsset) {
      Alert.alert('Espera', 'La foto todavía se está preparando para edición.');
      return;
    }

    setIsSaving(true);
    try {
      await PhotoMetadataManager.setPhotoLocation(photo.id, null, null);
      Alert.alert('Guardado', 'La localización se ha eliminado', [
        {text: 'OK', onPress: () => navigation.goBack()},
      ]);
    } catch {
      Alert.alert('Error', 'No se pudo eliminar la localización');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveLocation = async () => {
    if (isPreparingAsset) {
      Alert.alert('Espera', 'La foto todavía se está preparando para edición.');
      return;
    }

    const lat = Number(latitude.trim());
    const lon = Number(longitude.trim());
    const addressText = address.trim();

    if (!addressText && !latitude.trim() && !longitude.trim()) {
      await handleClearLocation();
      return;
    }

    let finalLat = lat;
    let finalLon = lon;

    if ((Number.isNaN(finalLat) || Number.isNaN(finalLon)) && addressText) {
      setIsSearchingAddress(true);
      try {
        const geocoded = await PhotoMetadataManager.geocodeAddress(addressText);
        finalLat = geocoded.latitude;
        finalLon = geocoded.longitude;
        setLatitude(String(finalLat));
        setLongitude(String(finalLon));
        if (geocoded.address) {
          setAddress(geocoded.address);
        }
      } catch {
        Alert.alert('Error', 'No se pudo localizar la dirección indicada');
        setIsSearchingAddress(false);
        return;
      } finally {
        setIsSearchingAddress(false);
      }
    }

    if (
      Number.isNaN(finalLat) ||
      Number.isNaN(finalLon) ||
      finalLat < -90 ||
      finalLat > 90 ||
      finalLon < -180 ||
      finalLon > 180
    ) {
      Alert.alert(
        'Error',
        'Introduce una latitud válida (-90 a 90) y una longitud válida (-180 a 180)',
      );
      return;
    }

    setIsSaving(true);
    try {
      await PhotoMetadataManager.setPhotoLocation(photo.id, finalLat, finalLon);
      Alert.alert('Guardado', 'La localización se ha guardado correctamente', [
        {text: 'OK', onPress: () => navigation.goBack()},
      ]);
    } catch {
      Alert.alert('Error', 'No se pudo guardar la localización en la foto original');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode={Platform.OS === 'ios' ? 'interactive' : 'on-drag'}>
        <Text style={styles.title}>Editar ubicación</Text>

        {(isLoadingLocation || isPreparingAsset) ? (
          <View style={styles.loadingBox}>
            <ActivityIndicator color="#007AFF" />
            <Text style={styles.loadingText}>
              {isPreparingAsset
                ? 'Preparando foto para edición...'
                : 'Cargando ubicación actual...'}
            </Text>
          </View>
        ) : null}

        <Text style={styles.label}>Dirección</Text>
        <TextInput
          style={styles.input}
          value={address}
          onChangeText={handleAddressChange}
          onFocus={() => setIsAddressFocused(true)}
          onBlur={() => setTimeout(() => setIsAddressFocused(false), 180)}
          placeholder="Escribe una dirección"
          editable={!isPreparingAsset}
          accessibilityLabel="Dirección"
        />

        {isAddressFocused && (
          <View style={styles.suggestionsContainer}>
            {isLoadingSuggestions ? (
              <Text style={styles.suggestionsInfo}>Buscando sugerencias...</Text>
            ) : suggestions.length > 0 ? (
              suggestions.map((item, idx) => (
                <TouchableOpacity
                  key={`${item.latitude}-${item.longitude}-${idx}`}
                  style={styles.suggestionRow}
                  onPress={() => applySuggestion(item)}
                  accessibilityRole="button"
                  accessibilityLabel={item.address}>
                  <Text style={styles.suggestionText}>{item.address}</Text>
                </TouchableOpacity>
              ))
            ) : address.trim().length >= 3 ? (
              <Text style={styles.suggestionsInfo}>
                No hay sugerencias para esta búsqueda
              </Text>
            ) : null}
          </View>
        )}

        <TouchableOpacity
          style={[styles.button, styles.secondaryButton]}
          onPress={handleSearchAddress}
          disabled={isSearchingAddress || isPreparingAsset}
          accessibilityRole="button"
            accessibilityLabel="Buscar dirección">
          {isSearchingAddress ? (
            <ActivityIndicator color="#007AFF" />
          ) : (
            <Text style={styles.secondaryButtonText}>Buscar dirección</Text>
          )}
        </TouchableOpacity>

        <Text style={styles.label}>Coordenadas (opcional)</Text>
        <View style={styles.row}>
          <TextInput
            style={[styles.input, styles.rowInput]}
            value={latitude}
            onChangeText={setLatitude}
            placeholder="Latitud"
            keyboardType="decimal-pad"
            editable={!isPreparingAsset}
            accessibilityLabel="Latitud"
          />
          <TextInput
            style={[styles.input, styles.rowInput]}
            value={longitude}
            onChangeText={setLongitude}
            placeholder="Longitud"
            keyboardType="decimal-pad"
            editable={!isPreparingAsset}
            accessibilityLabel="Longitud"
          />
        </View>

        <TouchableOpacity
          style={[styles.button, styles.primaryButton]}
          onPress={handleSaveLocation}
          disabled={isSaving || isPreparingAsset}
          accessibilityRole="button"
          accessibilityLabel="Guardar localización">
          {isSaving ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.primaryButtonText}>Guardar localización</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.button, styles.dangerButton]}
          onPress={handleClearLocation}
          disabled={isSaving || isPreparingAsset}
          accessibilityRole="button"
          accessibilityLabel="Eliminar localización">
          <Text style={styles.primaryButtonText}>Eliminar localización</Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    padding: 20,
    paddingBottom: 30,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#222',
    marginBottom: 16,
  },
  loadingBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  loadingText: {
    color: '#666',
    fontSize: 14,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    marginBottom: 6,
    marginTop: 10,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    minHeight: 50,
    backgroundColor: '#fff',
  },
  row: {
    flexDirection: 'row',
    gap: 10,
  },
  rowInput: {
    flex: 1,
  },
  suggestionsContainer: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    marginTop: 8,
    overflow: 'hidden',
  },
  suggestionRow: {
    paddingHorizontal: 12,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  suggestionText: {
    color: '#222',
    fontSize: 15,
  },
  suggestionsInfo: {
    color: '#666',
    fontSize: 14,
    paddingHorizontal: 12,
    paddingVertical: 12,
  },
  button: {
    marginTop: 12,
    minHeight: 50,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 12,
  },
  primaryButton: {
    backgroundColor: '#007AFF',
  },
  secondaryButton: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  dangerButton: {
    backgroundColor: '#FF3B30',
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButtonText: {
    color: '#007AFF',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default LocationEditorScreen;
