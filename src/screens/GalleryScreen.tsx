import React, {useEffect, useMemo, useRef, useState} from 'react';
import {
  View,
  FlatList,
  Image,
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  Alert,
  ActionSheetIOS,
  Platform,
  Share,
} from 'react-native';
import {useFocusEffect} from '@react-navigation/native';
import PhotoMetadataManager, {
  PhotoAsset,
  PhotoFilterType,
  PhotoPageResult,
} from '../modules/PhotoMetadataManager';

type FilterType = PhotoFilterType;
type DateRangeType = 'all-time' | 'last-7-days' | 'last-30-days' | 'this-year';

interface CacheEntry {
  items: PhotoAsset[];
  nextOffset: number;
  hasMore: boolean;
}

const PAGE_SIZE = 60;
const photoCache: Partial<Record<string, CacheEntry>> = {};

const GalleryScreen = ({navigation}: any) => {
  const [photos, setPhotos] = useState<PhotoAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [filter, setFilter] = useState<FilterType>('all');
  const [dateRange, setDateRange] = useState<DateRangeType>('all-time');
  const [isLoadingSlow, setIsLoadingSlow] = useState(false);
  const [hasPermission, setHasPermission] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [nextOffset, setNextOffset] = useState(0);

  const slowLoadingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const filterOptions: Array<{type: FilterType; label: string}> = [
    {type: 'all', label: 'Todas'},
    {type: 'with-description', label: 'Con descripción'},
    {type: 'without-description', label: 'Sin descripción'},
  ];

  const dateRangeOptions: Array<{type: DateRangeType; label: string}> = [
    {type: 'all-time', label: 'Todo el tiempo'},
    {type: 'last-7-days', label: 'Últimos 7 días'},
    {type: 'last-30-days', label: 'Últimos 30 días'},
    {type: 'this-year', label: 'Este año'},
  ];

  const cacheKey = useMemo(() => `${filter}|${dateRange}`, [filter, dateRange]);

  useEffect(() => {
    requestPermission();
  }, []);

  useEffect(() => {
    return () => {
      if (slowLoadingTimerRef.current) {
        clearTimeout(slowLoadingTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!hasPermission) {
      return;
    }
    loadInitialPage({preferCache: true});
  }, [hasPermission, cacheKey]);

  useFocusEffect(
    React.useCallback(() => {
      if (!hasPermission) {
        return;
      }
      loadInitialPage({preferCache: true});
    }, [hasPermission, cacheKey]),
  );

  const requestPermission = async () => {
    try {
      const granted = await PhotoMetadataManager.requestPhotoLibraryPermission();
      if (!granted) {
        Alert.alert(
          'Permiso necesario',
          'FotoDesc necesita acceso a tu galería para funcionar',
        );
        setLoading(false);
        return;
      }
      setHasPermission(true);
    } catch {
      Alert.alert('Error', 'No se pudo acceder a la galería');
      setLoading(false);
    }
  };

  const getDateRangeBoundaries = () => {
    const now = new Date();

    switch (dateRange) {
      case 'last-7-days': {
        const start = new Date(now);
        start.setDate(start.getDate() - 7);
        return {startDateIso: start.toISOString(), endDateIso: now.toISOString()};
      }
      case 'last-30-days': {
        const start = new Date(now);
        start.setDate(start.getDate() - 30);
        return {startDateIso: start.toISOString(), endDateIso: now.toISOString()};
      }
      case 'this-year': {
        const start = new Date(now.getFullYear(), 0, 1);
        return {startDateIso: start.toISOString(), endDateIso: now.toISOString()};
      }
      case 'all-time':
      default:
        return {startDateIso: null, endDateIso: null};
    }
  };

  const loadPageFromNative = async (offset: number): Promise<PhotoPageResult> => {
    const {startDateIso, endDateIso} = getDateRangeBoundaries();
    return PhotoMetadataManager.getPhotosPage(
      offset,
      PAGE_SIZE,
      filter,
      startDateIso,
      endDateIso,
    );
  };

  const startSlowLoadingTimer = () => {
    setIsLoadingSlow(false);
    if (slowLoadingTimerRef.current) {
      clearTimeout(slowLoadingTimerRef.current);
    }
    slowLoadingTimerRef.current = setTimeout(() => {
      setIsLoadingSlow(true);
    }, 2500);
  };

  const stopSlowLoadingTimer = () => {
    if (slowLoadingTimerRef.current) {
      clearTimeout(slowLoadingTimerRef.current);
      slowLoadingTimerRef.current = null;
    }
    setIsLoadingSlow(false);
  };

  const loadInitialPage = async ({preferCache}: {preferCache: boolean}) => {
    startSlowLoadingTimer();

    const cached = photoCache[cacheKey];
    if (preferCache && cached && cached.items.length > 0) {
      setPhotos(cached.items);
      setNextOffset(cached.nextOffset);
      setHasMore(cached.hasMore);
      setLoading(false);
      setRefreshing(true);
    } else {
      setLoading(true);
      setRefreshing(false);
      setPhotos([]);
      setNextOffset(0);
      setHasMore(false);
    }

    try {
      const page = await loadPageFromNative(0);
      setPhotos(page.items);
      setNextOffset(page.nextOffset);
      setHasMore(page.hasMore);
      photoCache[cacheKey] = page;
    } catch {
      Alert.alert('Error', 'Error al cargar las fotos');
    } finally {
      setLoading(false);
      setRefreshing(false);
      stopSlowLoadingTimer();
    }
  };

  const loadMorePhotos = async () => {
    if (loading || refreshing || loadingMore || !hasMore) {
      return;
    }

    setLoadingMore(true);
    try {
      const page = await loadPageFromNative(nextOffset);
      const merged = [...photos];
      const seen = new Set(merged.map(item => item.id));

      page.items.forEach(item => {
        if (!seen.has(item.id)) {
          merged.push(item);
          seen.add(item.id);
        }
      });

      setPhotos(merged);
      setNextOffset(page.nextOffset);
      setHasMore(page.hasMore);
      photoCache[cacheKey] = {
        items: merged,
        nextOffset: page.nextOffset,
        hasMore: page.hasMore,
      };
    } catch {
      Alert.alert('Error', 'No se pudieron cargar más fotos');
    } finally {
      setLoadingMore(false);
    }
  };

  const handleManualRefresh = async () => {
    await loadInitialPage({preferCache: false});
  };

  const formatDateTimeForAccessibility = (isoDate: string) => {
    const date = new Date(isoDate);
    return date.toLocaleString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const openFilterSelector = () => {
    const currentLabel =
      filterOptions.find(option => option.type === filter)?.label ?? 'Todas';

    if (Platform.OS === 'ios') {
      ActionSheetIOS.showActionSheetWithOptions(
        {
          title: 'Filtrar fotos',
          options: [...filterOptions.map(option => option.label), 'Cancelar'],
          cancelButtonIndex: filterOptions.length,
          message: `Filtro actual: ${currentLabel}`,
        },
        (buttonIndex: number) => {
          if (buttonIndex < filterOptions.length) {
            setFilter(filterOptions[buttonIndex].type);
          }
        },
      );
      return;
    }

    Alert.alert('Filtrar fotos', `Filtro actual: ${currentLabel}`, [
      ...filterOptions.map(option => ({
        text: option.label,
        onPress: () => setFilter(option.type),
      })),
      {text: 'Cancelar', style: 'cancel'},
    ]);
  };

  const openDateSelector = () => {
    const currentLabel =
      dateRangeOptions.find(option => option.type === dateRange)?.label ??
      'Todo el tiempo';

    if (Platform.OS === 'ios') {
      ActionSheetIOS.showActionSheetWithOptions(
        {
          title: 'Filtrar por fecha',
          options: [...dateRangeOptions.map(option => option.label), 'Cancelar'],
          cancelButtonIndex: dateRangeOptions.length,
          message: `Rango actual: ${currentLabel}`,
        },
        (buttonIndex: number) => {
          if (buttonIndex < dateRangeOptions.length) {
            setDateRange(dateRangeOptions[buttonIndex].type);
          }
        },
      );
      return;
    }

    Alert.alert('Filtrar por fecha', `Rango actual: ${currentLabel}`, [
      ...dateRangeOptions.map(option => ({
        text: option.label,
        onPress: () => setDateRange(option.type),
      })),
      {text: 'Cancelar', style: 'cancel'},
    ]);
  };

  const handleSharePhoto = async (item: PhotoAsset) => {
    try {
      const originalUri =
        await PhotoMetadataManager.getOriginalImageURLForSharing(item.id);

      await Share.share({
        title: item.filename,
        url: originalUri,
      });
    } catch {
      Alert.alert('Error', 'No se pudo compartir la foto original');
    }
  };

  const handleDeletePhoto = (item: PhotoAsset) => {
    Alert.alert('Eliminar foto', '¿Quieres eliminar esta foto de la galería?', [
      {text: 'Cancelar', style: 'cancel'},
      {
        text: 'Eliminar',
        style: 'destructive',
        onPress: async () => {
          try {
            await PhotoMetadataManager.deletePhoto(item.id);
            await loadInitialPage({preferCache: false});
          } catch {
            Alert.alert('Error', 'No se pudo eliminar la foto');
          }
        },
      },
    ]);
  };

  const handleRemoveDescription = (item: PhotoAsset) => {
    Alert.alert(
      'Eliminar descripción',
      '¿Quieres eliminar la descripción de esta foto?',
      [
        {text: 'Cancelar', style: 'cancel'},
        {
          text: 'Eliminar',
          style: 'destructive',
          onPress: async () => {
            try {
              await PhotoMetadataManager.setImageDescription(item.id, '');
              await loadInitialPage({preferCache: false});
            } catch {
              Alert.alert('Error', 'No se pudo eliminar la descripción');
            }
          },
        },
      ],
    );
  };

  const handlePhotoAccessibilityAction = (
    item: PhotoAsset,
    actionName?: string,
  ) => {
    if (actionName === 'edit-description') {
      navigation.navigate('PhotoDetail', {photo: item});
      return;
    }

    if (actionName === 'delete-photo') {
      handleDeletePhoto(item);
      return;
    }

    if (actionName === 'share-photo') {
      handleSharePhoto(item);
      return;
    }

    if (actionName === 'remove-description') {
      handleRemoveDescription(item);
    }
  };

  const renderPhoto = ({item}: {item: PhotoAsset}) => {
    const formattedDateTime = formatDateTimeForAccessibility(item.creationDate);
    const descriptionForVoiceOver =
      item.imageDescription && item.imageDescription.trim().length > 0
        ? item.imageDescription
        : 'Sin descripción';
    const hasDescription = descriptionForVoiceOver !== 'Sin descripción';

    const accessibilityLabel = hasDescription
      ? `${descriptionForVoiceOver}. ${formattedDateTime}`
      : `Sin descripción. ${formattedDateTime}`;

    return (
      <TouchableOpacity
        style={styles.photoContainer}
        onPress={() => navigation.navigate('PhotoDetail', {photo: item})}
        accessibilityActions={[
          {name: 'edit-description', label: 'Editar descripción'},
          {name: 'delete-photo', label: 'Eliminar foto'},
          {name: 'share-photo', label: 'Compartir foto'},
          {name: 'remove-description', label: 'Eliminar descripción'},
        ]}
        onAccessibilityAction={event =>
          handlePhotoAccessibilityAction(item, event.nativeEvent.actionName)
        }
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

  const renderFooter = () => {
    if (!loadingMore) {
      return null;
    }

    return (
      <View style={styles.footerLoader}>
        <ActivityIndicator size="small" color="#007AFF" />
        <Text style={styles.footerLoaderText}>Cargando más fotos...</Text>
      </View>
    );
  };

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
        <View style={styles.controlsRow}>
          <TouchableOpacity
            style={styles.filterDropdownButton}
            onPress={openFilterSelector}
            accessibilityRole="button"
            accessibilityLabel={`Filtro actual: ${
              filterOptions.find(option => option.type === filter)?.label ?? 'Todas'
            }. Toca dos veces para cambiar`}>
            <Text style={styles.filterDropdownText}>
              {filterOptions.find(option => option.type === filter)?.label ?? 'Todas'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.filterDropdownButton}
            onPress={openDateSelector}
            accessibilityRole="button"
            accessibilityLabel={`Rango actual: ${
              dateRangeOptions.find(option => option.type === dateRange)?.label ??
              'Todo el tiempo'
            }. Toca dos veces para cambiar`}>
            <Text style={styles.filterDropdownText}>
              {dateRangeOptions.find(option => option.type === dateRange)?.label ??
                'Todo el tiempo'}
            </Text>
          </TouchableOpacity>
        </View>

        {(loading || refreshing) && isLoadingSlow && (
          <View style={styles.slowLoadingNotice}>
            <ActivityIndicator size="small" color="#666" />
            <Text style={styles.slowLoadingText}>
              La carga está tardando más de lo normal...
            </Text>
          </View>
        )}
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
          refreshing={refreshing}
          onRefresh={handleManualRefresh}
          onEndReached={loadMorePhotos}
          onEndReachedThreshold={0.4}
          ListFooterComponent={renderFooter}
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
    padding: 10,
    backgroundColor: '#f5f5f5',
    borderBottomWidth: 1,
    borderBottomColor: '#ddd',
  },
  controlsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  filterDropdownButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 8,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  filterDropdownText: {
    fontSize: 14,
    color: '#333',
    fontWeight: '600',
    textAlign: 'center',
  },
  slowLoadingNotice: {
    marginTop: 10,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 8,
    backgroundColor: '#fff8e6',
    borderWidth: 1,
    borderColor: '#f1dfb3',
  },
  slowLoadingText: {
    color: '#7a6225',
    fontSize: 13,
    fontWeight: '600',
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
  footerLoader: {
    paddingVertical: 12,
    alignItems: 'center',
    gap: 6,
  },
  footerLoaderText: {
    fontSize: 12,
    color: '#666',
  },
});

export default GalleryScreen;
