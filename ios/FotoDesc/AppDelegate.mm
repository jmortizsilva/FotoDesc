#import "AppDelegate.h"

#import <React/RCTBundleURLProvider.h>
#import <React/RCTBridgeModule.h>
#import <Photos/Photos.h>
#import <UIKit/UIKit.h>
#import <ImageIO/ImageIO.h>
#import <MobileCoreServices/MobileCoreServices.h>

@interface PhotoMetadataManager : NSObject <RCTBridgeModule>
@end

@implementation PhotoMetadataManager

RCT_EXPORT_MODULE();

+ (BOOL)requiresMainQueueSetup
{
  return NO;
}

- (PHAsset *)assetForId:(NSString *)assetId
{
  PHFetchResult<PHAsset *> *result = [PHAsset fetchAssetsWithLocalIdentifiers:@[assetId] options:nil];
  return result.firstObject;
}

- (NSString *)iso8601StringFromDate:(NSDate *)date
{
  NSISO8601DateFormatter *formatter = [NSISO8601DateFormatter new];
  return [formatter stringFromDate:date ?: [NSDate date]];
}

- (void)assetToDictionary:(PHAsset *)asset completion:(void (^)(NSDictionary *photoDict))completion
{
  NSArray<PHAssetResource *> *resources = [PHAssetResource assetResourcesForAsset:asset];
  PHAssetResource *resource = resources.firstObject;
  if (!resource) {
    completion(nil);
    return;
  }

  PHImageRequestOptions *options = [PHImageRequestOptions new];
  options.synchronous = NO;
  options.deliveryMode = PHImageRequestOptionsDeliveryModeHighQualityFormat;

  __block NSString *imageUri = @"";
  __block NSString *descriptionText = nil;
  
  [[PHImageManager defaultManager] requestImageDataAndOrientationForAsset:asset
                                                                   options:options
                                                             resultHandler:^(NSData * _Nullable data,
                                                                             NSString * _Nullable dataUTI,
                                                                             CGImagePropertyOrientation orientation,
                                                                             NSDictionary * _Nullable info) {
    if (data) {
      NSURL *tempURL = [NSURL fileURLWithPath:[NSTemporaryDirectory() stringByAppendingPathComponent:resource.originalFilename ?: @"image.jpg"]];
      [data writeToURL:tempURL atomically:YES];
      imageUri = tempURL.absoluteString ?: @"";
      
      // Extract IPTC Caption/Abstract (description) from image metadata
      CGImageSourceRef source = CGImageSourceCreateWithData((__bridge CFDataRef)data, NULL);
      if (source) {
        NSDictionary *metadata = (__bridge_transfer NSDictionary *)CGImageSourceCopyPropertiesAtIndex(source, 0, NULL);
        NSDictionary *iptc = metadata[(NSString *)kCGImagePropertyIPTCDictionary];
        descriptionText = iptc[(NSString *)kCGImagePropertyIPTCCaptionAbstract];
        CFRelease(source);
      }
    }
    
    BOOL hasDescription = (descriptionText.length > 0);
    
    completion(@{
      @"id": asset.localIdentifier ?: @"",
      @"uri": imageUri,
      @"filename": resource.originalFilename ?: @"",
      @"width": @(asset.pixelWidth),
      @"height": @(asset.pixelHeight),
      @"creationDate": [self iso8601StringFromDate:asset.creationDate],
      @"imageDescription": descriptionText ?: @"",
      @"hasDescription": @(hasDescription)
    });
  }];
}

RCT_REMAP_METHOD(requestPhotoLibraryPermission,
                 requestPhotoLibraryPermissionWithResolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(RCTPromiseRejectBlock)reject)
{
  if (@available(iOS 14, *)) {
    PHAuthorizationStatus status = [PHPhotoLibrary authorizationStatusForAccessLevel:PHAccessLevelReadWrite];
    switch (status) {
      case PHAuthorizationStatusAuthorized:
      case PHAuthorizationStatusLimited:
        resolve(@(YES));
        break;
      case PHAuthorizationStatusDenied:
      case PHAuthorizationStatusRestricted:
        resolve(@(NO));
        break;
      case PHAuthorizationStatusNotDetermined: {
        [PHPhotoLibrary requestAuthorizationForAccessLevel:PHAccessLevelReadWrite handler:^(PHAuthorizationStatus newStatus) {
          BOOL granted = (newStatus == PHAuthorizationStatusAuthorized || newStatus == PHAuthorizationStatusLimited);
          resolve(@(granted));
              }
              default:
                resolve(@(NO));
                break;
        }];
        break;
    }
  } else {
    // Fallback for iOS 13
    PHAuthorizationStatus status = [PHPhotoLibrary authorizationStatus];
    switch (status) {
      case PHAuthorizationStatusAuthorized:
        resolve(@(YES));
        break;
      case PHAuthorizationStatusDenied:
      case PHAuthorizationStatusRestricted:
        resolve(@(NO));
        break;
      case PHAuthorizationStatusNotDetermined: {
        [PHPhotoLibrary requestAuthorization:^(PHAuthorizationStatus newStatus) {
          resolve(@(newStatus == PHAuthorizationStatusAuthorized));
          }
        }];
        break;
      default:
        resolve(@(NO));
        break;
    }
  }
}

RCT_REMAP_METHOD(getAllPhotos,
                 getAllPhotosWithResolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(RCTPromiseRejectBlock)reject)
{
  dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
    PHFetchOptions *fetchOptions = [PHFetchOptions new];
    fetchOptions.sortDescriptors = @[[NSSortDescriptor sortDescriptorWithKey:@"creationDate" ascending:NO]];
    PHFetchResult<PHAsset *> *assets = [PHAsset fetchAssetsWithMediaType:PHAssetMediaTypeImage options:fetchOptions];

    NSMutableArray *photos = [NSMutableArray arrayWithCapacity:assets.count];
    __block NSInteger remaining = assets.count;
    
    if (remaining == 0) {
      resolve(@[]);
      return;
    }
    
    [assets enumerateObjectsUsingBlock:^(PHAsset * _Nonnull asset, NSUInteger idx, BOOL * _Nonnull stop) {
      [self assetToDictionary:asset completion:^(NSDictionary *photoDict) {
        if (photoDict) {
          @synchronized(photos) {
            [photos addObject:photoDict];
          }
        }
        remaining--;
        if (remaining == 0) {
          // Sort by creation date descending before returning
          NSArray *sorted = [photos sortedArrayUsingComparator:^NSComparisonResult(NSDictionary *a, NSDictionary *b) {
            return [b[@"creationDate"] compare:a[@"creationDate"]];
          }];
          resolve(sorted);
        }
      }];
    }];
  });
}

RCT_REMAP_METHOD(getPhotosWithDescription,
                 getPhotosWithDescriptionWithResolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(RCTPromiseRejectBlock)reject)
{
  dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
    PHFetchOptions *fetchOptions = [PHFetchOptions new];
    fetchOptions.sortDescriptors = @[[NSSortDescriptor sortDescriptorWithKey:@"creationDate" ascending:NO]];
    PHFetchResult<PHAsset *> *assets = [PHAsset fetchAssetsWithMediaType:PHAssetMediaTypeImage options:fetchOptions];

    NSMutableArray *photos = [NSMutableArray array];
    __block NSInteger remaining = assets.count;
    
    if (remaining == 0) {
      resolve(@[]);
      return;
    }
    
    [assets enumerateObjectsUsingBlock:^(PHAsset * _Nonnull asset, NSUInteger idx, BOOL * _Nonnull stop) {
      [self assetToDictionary:asset completion:^(NSDictionary *photoDict) {
        if (photoDict && [photoDict[@"hasDescription"] boolValue]) {
          @synchronized(photos) {
            [photos addObject:photoDict];
          }
        }
        remaining--;
        if (remaining == 0) {
          NSArray *sorted = [photos sortedArrayUsingComparator:^NSComparisonResult(NSDictionary *a, NSDictionary *b) {
            return [b[@"creationDate"] compare:a[@"creationDate"]];
          }];
          resolve(sorted);
        }
      }];
    }];
  });
}

RCT_REMAP_METHOD(getPhotosWithoutDescription,
                 getPhotosWithoutDescriptionWithResolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(RCTPromiseRejectBlock)reject)
{
  dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
    PHFetchOptions *fetchOptions = [PHFetchOptions new];
    fetchOptions.sortDescriptors = @[[NSSortDescriptor sortDescriptorWithKey:@"creationDate" ascending:NO]];
    PHFetchResult<PHAsset *> *assets = [PHAsset fetchAssetsWithMediaType:PHAssetMediaTypeImage options:fetchOptions];

    NSMutableArray *photos = [NSMutableArray array];
    __block NSInteger remaining = assets.count;
    
    if (remaining == 0) {
      resolve(@[]);
      return;
    }
    
    [assets enumerateObjectsUsingBlock:^(PHAsset * _Nonnull asset, NSUInteger idx, BOOL * _Nonnull stop) {
      [self assetToDictionary:asset completion:^(NSDictionary *photoDict) {
        if (photoDict && ![photoDict[@"hasDescription"] boolValue]) {
          @synchronized(photos) {
            [photos addObject:photoDict];
          }
        }
        remaining--;
        if (remaining == 0) {
          NSArray *sorted = [photos sortedArrayUsingComparator:^NSComparisonResult(NSDictionary *a, NSDictionary *b) {
            return [b[@"creationDate"] compare:a[@"creationDate"]];
          }];
          resolve(sorted);
        }
      }];
    }];
  });
}

RCT_REMAP_METHOD(getImageDescription,
                 getImageDescriptionForAsset:(NSString *)assetId
                 resolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(RCTPromiseRejectBlock)reject)
{
  PHAsset *asset = [self assetForId:assetId];
  if (!asset) {
    reject(@"ASSET_NOT_FOUND", @"No se encontró la foto", nil);
    return;
  }

  PHImageRequestOptions *options = [PHImageRequestOptions new];
  options.synchronous = NO;
  options.deliveryMode = PHImageRequestOptionsDeliveryModeHighQualityFormat;
  
  [[PHImageManager defaultManager] requestImageDataAndOrientationForAsset:asset
                                                                   options:options
                                                             resultHandler:^(NSData * _Nullable data,
                                                                             NSString * _Nullable dataUTI,
                                                                             CGImagePropertyOrientation orientation,
                                                                             NSDictionary * _Nullable info) {
    if (!data) {
      resolve((id)kCFNull);
      return;
    }
    
    // Extract IPTC Caption/Abstract from image metadata
    CGImageSourceRef source = CGImageSourceCreateWithData((__bridge CFDataRef)data, NULL);
    if (source) {
      NSDictionary *metadata = (__bridge_transfer NSDictionary *)CGImageSourceCopyPropertiesAtIndex(source, 0, NULL);
      NSDictionary *iptc = metadata[(NSString *)kCGImagePropertyIPTCDictionary];
      NSString *description = iptc[(NSString *)kCGImagePropertyIPTCCaptionAbstract];
      CFRelease(source);
      
      resolve(description ?: (id)kCFNull);
    } else {
      resolve((id)kCFNull);
    }
  }];
}

RCT_REMAP_METHOD(setImageDescription,
                 setImageDescriptionForAsset:(NSString *)assetId
                 description:(NSString *)description
                 resolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(RCTPromiseRejectBlock)reject)
{
  PHAsset *asset = [self assetForId:assetId];
  if (!asset) {
    reject(@"ASSET_NOT_FOUND", @"No se encontró la foto", nil);
    return;
  }

  // Request content editing input to edit the photo's metadata
  PHContentEditingInputRequestOptions *editOptions = [PHContentEditingInputRequestOptions new];
  editOptions.canHandleAdjustmentData = ^BOOL(PHAdjustmentData * _Nonnull adjustmentData) {
    return [adjustmentData.formatIdentifier isEqualToString:@"com.fotodesc.iptc"];
  };
  
  [asset requestContentEditingInputWithOptions:editOptions
                             completionHandler:^(PHContentEditingInput * _Nullable input, NSDictionary * _Nonnull info) {
    if (!input || !input.fullSizeImageURL) {
      reject(@"EDIT_INPUT_FAILED", @"No se pudo obtener la imagen para editar", nil);
      return;
    }
    
    // Load the original image
    CGImageSourceRef source = CGImageSourceCreateWithURL((__bridge CFURLRef)input.fullSizeImageURL, NULL);
    if (!source) {
      reject(@"IMAGE_LOAD_FAILED", @"No se pudo cargar la imagen", nil);
      return;
    }
    
    // Get original metadata
    NSDictionary *originalMetadata = (__bridge_transfer NSDictionary *)CGImageSourceCopyPropertiesAtIndex(source, 0, NULL);
    NSMutableDictionary *mutableMetadata = [originalMetadata mutableCopy] ?: [NSMutableDictionary dictionary];
    
    // Update IPTC metadata with description
    NSMutableDictionary *iptcDict = [mutableMetadata[(NSString *)kCGImagePropertyIPTCDictionary] mutableCopy] ?: [NSMutableDictionary dictionary];
    iptcDict[(NSString *)kCGImagePropertyIPTCCaptionAbstract] = description;
    mutableMetadata[(NSString *)kCGImagePropertyIPTCDictionary] = iptcDict;
    
    // Create output for edited content
    PHContentEditingOutput *output = [[PHContentEditingOutput alloc] initWithContentEditingInput:input];
    
    // Create adjustment data to mark this as our edit
    NSData *adjustmentData = [@"IPTC Description Edit" dataUsingEncoding:NSUTF8StringEncoding];
    output.adjustmentData = [[PHAdjustmentData alloc] initWithFormatIdentifier:@"com.fotodesc.iptc"
                                                                formatVersion:@"1.0"
                                                                         data:adjustmentData];
    
    // Get the original image type (JPEG, HEIC, etc.)
    CFStringRef imageType = CGImageSourceGetType(source);
    if (!imageType) {
      imageType = kUTTypeJPEG; // Default to JPEG
    }
    
    // Create destination for the edited image
    CGImageDestinationRef destination = CGImageDestinationCreateWithURL((__bridge CFURLRef)output.renderedContentURL,
                                                                         imageType,
                                                                         1,
                                                                         NULL);
    if (!destination) {
      CFRelease(source);
      reject(@"DESTINATION_FAILED", @"No se pudo crear el destino de la imagen", nil);
      return;
    }
    
    // Get the original image
    CGImageRef image = CGImageSourceCreateImageAtIndex(source, 0, NULL);
    if (!image) {
      CFRelease(source);
      CFRelease(destination);
      reject(@"IMAGE_CREATE_FAILED", @"No se pudo crear la imagen", nil);
      return;
    }
    
    // Add image with updated metadata to destination
    CGImageDestinationAddImage(destination, image, (__bridge CFDictionaryRef)mutableMetadata);
    
    // Finalize the image file
    if (!CGImageDestinationFinalize(destination)) {
      CFRelease(image);
      CFRelease(source);
      CFRelease(destination);
      reject(@"FINALIZE_FAILED", @"No se pudo finalizar la imagen editada", nil);
      return;
    }
    
    // Clean up
    CFRelease(image);
    CFRelease(source);
    CFRelease(destination);
    
    // Apply changes to the photo library - this REPLACES the original photo
    [[PHPhotoLibrary sharedPhotoLibrary] performChanges:^{
      PHAssetChangeRequest *request = [PHAssetChangeRequest changeRequestForAsset:asset];
      request.contentEditingOutput = output;
    } completionHandler:^(BOOL success, NSError * _Nullable error) {
      if (success) {
        resolve(@(YES));
      } else {
        reject(@"SAVE_FAILED", @"No se pudo guardar la descripción en la foto", error);
      }
    }];
  }];
}

RCT_REMAP_METHOD(deletePhoto,
                 deletePhotoForAsset:(NSString *)assetId
                 resolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(RCTPromiseRejectBlock)reject)
{
  PHAsset *asset = [self assetForId:assetId];
  if (!asset) {
    reject(@"ASSET_NOT_FOUND", @"No se encontró la foto", nil);
    return;
  }

  [[PHPhotoLibrary sharedPhotoLibrary] performChanges:^{
    [PHAssetChangeRequest deleteAssets:@[asset]];
  } completionHandler:^(BOOL success, NSError * _Nullable error) {
    if (success) {
      resolve(@(YES));
    } else {
      reject(@"DELETE_FAILED", @"No se pudo eliminar la foto", error);
    }
  }];
}

RCT_REMAP_METHOD(getImageBase64,
                 getImageBase64ForAsset:(NSString *)assetId
                 maxSize:(nonnull NSNumber *)maxSize
                 resolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(RCTPromiseRejectBlock)reject)
{
  PHAsset *asset = [self assetForId:assetId];
  if (!asset) {
    reject(@"ASSET_NOT_FOUND", @"No se encontró la foto", nil);
    return;
  }

  PHImageRequestOptions *options = [PHImageRequestOptions new];
  options.synchronous = NO;
  options.deliveryMode = PHImageRequestOptionsDeliveryModeHighQualityFormat;
  options.resizeMode = PHImageRequestOptionsResizeModeExact;

  CGSize targetSize = CGSizeMake(maxSize.intValue, maxSize.intValue);
  [[PHImageManager defaultManager] requestImageForAsset:asset
                                             targetSize:targetSize
                                            contentMode:PHImageContentModeAspectFit
                                                options:options
                                          resultHandler:^(UIImage * _Nullable result, NSDictionary * _Nullable info) {
    if (!result) {
      reject(@"IMAGE_LOAD_FAILED", @"No se pudo cargar la imagen", nil);
      return;
    }
    NSData *imageData = UIImageJPEGRepresentation(result, 0.8);
    if (!imageData) {
      reject(@"IMAGE_ENCODE_FAILED", @"No se pudo codificar la imagen", nil);
      return;
    }
    resolve([imageData base64EncodedStringWithOptions:0]);
  }];
}

@end

@implementation AppDelegate

- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions
{
  self.moduleName = @"FotoDesc";
  // You can add your custom initial props in the dictionary below.
  // They will be passed down to the ViewController used by React Native.
  self.initialProps = @{};

  return [super application:application didFinishLaunchingWithOptions:launchOptions];
}

- (NSURL *)sourceURLForBridge:(RCTBridge *)bridge
{
  return [self getBundleURL];
}

- (NSURL *)getBundleURL
{
#if DEBUG
  return [[RCTBundleURLProvider sharedSettings] jsBundleURLForBundleRoot:@"index"];
#else
  return [[NSBundle mainBundle] URLForResource:@"main" withExtension:@"jsbundle"];
#endif
}

@end
