import {NativeModules} from 'react-native';

const {PhotoMetadataManager} = NativeModules;

export interface PhotoAsset {
  id: string;
  uri: string;
  filename: string;
  width: number;
  height: number;
  creationDate: string;
  imageDescription?: string;
  hasDescription: boolean;
}

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
   * Lee el ImageDescription de una foto específica
   */
  getImageDescription(assetId: string): Promise<string | null>;

  /**
   * Guarda el ImageDescription en una foto
   */
  setImageDescription(assetId: string, description: string): Promise<boolean>;

  /**
   * Elimina una foto de la galería
   */
  deletePhoto(assetId: string): Promise<boolean>;

  /**
   * Obtiene la imagen en base64 para enviar a IA
   */
  getImageBase64(assetId: string, maxSize: number): Promise<string>;
}

export default PhotoMetadataManager as PhotoMetadataModule;
