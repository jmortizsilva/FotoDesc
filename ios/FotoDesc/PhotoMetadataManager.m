//
//  PhotoMetadataManager.m
//  FotoDesc
//
//  Bridge para exponer el módulo Swift a React Native
//

#import <React/RCTBridgeModule.h>

@interface RCT_EXTERN_MODULE(PhotoMetadataManager, NSObject)

RCT_EXTERN_METHOD(requestPhotoLibraryPermission:(RCTPromiseResolveBlock)resolve
                  rejecter:(RCTPromiseRejectBlock)reject)

RCT_EXTERN_METHOD(getAllPhotos:(RCTPromiseResolveBlock)resolve
                  rejecter:(RCTPromiseRejectBlock)reject)

RCT_EXTERN_METHOD(getPhotosWithDescription:(RCTPromiseResolveBlock)resolve
                  rejecter:(RCTPromiseRejectBlock)reject)

RCT_EXTERN_METHOD(getPhotosWithoutDescription:(RCTPromiseResolveBlock)resolve
                  rejecter:(RCTPromiseRejectBlock)reject)

RCT_EXTERN_METHOD(getImageDescription:(NSString *)assetId
                  resolver:(RCTPromiseResolveBlock)resolve
                  rejecter:(RCTPromiseRejectBlock)reject)

RCT_EXTERN_METHOD(setImageDescription:(NSString *)assetId
                  description:(NSString *)description
                  resolver:(RCTPromiseResolveBlock)resolve
                  rejecter:(RCTPromiseRejectBlock)reject)

RCT_EXTERN_METHOD(deletePhoto:(NSString *)assetId
                  resolver:(RCTPromiseResolveBlock)resolve
                  rejecter:(RCTPromiseRejectBlock)reject)

RCT_EXTERN_METHOD(getImageBase64:(NSString *)assetId
                  maxSize:(nonnull NSNumber *)maxSize
                  resolver:(RCTPromiseResolveBlock)resolve
                  rejecter:(RCTPromiseRejectBlock)reject)

@end
