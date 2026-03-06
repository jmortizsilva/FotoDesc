import {NativeModules} from 'react-native';

const {PhotoMetadataManager} = NativeModules;

export interface PhotoAsset {
  id: string;
  uri: string;
  filename: string;
  width: number;
  height: number;
  creationDate: string;
  locationLatitude?: number | null;
  locationLongitude?: number | null;
  imageDescription?: string;
  hasDescription: boolean;
}

export interface PhotoLocation {
  latitude: number;
  longitude: number;
  address?: string;
}

export interface PhotoPageResult {
  items: PhotoAsset[];
  nextOffset: number;
  hasMore: boolean;
}

export type PhotoFilterType = 'all' | 'with-description' | 'without-description';

export interface PhotoMetadataModule {
  /**
   * Solicita permisos de acceso a la galería de fotos
   */
  requestPhotoLibraryPermission(): Promise<boolean>;

  /**
   * Obtiene todas las fotos de la galería
   */
  getAllPhotos(): Promise<PhotoAsset[]>;

  /**
   * Obtiene las fotos que tienen descripción
   */
  getPhotosWithDescription(): Promise<PhotoAsset[]>;

  /**
   * Obtiene las fotos sin descripción
   */
  getPhotosWithoutDescription(): Promise<PhotoAsset[]>;

  /**
   * Obtiene una página de fotos con filtro opcional y rango de fechas
   */
  getPhotosPage(
    offset: number,
    limit: number,
    filterType: PhotoFilterType,
    startDateIso?: string | null,
    endDateIso?: string | null,
  ): Promise<PhotoPageResult>;

  /**
   * Lee el ImageDescription de una foto específica
   */
  getImageDescription(assetId: string): Promise<string | null>;

  /**
   * Guarda el ImageDescription en una foto
   */
  setImageDescription(assetId: string, description: string): Promise<boolean>;

  /**
   * Prepara una foto para editar metadatos (descarga desde iCloud si hace falta)
   */
  prepareAssetForEditing(assetId: string): Promise<boolean>;

  /**
   * Elimina una foto de la galería
   */
  deletePhoto(assetId: string): Promise<boolean>;

  /**
   * Obtiene la imagen en base64 para enviar a IA
   */
  getImageBase64(assetId: string, maxSize: number): Promise<string>;

  /**
   * Exporta una copia de la imagen con metadatos incrustados para compartir
   */
  exportImageForSharing(assetId: string, description?: string): Promise<string>;

  /**
   * Obtiene la URL del archivo original para compartir una copia fiel
   */
  getOriginalImageURLForSharing(assetId: string): Promise<string>;

  /**
   * Obtiene la localización GPS de una foto
   */
  getPhotoLocation(assetId: string): Promise<PhotoLocation | null>;

  /**
   * Guarda o elimina la localización GPS de una foto
   */
  setPhotoLocation(
    assetId: string,
    latitude: number | null,
    longitude: number | null,
  ): Promise<boolean>;

  /**
   * Convierte coordenadas a una dirección legible
   */
  reverseGeocodeLocation(latitude: number, longitude: number): Promise<string | null>;

  /**
   * Convierte una dirección legible a coordenadas
   */
  geocodeAddress(addressText: string): Promise<PhotoLocation>;

  /**
   * Busca sugerencias de dirección mientras el usuario escribe
   */
  searchAddressSuggestions(searchText: string): Promise<PhotoLocation[]>;
}

export default PhotoMetadataManager as PhotoMetadataModule;
