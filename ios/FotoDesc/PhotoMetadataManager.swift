//
//  PhotoMetadataManager.swift
//  FotoDesc
//
//  Módulo nativo para gestionar metadatos EXIF en fotos de iOS
//  Permite leer y escribir el campo ImageDescription para accesibilidad
//

import Foundation
import Photos
import UIKit

@objc(PhotoMetadataManager)
class PhotoMetadataManager: NSObject {
  
  // MARK: - Request Photo Library Permission
  
  @objc
  func requestPhotoLibraryPermission(_ resolve: @escaping RCTPromiseResolveBlock,
                                     rejecter reject: @escaping RCTPromiseRejectBlock) {
    let status = PHPhotoLibrary.authorizationStatus(for: .readWrite)
    
    switch status {
    case .authorized, .limited:
      resolve(true)
    case .denied, .restricted:
      resolve(false)
    case .notDetermined:
      PHPhotoLibrary.requestAuthorization(for: .readWrite) { newStatus in
        resolve(newStatus == .authorized || newStatus == .limited)
      }
    @unknown default:
      resolve(false)
    }
  }
  
  // MARK: - Get All Photos
  
  @objc
  func getAllPhotos(_ resolve: @escaping RCTPromiseResolveBlock,
                    rejecter reject: @escaping RCTPromiseRejectBlock) {
    DispatchQueue.global(qos: .userInitiated).async {
      let fetchOptions = PHFetchOptions()
      fetchOptions.sortDescriptors = [NSSortDescriptor(key: "creationDate", ascending: false)]
      
      let assets = PHAsset.fetchAssets(with: .image, options: fetchOptions)
      var photoArray: [[String: Any]] = []
      
      assets.enumerateObjects { asset, _, _ in
        if let photoDict = self.assetToDictionary(asset) {
          photoArray.append(photoDict)
        }
      }
      
      DispatchQueue.main.async {
        resolve(photoArray)
      }
    }
  }
  
  // MARK: - Get Photos With Description
  
  @objc
  func getPhotosWithDescription(_ resolve: @escaping RCTPromiseResolveBlock,
                                rejecter reject: @escaping RCTPromiseRejectBlock) {
    DispatchQueue.global(qos: .userInitiated).async {
      let fetchOptions = PHFetchOptions()
      fetchOptions.sortDescriptors = [NSSortDescriptor(key: "creationDate", ascending: false)]
      
      let assets = PHAsset.fetchAssets(with: .image, options: fetchOptions)
      var photoArray: [[String: Any]] = []
      
      assets.enumerateObjects { asset, _, _ in
        if let description = asset.accessibilityDescription, !description.isEmpty {
          if let photoDict = self.assetToDictionary(asset) {
            photoArray.append(photoDict)
          }
        }
      }
      
      DispatchQueue.main.async {
        resolve(photoArray)
      }
    }
  }
  
  // MARK: - Get Photos Without Description
  
  @objc
  func getPhotosWithoutDescription(_ resolve: @escaping RCTPromiseResolveBlock,
                                    rejecter reject: @escaping RCTPromiseRejectBlock) {
    DispatchQueue.global(qos: .userInitiated).async {
      let fetchOptions = PHFetchOptions()
      fetchOptions.sortDescriptors = [NSSortDescriptor(key: "creationDate", ascending: false)]
      
      let assets = PHAsset.fetchAssets(with: .image, options: fetchOptions)
      var photoArray: [[String: Any]] = []
      
      assets.enumerateObjects { asset, _, _ in
        if asset.accessibilityDescription == nil || asset.accessibilityDescription?.isEmpty == true {
          if let photoDict = self.assetToDictionary(asset) {
            photoArray.append(photoDict)
          }
        }
      }
      
      DispatchQueue.main.async {
        resolve(photoArray)
      }
    }
  }
  
  // MARK: - Get Image Description
  
  @objc
  func getImageDescription(_ assetId: String,
                          resolver resolve: @escaping RCTPromiseResolveBlock,
                          rejecter reject: @escaping RCTPromiseRejectBlock) {
    guard let asset = fetchAsset(withIdentifier: assetId) else {
      reject("ASSET_NOT_FOUND", "No se encontró la foto", nil)
      return
    }
    
    let description = asset.accessibilityDescription
    resolve(description ?? NSNull())
  }
  
  // MARK: - Set Image Description
  
  @objc
  func setImageDescription(_ assetId: String,
                          description: String,
                          resolver resolve: @escaping RCTPromiseResolveBlock,
                          rejecter reject: @escaping RCTPromiseRejectBlock) {
    guard let asset = fetchAsset(withIdentifier: assetId) else {
      reject("ASSET_NOT_FOUND", "No se encontró la foto", nil)
      return
    }
    
    PHPhotoLibrary.shared().performChanges({
      let request = PHAssetChangeRequest(for: asset)
      request.accessibilityDescription = description
    }) { success, error in
      if success {
        resolve(true)
      } else {
        reject("SAVE_FAILED", "No se pudo guardar la descripción", error)
      }
    }
  }
  
  // MARK: - Delete Photo
  
  @objc
  func deletePhoto(_ assetId: String,
                   resolver resolve: @escaping RCTPromiseResolveBlock,
                   rejecter reject: @escaping RCTPromiseRejectBlock) {
    guard let asset = fetchAsset(withIdentifier: assetId) else {
      reject("ASSET_NOT_FOUND", "No se encontró la foto", nil)
      return
    }
    
    PHPhotoLibrary.shared().performChanges({
      PHAssetChangeRequest.deleteAssets([asset] as NSArray)
    }) { success, error in
      if success {
        resolve(true)
      } else {
        reject("DELETE_FAILED", "No se pudo eliminar la foto", error)
      }
    }
  }
  
  // MARK: - Get Image Base64
  
  @objc
  func getImageBase64(_ assetId: String,
                     maxSize: NSNumber,
                     resolver resolve: @escaping RCTPromiseResolveBlock,
                     rejecter reject: @escaping RCTPromiseRejectBlock) {
    guard let asset = fetchAsset(withIdentifier: assetId) else {
      reject("ASSET_NOT_FOUND", "No se encontró la foto", nil)
      return
    }
    
    let options = PHImageRequestOptions()
    options.isSynchronous = true
    options.deliveryMode = .highQualityFormat
    options.resizeMode = .exact
    
    let targetSize = CGSize(width: maxSize.intValue, height: maxSize.intValue)
    
    PHImageManager.default().requestImage(for: asset,
                                         targetSize: targetSize,
                                         contentMode: .aspectFit,
                                         options: options) { image, _ in
      guard let image = image else {
        reject("IMAGE_LOAD_FAILED", "No se pudo cargar la imagen", nil)
        return
      }
      
      guard let imageData = image.jpegData(compressionQuality: 0.8) else {
        reject("IMAGE_ENCODE_FAILED", "No se pudo codificar la imagen", nil)
        return
      }
      
      let base64String = imageData.base64EncodedString()
      resolve(base64String)
    }
  }
  
  // MARK: - Helper Methods
  
  private func fetchAsset(withIdentifier identifier: String) -> PHAsset? {
    let fetchResult = PHAsset.fetchAssets(withLocalIdentifiers: [identifier], options: nil)
    return fetchResult.firstObject
  }
  
  private func assetToDictionary(_ asset: PHAsset) -> [String: Any]? {
    let resources = PHAssetResource.assetResources(for: asset)
    guard let resource = resources.first else { return nil }
    
    let imageManager = PHImageManager.default()
    let options = PHImageRequestOptions()
    options.isSynchronous = true
    options.deliveryMode = .fastFormat
    
    var imageUri = ""
    imageManager.requestImageDataAndOrientation(for: asset, options: options) { data, _, _, _ in
      if let data = data {
        let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent(resource.originalFilename)
        try? data.write(to: tempURL)
        imageUri = tempURL.absoluteString
      }
    }
    
    let description = asset.accessibilityDescription
    let hasDescription = description != nil && !description!.isEmpty
    
    return [
      "id": asset.localIdentifier,
      "uri": imageUri,
      "filename": resource.originalFilename,
      "width": asset.pixelWidth,
      "height": asset.pixelHeight,
      "creationDate": (asset.creationDate ?? Date()).iso8601String,
      "imageDescription": description ?? "",
      "hasDescription": hasDescription
    ]
  }
}

// MARK: - Date Extension

extension Date {
  var iso8601String: String {
    let formatter = ISO8601DateFormatter()
    return formatter.string(from: self)
  }
}

// MARK: - React Native Bridge

@objc(PhotoMetadataManagerBridge)
class PhotoMetadataManagerBridge: NSObject {
  @objc
  static func requiresMainQueueSetup() -> Bool {
    return false
  }
}
