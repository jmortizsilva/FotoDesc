import React, {useEffect, useState} from 'react';
import {
  View,
  FlatList,
  Image,
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  Alert,
  AccessibilityInfo,
} from 'react-native';
import PhotoMetadataManager, {PhotoAsset} from '../modules/PhotoMetadataManager';

type FilterType = 'all' | 'with-description' | 'without-description';

const GalleryScreen = ({navigation}: any) => {
  const [photos, setPhotos] = useState<PhotoAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FilterType>('all');

  useEffect(() => {
    requestPermissionAndLoadPhotos();
  }, []);

  useEffect(() => {
    loadPhotosByFilter();
  }, [filter]);

  const requestPermissionAndLoadPhotos = async () => {
    try {
      const hasPermission = await PhotoMetadataManager.requestPhotoLibraryPermission();
      if (!hasPermission) {
        Alert.alert(
          'Permiso necesario',
          'FotoDesc necesita acceso a tu galería para funcionar',
        );
        return;
      }
      await loadPhotosByFilter();
    } catch (error) {
      Alert.alert('Error', 'No se pudo acceder a la galería');
      setLoading(false);
    }
  };

  const loadPhotosByFilter = async () => {
    setLoading(true);
    try {
      let loadedPhotos: PhotoAsset[] = [];
      
      switch (filter) {
        case 'all':
          loadedPhotos = await PhotoMetadataManager.getAllPhotos();
          break;
        case 'with-description':
          loadedPhotos = await PhotoMetadataManager.getPhotosWithDescription();
          break;
        case 'without-description':
          loadedPhotos = await PhotoMetadataManager.getPhotosWithoutDescription();
          break;
      }
      
      setPhotos(loadedPhotos);
    } catch (error) {
      Alert.alert('Error', 'Error al cargar las fotos');
    } finally {
      setLoading(false);
    }
  };

  const renderPhoto = ({item}: {item: PhotoAsset}) => {
    const accessibilityLabel = item.hasDescription
      ? `Foto: ${item.imageDescription || 'Sin descripción'}. Tiene descripción añadida.`
      : `Foto: ${item.filename}. Sin descripción. Toca dos veces para añadir.`;

    return (
      <TouchableOpacity
        style={styles.photoContainer}
        onPress={() => navigation.navigate('PhotoDetail', {photo: item})}
        accessibilityLabel={accessibilityLabel}
        accessibilityRole="imagebutton">
        <Image source={{uri: item.uri}} style={styles.photo} />
        {item.hasDescription && (
          <View style={styles.badge} accessibilityElementsHidden>
            <Text style={styles.badgeText}>✓</Text>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  const FilterButton = ({
    type,
    label,
  }: {
    type: FilterType;
    label: string;
  }) => (
    <TouchableOpacity
      style={[styles.filterButton, filter === type && styles.filterButtonActive]}
      onPress={() => setFilter(type)}
      accessibilityLabel={`Filtrar: ${label}`}
      accessibilityRole="button"
      accessibilityState={{selected: filter === type}}>
      <Text
        style={[
          styles.filterButtonText,
          filter === type && styles.filterButtonTextActive,
        ]}>
        {label}
      </Text>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Cargando fotos...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.filterContainer}>
        <FilterButton type="all" label="Todas" />
        <FilterButton type="with-description" label="Con descripción" />
        <FilterButton type="without-description" label="Sin descripción" />
      </View>

      {photos.length === 0 ? (
        <View style={styles.centered}>
          <Text style={styles.emptyText}>No hay fotos en esta categoría</Text>
        </View>
      ) : (
        <FlatList
          data={photos}
          renderItem={renderPhoto}
          keyExtractor={item => item.id}
          numColumns={3}
          contentContainerStyle={styles.grid}
          accessibilityLabel={`Galería con ${photos.length} fotos`}
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  filterContainer: {
    flexDirection: 'row',
    padding: 10,
    backgroundColor: '#f5f5f5',
    borderBottomWidth: 1,
    borderBottomColor: '#ddd',
  },
  filterButton: {
    flex: 1,
    padding: 10,
    marginHorizontal: 5,
    borderRadius: 8,
    backgroundColor: '#fff',
    alignItems: 'center',
  },
  filterButtonActive: {
    backgroundColor: '#007AFF',
  },
  filterButtonText: {
    fontSize: 12,
    color: '#333',
    fontWeight: '600',
  },
  filterButtonTextActive: {
    color: '#fff',
  },
  grid: {
    padding: 5,
  },
  photoContainer: {
    flex: 1 / 3,
    aspectRatio: 1,
    padding: 2,
    position: 'relative',
  },
  photo: {
    width: '100%',
    height: '100%',
    borderRadius: 4,
  },
  badge: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: '#34C759',
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  badgeText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
  },
});

export default GalleryScreen;
