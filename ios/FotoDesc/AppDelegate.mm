#import "AppDelegate.h"

#import <React/RCTBundleURLProvider.h>
#import <React/RCTBridgeModule.h>
#import <Photos/Photos.h>
#import <UIKit/UIKit.h>
#import <ImageIO/ImageIO.h>
#import <MobileCoreServices/MobileCoreServices.h>
#import <CoreLocation/CoreLocation.h>
#import <math.h>

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

- (NSString *)fileExtensionForImageType:(CFStringRef)imageType
{
  if (!imageType) {
    return @"jpg";
  }

  if (UTTypeConformsTo(imageType, kUTTypeJPEG)) {
    return @"jpg";
  }
  if (UTTypeConformsTo(imageType, kUTTypePNG)) {
    return @"png";
  }
  if (UTTypeConformsTo(imageType, CFSTR("public.heic"))) {
    return @"heic";
  }

  return @"jpg";
}

- (NSDictionary *)gpsMetadataDictionaryForLatitude:(NSNumber *)latitude longitude:(NSNumber *)longitude
{
  if (!latitude || !longitude) {
    return nil;
  }

  double lat = latitude.doubleValue;
  double lon = longitude.doubleValue;

  return @{
    (NSString *)kCGImagePropertyGPSLatitude: @(fabs(lat)),
    (NSString *)kCGImagePropertyGPSLatitudeRef: (lat >= 0 ? @"N" : @"S"),
    (NSString *)kCGImagePropertyGPSLongitude: @(fabs(lon)),
    (NSString *)kCGImagePropertyGPSLongitudeRef: (lon >= 0 ? @"E" : @"W")
  };
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
  options.networkAccessAllowed = YES;
  options.version = PHImageRequestOptionsVersionCurrent;

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
      
      // Extract description from common metadata fields (IPTC/TIFF/EXIF/XMP tags).
      CGImageSourceRef source = CGImageSourceCreateWithData((__bridge CFDataRef)data, NULL);
      if (source) {
        NSDictionary *metadata = (__bridge_transfer NSDictionary *)CGImageSourceCopyPropertiesAtIndex(source, 0, NULL);
        descriptionText = [self extractImageDescriptionFromMetadata:metadata];
        if (descriptionText.length == 0) {
          descriptionText = [self extractImageDescriptionFromImageSource:source];
        }
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
      @"locationLatitude": asset.location ? @(asset.location.coordinate.latitude) : [NSNull null],
      @"locationLongitude": asset.location ? @(asset.location.coordinate.longitude) : [NSNull null],
      @"imageDescription": descriptionText ?: @"",
      @"hasDescription": @(hasDescription)
    });
  }];
}

- (NSString *)extractImageDescriptionFromMetadata:(NSDictionary *)metadata
{
  if (!metadata) {
    return nil;
  }

  NSDictionary *iptc = metadata[(NSString *)kCGImagePropertyIPTCDictionary];
  NSString *iptcCaption = [iptc[(NSString *)kCGImagePropertyIPTCCaptionAbstract] isKindOfClass:[NSString class]]
    ? iptc[(NSString *)kCGImagePropertyIPTCCaptionAbstract]
    : nil;
  if (iptcCaption.length > 0) {
    return iptcCaption;
  }

  NSDictionary *tiff = metadata[(NSString *)kCGImagePropertyTIFFDictionary];
  NSString *tiffDescription = [tiff[(NSString *)kCGImagePropertyTIFFImageDescription] isKindOfClass:[NSString class]]
    ? tiff[(NSString *)kCGImagePropertyTIFFImageDescription]
    : nil;
  if (tiffDescription.length > 0) {
    return tiffDescription;
  }

  NSString *iptcObjectName = [iptc[(NSString *)kCGImagePropertyIPTCObjectName] isKindOfClass:[NSString class]]
    ? iptc[(NSString *)kCGImagePropertyIPTCObjectName]
    : nil;
  if (iptcObjectName.length > 0) {
    return iptcObjectName;
  }

  NSDictionary *png = metadata[(NSString *)kCGImagePropertyPNGDictionary];
  NSString *pngDescription = [png[(NSString *)kCGImagePropertyPNGDescription] isKindOfClass:[NSString class]]
    ? png[(NSString *)kCGImagePropertyPNGDescription]
    : nil;
  if (pngDescription.length > 0) {
    return pngDescription;
  }

  NSDictionary *exif = metadata[(NSString *)kCGImagePropertyExifDictionary];
  NSString *userComment = [exif[(NSString *)kCGImagePropertyExifUserComment] isKindOfClass:[NSString class]]
    ? exif[(NSString *)kCGImagePropertyExifUserComment]
    : nil;
  if (userComment.length > 0) {
    return userComment;
  }

  return nil;
}

- (NSString *)extractImageDescriptionFromImageSource:(CGImageSourceRef)source
{
  if (!source) {
    return nil;
  }

  CGImageMetadataRef imageMetadata = CGImageSourceCopyMetadataAtIndex(source, 0, NULL);
  if (!imageMetadata) {
    return nil;
  }

  CFArrayRef tags = CGImageMetadataCopyTags(imageMetadata);
  CFRelease(imageMetadata);
  if (!tags) {
    return nil;
  }

  NSArray<NSString *> *priorityNames = @[
    @"caption-abstract",
    @"imagedescription",
    @"description",
    @"artworkcontentdescription",
    @"usercomment",
    @"xpcomment",
    @"title",
    @"objectname"
  ];

  NSMutableDictionary<NSString *, NSString *> *foundByName = [NSMutableDictionary dictionary];

  for (CFIndex i = 0; i < CFArrayGetCount(tags); i++) {
    CGImageMetadataTagRef tag = (CGImageMetadataTagRef)CFArrayGetValueAtIndex(tags, i);
    if (!tag) {
      continue;
    }

    CFStringRef nameRef = CGImageMetadataTagCopyName(tag);
    CFTypeRef valueRef = CGImageMetadataTagCopyValue(tag);
    if (!nameRef || !valueRef) {
      if (nameRef) {
        CFRelease(nameRef);
      }
      if (valueRef) {
        CFRelease(valueRef);
      }
      continue;
    }

    NSString *name = [(__bridge NSString *)nameRef lowercaseString];
    NSString *value = nil;

    if (CFGetTypeID(valueRef) == CFStringGetTypeID()) {
      value = (__bridge NSString *)valueRef;
    }

    if (name.length > 0 && value.length > 0) {
      foundByName[name] = value;
    }

    CFRelease(nameRef);
    CFRelease(valueRef);
  }

  CFRelease(tags);

  for (NSString *priorityName in priorityNames) {
    NSString *foundValue = foundByName[priorityName];
    if (foundValue.length > 0) {
      return foundValue;
    }
  }

  return nil;
}

- (NSString *)formattedAddressFromPlacemark:(CLPlacemark *)placemark fallback:(NSString *)fallback
{
  NSMutableArray<NSString *> *parts = [NSMutableArray array];
  if (placemark.name.length > 0) [parts addObject:placemark.name];
  if (placemark.locality.length > 0) [parts addObject:placemark.locality];
  if (placemark.administrativeArea.length > 0) [parts addObject:placemark.administrativeArea];
  if (placemark.country.length > 0) [parts addObject:placemark.country];

  NSString *address = [parts componentsJoinedByString:@", "];
  return address.length > 0 ? address : (fallback ?: @"");
}

- (NSNumber *)signedCoordinateFromMetadataValue:(id)value refValue:(id)refValue positiveRefs:(NSArray<NSString *> *)positiveRefs
{
  if (![value respondsToSelector:@selector(doubleValue)]) {
    return nil;
  }

  double coordinate = [value doubleValue];
  NSString *ref = [refValue isKindOfClass:[NSString class]] ? [(NSString *)refValue uppercaseString] : @"";
  BOOL isPositiveRef = [positiveRefs containsObject:ref];
  if (!isPositiveRef) {
    coordinate = -fabs(coordinate);
  } else {
    coordinate = fabs(coordinate);
  }

  return @(coordinate);
}

- (NSDictionary *)gpsCoordinatesFromMetadataDictionary:(NSDictionary *)metadata
{
  if (![metadata isKindOfClass:[NSDictionary class]]) {
    return nil;
  }

  NSDictionary *gps = metadata[(NSString *)kCGImagePropertyGPSDictionary];
  if (![gps isKindOfClass:[NSDictionary class]]) {
    return nil;
  }

  NSNumber *lat = [self signedCoordinateFromMetadataValue:gps[(NSString *)kCGImagePropertyGPSLatitude]
                                                 refValue:gps[(NSString *)kCGImagePropertyGPSLatitudeRef]
                                             positiveRefs:@[@"N"]];
  NSNumber *lon = [self signedCoordinateFromMetadataValue:gps[(NSString *)kCGImagePropertyGPSLongitude]
                                                 refValue:gps[(NSString *)kCGImagePropertyGPSLongitudeRef]
                                             positiveRefs:@[@"E"]];
  if (!lat || !lon) {
    return nil;
  }

  return @{
    @"latitude": lat,
    @"longitude": lon
  };
}

- (NSDate *)dateFromIso8601String:(NSString *)isoDate
{
  if (![isoDate isKindOfClass:[NSString class]] || isoDate.length == 0) {
    return nil;
  }

  NSISO8601DateFormatter *formatter = [NSISO8601DateFormatter new];
  return [formatter dateFromString:isoDate];
}

- (BOOL)photoDictionary:(NSDictionary *)photoDict matchesFilterType:(NSString *)filterType
{
  if (![filterType isKindOfClass:[NSString class]] || filterType.length == 0 || [filterType isEqualToString:@"all"]) {
    return YES;
  }

  BOOL hasDescription = [photoDict[@"hasDescription"] boolValue];
  if ([filterType isEqualToString:@"with-description"]) {
    return hasDescription;
  }
  if ([filterType isEqualToString:@"without-description"]) {
    return !hasDescription;
  }

  return YES;
}

RCT_REMAP_METHOD(requestPhotoLibraryPermission,
                 requestPhotoLibraryPermissionWithResolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(RCTPromiseRejectBlock)reject)
{
  if (@available(iOS 14, *)) {
    PHAuthorizationStatus status = [PHPhotoLibrary authorizationStatusForAccessLevel:PHAccessLevelReadWrite];
    if (status == PHAuthorizationStatusAuthorized || status == PHAuthorizationStatusLimited) {
      resolve(@(YES));
    } else if (status == PHAuthorizationStatusDenied || status == PHAuthorizationStatusRestricted) {
      resolve(@(NO));
    } else if (status == PHAuthorizationStatusNotDetermined) {
      [PHPhotoLibrary requestAuthorizationForAccessLevel:PHAccessLevelReadWrite handler:^(PHAuthorizationStatus newStatus) {
        BOOL granted = (newStatus == PHAuthorizationStatusAuthorized || newStatus == PHAuthorizationStatusLimited);
        resolve(@(granted));
      }];
    } else {
      resolve(@(NO));
    }
  } else {
    // Fallback for iOS 13
    PHAuthorizationStatus status = [PHPhotoLibrary authorizationStatus];
    if (status == PHAuthorizationStatusAuthorized) {
      resolve(@(YES));
    } else if (status == PHAuthorizationStatusDenied || status == PHAuthorizationStatusRestricted) {
      resolve(@(NO));
    } else if (status == PHAuthorizationStatusNotDetermined) {
      [PHPhotoLibrary requestAuthorization:^(PHAuthorizationStatus newStatus) {
        resolve(@(newStatus == PHAuthorizationStatusAuthorized));
      }];
    } else {
      resolve(@(NO));
    }
  }
}

RCT_REMAP_METHOD(getPhotosPage,
                 getPhotosPageWithOffset:(nonnull NSNumber *)offset
                 limit:(nonnull NSNumber *)limit
                 filterType:(NSString *)filterType
                 startDateIso:(NSString *)startDateIso
                 endDateIso:(NSString *)endDateIso
                 resolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(RCTPromiseRejectBlock)reject)
{
  dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
    NSInteger safeOffset = MAX(0, offset.integerValue);
    NSInteger safeLimit = MIN(MAX(1, limit.integerValue), 120);

    PHFetchOptions *fetchOptions = [PHFetchOptions new];
    fetchOptions.sortDescriptors = @[[NSSortDescriptor sortDescriptorWithKey:@"creationDate" ascending:NO]];

    NSDate *startDate = [self dateFromIso8601String:startDateIso];
    NSDate *endDate = [self dateFromIso8601String:endDateIso];
    if (startDate && endDate) {
      fetchOptions.predicate = [NSPredicate predicateWithFormat:@"creationDate >= %@ AND creationDate <= %@", startDate, endDate];
    } else if (startDate) {
      fetchOptions.predicate = [NSPredicate predicateWithFormat:@"creationDate >= %@", startDate];
    } else if (endDate) {
      fetchOptions.predicate = [NSPredicate predicateWithFormat:@"creationDate <= %@", endDate];
    }

    PHFetchResult<PHAsset *> *assets = [PHAsset fetchAssetsWithMediaType:PHAssetMediaTypeImage options:fetchOptions];
    NSInteger totalAssets = assets.count;
    if (safeOffset >= totalAssets) {
      resolve(@{
        @"items": @[],
        @"nextOffset": @(safeOffset),
        @"hasMore": @(NO)
      });
      return;
    }

    NSMutableArray *items = [NSMutableArray arrayWithCapacity:safeLimit];
    __block NSInteger scanIndex = safeOffset;
    __block BOOL didResolve = NO;

    void (^resolvePage)(BOOL) = ^(BOOL timedOut) {
      if (didResolve) {
        return;
      }
      didResolve = YES;
      BOOL hasMore = scanIndex < totalAssets;
      resolve(@{
        @"items": items,
        @"nextOffset": @(scanIndex),
        @"hasMore": @(hasMore || timedOut)
      });
    };

    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(12 * NSEC_PER_SEC)),
                   dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
      @synchronized(items) {
        resolvePage(YES);
      }
    });

    __block void (^processNextAsset)(void);
    processNextAsset = ^{
      @synchronized(items) {
        if (didResolve) {
          return;
        }

        if (items.count >= safeLimit) {
          resolvePage(NO);
          return;
        }

        if (scanIndex >= totalAssets) {
          resolvePage(NO);
          return;
        }

        PHAsset *asset = [assets objectAtIndex:scanIndex];
        scanIndex++;

        [self assetToDictionary:asset completion:^(NSDictionary *photoDict) {
          @synchronized(items) {
            if (didResolve) {
              return;
            }

            if (photoDict && [self photoDictionary:photoDict matchesFilterType:filterType]) {
              [items addObject:photoDict];
            }
          }
          processNextAsset();
        }];
      }
    };

    processNextAsset();
  });
}

RCT_REMAP_METHOD(getAllPhotos,
                 getAllPhotosWithResolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(RCTPromiseRejectBlock)reject)
{
  dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
    PHFetchOptions *fetchOptions = [PHFetchOptions new];
    fetchOptions.sortDescriptors = @[[NSSortDescriptor sortDescriptorWithKey:@"creationDate" ascending:NO]];
    fetchOptions.fetchLimit = 500;
    PHFetchResult<PHAsset *> *assets = [PHAsset fetchAssetsWithMediaType:PHAssetMediaTypeImage options:fetchOptions];

    NSMutableArray *photos = [NSMutableArray arrayWithCapacity:assets.count];
    __block NSInteger remaining = assets.count;
    __block BOOL didResolve = NO;

    void (^resolveSortedIfNeeded)(void) = ^{
      if (didResolve) {
        return;
      }
      didResolve = YES;
      NSArray *sorted = [photos sortedArrayUsingComparator:^NSComparisonResult(NSDictionary *a, NSDictionary *b) {
        return [b[@"creationDate"] compare:a[@"creationDate"]];
      }];
      resolve(sorted);
    };
    
    if (remaining == 0) {
      resolve(@[]);
      return;
    }

    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(12 * NSEC_PER_SEC)),
                   dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
      @synchronized(photos) {
        resolveSortedIfNeeded();
      }
    });
    
    [assets enumerateObjectsUsingBlock:^(PHAsset * _Nonnull asset, NSUInteger idx, BOOL * _Nonnull stop) {
      [self assetToDictionary:asset completion:^(NSDictionary *photoDict) {
        @synchronized(photos) {
          if (didResolve) {
            return;
          }

          if (photoDict) {
            [photos addObject:photoDict];
          }

          remaining--;
          if (remaining == 0) {
            resolveSortedIfNeeded();
          }
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
    fetchOptions.fetchLimit = 500;
    PHFetchResult<PHAsset *> *assets = [PHAsset fetchAssetsWithMediaType:PHAssetMediaTypeImage options:fetchOptions];

    NSMutableArray *photos = [NSMutableArray array];
    __block NSInteger remaining = assets.count;
    __block BOOL didResolve = NO;

    void (^resolveSortedIfNeeded)(void) = ^{
      if (didResolve) {
        return;
      }
      didResolve = YES;
      NSArray *sorted = [photos sortedArrayUsingComparator:^NSComparisonResult(NSDictionary *a, NSDictionary *b) {
        return [b[@"creationDate"] compare:a[@"creationDate"]];
      }];
      resolve(sorted);
    };
    
    if (remaining == 0) {
      resolve(@[]);
      return;
    }

    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(12 * NSEC_PER_SEC)),
                   dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
      @synchronized(photos) {
        resolveSortedIfNeeded();
      }
    });
    
    [assets enumerateObjectsUsingBlock:^(PHAsset * _Nonnull asset, NSUInteger idx, BOOL * _Nonnull stop) {
      [self assetToDictionary:asset completion:^(NSDictionary *photoDict) {
        @synchronized(photos) {
          if (didResolve) {
            return;
          }

          if (photoDict && [photoDict[@"hasDescription"] boolValue]) {
            [photos addObject:photoDict];
          }

          remaining--;
          if (remaining == 0) {
            resolveSortedIfNeeded();
          }
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
    fetchOptions.fetchLimit = 500;
    PHFetchResult<PHAsset *> *assets = [PHAsset fetchAssetsWithMediaType:PHAssetMediaTypeImage options:fetchOptions];

    NSMutableArray *photos = [NSMutableArray array];
    __block NSInteger remaining = assets.count;
    __block BOOL didResolve = NO;

    void (^resolveSortedIfNeeded)(void) = ^{
      if (didResolve) {
        return;
      }
      didResolve = YES;
      NSArray *sorted = [photos sortedArrayUsingComparator:^NSComparisonResult(NSDictionary *a, NSDictionary *b) {
        return [b[@"creationDate"] compare:a[@"creationDate"]];
      }];
      resolve(sorted);
    };
    
    if (remaining == 0) {
      resolve(@[]);
      return;
    }

    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(12 * NSEC_PER_SEC)),
                   dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
      @synchronized(photos) {
        resolveSortedIfNeeded();
      }
    });
    
    [assets enumerateObjectsUsingBlock:^(PHAsset * _Nonnull asset, NSUInteger idx, BOOL * _Nonnull stop) {
      [self assetToDictionary:asset completion:^(NSDictionary *photoDict) {
        @synchronized(photos) {
          if (didResolve) {
            return;
          }

          if (photoDict && ![photoDict[@"hasDescription"] boolValue]) {
            [photos addObject:photoDict];
          }

          remaining--;
          if (remaining == 0) {
            resolveSortedIfNeeded();
          }
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

  void (^resolveFromImageDataFallback)(void) = ^{
    PHImageRequestOptions *options = [PHImageRequestOptions new];
    options.synchronous = NO;
    options.deliveryMode = PHImageRequestOptionsDeliveryModeHighQualityFormat;
    options.networkAccessAllowed = YES;
    options.version = PHImageRequestOptionsVersionCurrent;

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

      CGImageSourceRef source = CGImageSourceCreateWithData((__bridge CFDataRef)data, NULL);
      if (!source) {
        resolve((id)kCFNull);
        return;
      }

      NSDictionary *metadata = (__bridge_transfer NSDictionary *)CGImageSourceCopyPropertiesAtIndex(source, 0, NULL);
      NSString *description = [self extractImageDescriptionFromMetadata:metadata];
      if (description.length == 0) {
        description = [self extractImageDescriptionFromImageSource:source];
      }
      CFRelease(source);

      resolve(description ?: (id)kCFNull);
    }];
  };

  PHContentEditingInputRequestOptions *inputOptions = [PHContentEditingInputRequestOptions new];
  inputOptions.networkAccessAllowed = YES;

  [asset requestContentEditingInputWithOptions:inputOptions
                             completionHandler:^(PHContentEditingInput * _Nullable input, NSDictionary * _Nonnull info) {
    NSURL *fullSizeURL = input.fullSizeImageURL;
    if (!fullSizeURL) {
      resolveFromImageDataFallback();
      return;
    }

    CGImageSourceRef source = CGImageSourceCreateWithURL((__bridge CFURLRef)fullSizeURL, NULL);
    if (!source) {
      resolveFromImageDataFallback();
      return;
    }

    NSDictionary *metadata = (__bridge_transfer NSDictionary *)CGImageSourceCopyPropertiesAtIndex(source, 0, NULL);
    NSString *description = [self extractImageDescriptionFromMetadata:metadata];
    if (description.length == 0) {
      description = [self extractImageDescriptionFromImageSource:source];
    }
    CFRelease(source);

    resolve(description ?: (id)kCFNull);
  }];
}

RCT_REMAP_METHOD(getPhotoLocation,
                 getPhotoLocationForAsset:(NSString *)assetId
                 resolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(RCTPromiseRejectBlock)reject)
{
  PHAsset *asset = [self assetForId:assetId];
  if (!asset) {
    reject(@"ASSET_NOT_FOUND", @"No se encontró la foto", nil);
    return;
  }

  CLLocation *location = asset.location;
  if (!location) {
    void (^resolveFromImageDataFallback)(void) = ^{
      PHImageRequestOptions *dataOptions = [PHImageRequestOptions new];
      dataOptions.synchronous = NO;
      dataOptions.deliveryMode = PHImageRequestOptionsDeliveryModeHighQualityFormat;
      dataOptions.networkAccessAllowed = YES;

      [[PHImageManager defaultManager] requestImageDataAndOrientationForAsset:asset
                                                                       options:dataOptions
                                                                 resultHandler:^(NSData * _Nullable data,
                                                                                 NSString * _Nullable dataUTI,
                                                                                 CGImagePropertyOrientation orientation,
                                                                                 NSDictionary * _Nullable info) {
        if (!data) {
          resolve((id)kCFNull);
          return;
        }

        CGImageSourceRef sourceFromData = CGImageSourceCreateWithData((__bridge CFDataRef)data, NULL);
        if (!sourceFromData) {
          resolve((id)kCFNull);
          return;
        }

        NSDictionary *metadataFromData = (__bridge_transfer NSDictionary *)CGImageSourceCopyPropertiesAtIndex(sourceFromData, 0, NULL);
        CFRelease(sourceFromData);

        NSDictionary *coordsFromData = [self gpsCoordinatesFromMetadataDictionary:metadataFromData];
        resolve(coordsFromData ?: (id)kCFNull);
      }];
    };

    PHContentEditingInputRequestOptions *inputOptions = [PHContentEditingInputRequestOptions new];
    inputOptions.networkAccessAllowed = YES;

    [asset requestContentEditingInputWithOptions:inputOptions
                               completionHandler:^(PHContentEditingInput * _Nullable input, NSDictionary * _Nonnull info) {
      NSURL *fullSizeURL = input.fullSizeImageURL;
      if (!fullSizeURL) {
        resolveFromImageDataFallback();
        return;
      }

      CGImageSourceRef source = CGImageSourceCreateWithURL((__bridge CFURLRef)fullSizeURL, NULL);
      if (!source) {
        resolveFromImageDataFallback();
        return;
      }

      NSDictionary *metadata = (__bridge_transfer NSDictionary *)CGImageSourceCopyPropertiesAtIndex(source, 0, NULL);
      CFRelease(source);

      NSDictionary *metadataCoordinates = [self gpsCoordinatesFromMetadataDictionary:metadata];
      if (metadataCoordinates) {
        resolve(metadataCoordinates);
        return;
      }

      resolveFromImageDataFallback();
    }];
    return;
  }

  resolve(@{
    @"latitude": @(location.coordinate.latitude),
    @"longitude": @(location.coordinate.longitude)
  });
}

RCT_REMAP_METHOD(setPhotoLocation,
                 setPhotoLocationForAsset:(NSString *)assetId
                 latitude:(NSNumber * _Nullable)latitude
                 longitude:(NSNumber * _Nullable)longitude
                 resolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(RCTPromiseRejectBlock)reject)
{
  PHAsset *asset = [self assetForId:assetId];
  if (!asset) {
    reject(@"ASSET_NOT_FOUND", @"No se encontró la foto", nil);
    return;
  }

  PHContentEditingInputRequestOptions *editOptions = [PHContentEditingInputRequestOptions new];
  editOptions.networkAccessAllowed = YES;
  editOptions.canHandleAdjustmentData = ^BOOL(PHAdjustmentData * _Nonnull adjustmentData) {
    return YES;
  };

  [asset requestContentEditingInputWithOptions:editOptions
                             completionHandler:^(PHContentEditingInput * _Nullable input, NSDictionary * _Nonnull info) {
    if (!input || !input.fullSizeImageURL) {
      NSError *inputError = info[PHContentEditingInputErrorKey];
      reject(@"EDIT_INPUT_FAILED", @"No se pudo obtener la imagen para editar ubicación", inputError);
      return;
    }

    CGImageSourceRef source = CGImageSourceCreateWithURL((__bridge CFURLRef)input.fullSizeImageURL, NULL);
    if (!source) {
      reject(@"IMAGE_LOAD_FAILED", @"No se pudo cargar la imagen para guardar ubicación", nil);
      return;
    }

    NSDictionary *originalMetadata = (__bridge_transfer NSDictionary *)CGImageSourceCopyPropertiesAtIndex(source, 0, NULL);
    NSMutableDictionary *mutableMetadata = [originalMetadata mutableCopy] ?: [NSMutableDictionary dictionary];

    if (latitude && longitude) {
      NSDictionary *gps = [self gpsMetadataDictionaryForLatitude:latitude longitude:longitude];
      mutableMetadata[(NSString *)kCGImagePropertyGPSDictionary] = gps ?: @{};
    } else {
      [mutableMetadata removeObjectForKey:(NSString *)kCGImagePropertyGPSDictionary];
    }

    PHContentEditingOutput *output = [[PHContentEditingOutput alloc] initWithContentEditingInput:input];
    NSData *adjustmentData = [@"GPS Location Edit" dataUsingEncoding:NSUTF8StringEncoding];
    output.adjustmentData = [[PHAdjustmentData alloc] initWithFormatIdentifier:@"com.fotodesc.gps"
                                                                formatVersion:@"1.0"
                                                                         data:adjustmentData];

    CFStringRef imageType = CGImageSourceGetType(source);
    if (!imageType) {
      imageType = kUTTypeJPEG;
    }
    if (UTTypeConformsTo(imageType, kUTTypePNG)) {
      imageType = CFSTR("public.heic");
    }

    CGImageDestinationRef destination = CGImageDestinationCreateWithURL((__bridge CFURLRef)output.renderedContentURL,
                                                                         imageType,
                                                                         1,
                                                                         NULL);
    if (!destination) {
      CFRelease(source);
      reject(@"DESTINATION_FAILED", @"No se pudo crear el destino para guardar ubicación", nil);
      return;
    }

    CGImageRef image = CGImageSourceCreateImageAtIndex(source, 0, NULL);
    if (!image) {
      CFRelease(source);
      CFRelease(destination);
      reject(@"IMAGE_CREATE_FAILED", @"No se pudo preparar la imagen para guardar ubicación", nil);
      return;
    }

    CGImageDestinationAddImage(destination, image, (__bridge CFDictionaryRef)mutableMetadata);
    BOOL finalized = CGImageDestinationFinalize(destination);

    CFRelease(image);
    CFRelease(source);
    CFRelease(destination);

    if (!finalized) {
      reject(@"FINALIZE_FAILED", @"No se pudo finalizar la imagen con ubicación", nil);
      return;
    }

    [[PHPhotoLibrary sharedPhotoLibrary] performChanges:^{
      PHAssetChangeRequest *request = [PHAssetChangeRequest changeRequestForAsset:asset];
      request.contentEditingOutput = output;
      if (latitude && longitude) {
        CLLocation *location = [[CLLocation alloc] initWithLatitude:latitude.doubleValue
                                                          longitude:longitude.doubleValue];
        request.location = location;
      } else {
        request.location = nil;
      }
    } completionHandler:^(BOOL success, NSError * _Nullable error) {
      if (success) {
        resolve(@(YES));
      } else {
        reject(@"SET_LOCATION_FAILED", @"No se pudo guardar la localización en la foto", error);
      }
    }];
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
    return YES;
  };
  // Some assets are stored in iCloud and need network download before editing.
  editOptions.networkAccessAllowed = YES;
  
  [asset requestContentEditingInputWithOptions:editOptions
                             completionHandler:^(PHContentEditingInput * _Nullable input, NSDictionary * _Nonnull info) {
    if (!input || !input.fullSizeImageURL) {
      NSError *inputError = info[PHContentEditingInputErrorKey];
      if (inputError) {
        reject(@"EDIT_INPUT_FAILED", @"No se pudo obtener la imagen para editar", inputError);
      } else {
        reject(@"EDIT_INPUT_FAILED", @"No se pudo obtener la imagen para editar", nil);
      }
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
    if (description.length > 0) {
      iptcDict[(NSString *)kCGImagePropertyIPTCCaptionAbstract] = description;
    } else {
      [iptcDict removeObjectForKey:(NSString *)kCGImagePropertyIPTCCaptionAbstract];
    }
    mutableMetadata[(NSString *)kCGImagePropertyIPTCDictionary] = iptcDict;

    // Mirror description in TIFF ImageDescription to support photos like the sample.
    NSMutableDictionary *tiffDict = [mutableMetadata[(NSString *)kCGImagePropertyTIFFDictionary] mutableCopy] ?: [NSMutableDictionary dictionary];
    if (description.length > 0) {
      tiffDict[(NSString *)kCGImagePropertyTIFFImageDescription] = description;
    } else {
      [tiffDict removeObjectForKey:(NSString *)kCGImagePropertyTIFFImageDescription];
    }
    mutableMetadata[(NSString *)kCGImagePropertyTIFFDictionary] = tiffDict;
    
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

    // Some PNG assets (e.g. screenshots) may fail commit with contentEditingOutput.
    // iOS Photos commonly rewrites these edits as HEIC resources.
    // Aligning with that behavior improves compatibility.
    if (UTTypeConformsTo(imageType, kUTTypePNG)) {
      imageType = CFSTR("public.heic");
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

RCT_REMAP_METHOD(prepareAssetForEditing,
                 prepareAssetForEditingForAsset:(NSString *)assetId
                 resolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(RCTPromiseRejectBlock)reject)
{
  PHAsset *asset = [self assetForId:assetId];
  if (!asset) {
    reject(@"ASSET_NOT_FOUND", @"No se encontró la foto", nil);
    return;
  }

  PHContentEditingInputRequestOptions *options = [PHContentEditingInputRequestOptions new];
  options.networkAccessAllowed = YES;
  options.canHandleAdjustmentData = ^BOOL(PHAdjustmentData * _Nonnull adjustmentData) {
    return YES;
  };

  [asset requestContentEditingInputWithOptions:options
                             completionHandler:^(PHContentEditingInput * _Nullable input, NSDictionary * _Nonnull info) {
    if (!input || !input.fullSizeImageURL) {
      NSError *inputError = info[PHContentEditingInputErrorKey];
      if (inputError) {
        reject(@"PREPARE_ASSET_FAILED", @"No se pudo preparar la foto para edición", inputError);
      } else {
        reject(@"PREPARE_ASSET_FAILED", @"No se pudo preparar la foto para edición", nil);
      }
      return;
    }

    resolve(@(YES));
  }];
}

RCT_REMAP_METHOD(reverseGeocodeLocation,
                 reverseGeocodeLocationForLatitude:(nonnull NSNumber *)latitude
                 longitude:(nonnull NSNumber *)longitude
                 resolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(RCTPromiseRejectBlock)reject)
{
  CLLocation *location = [[CLLocation alloc] initWithLatitude:latitude.doubleValue longitude:longitude.doubleValue];
  CLGeocoder *geocoder = [CLGeocoder new];

  [geocoder reverseGeocodeLocation:location completionHandler:^(NSArray<CLPlacemark *> * _Nullable placemarks, NSError * _Nullable error) {
    if (error || placemarks.count == 0) {
      resolve((id)kCFNull);
      return;
    }

    CLPlacemark *placemark = placemarks.firstObject;
    NSString *address = [self formattedAddressFromPlacemark:placemark fallback:nil];
    if (address.length == 0) {
      resolve((id)kCFNull);
      return;
    }

    resolve(address);
  }];
}

RCT_REMAP_METHOD(geocodeAddress,
                 geocodeAddressText:(NSString *)addressText
                 resolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(RCTPromiseRejectBlock)reject)
{
  if (addressText.length == 0) {
    reject(@"INVALID_ADDRESS", @"La dirección está vacía", nil);
    return;
  }

  CLGeocoder *geocoder = [CLGeocoder new];
  [geocoder geocodeAddressString:addressText completionHandler:^(NSArray<CLPlacemark *> * _Nullable placemarks, NSError * _Nullable error) {
    if (error || placemarks.count == 0) {
      reject(@"GEOCODE_FAILED", @"No se pudo encontrar la dirección", error);
      return;
    }

    CLPlacemark *placemark = placemarks.firstObject;
    CLLocation *location = placemark.location;
    if (!location) {
      reject(@"GEOCODE_FAILED", @"No se encontraron coordenadas para la dirección", nil);
      return;
    }

    resolve(@{
      @"latitude": @(location.coordinate.latitude),
      @"longitude": @(location.coordinate.longitude),
      @"address": [self formattedAddressFromPlacemark:placemark fallback:addressText]
    });
  }];
}

RCT_REMAP_METHOD(searchAddressSuggestions,
                 searchAddressSuggestionsForText:(NSString *)searchText
                 resolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(RCTPromiseRejectBlock)reject)
{
  if (searchText.length < 3) {
    resolve(@[]);
    return;
  }

  CLGeocoder *geocoder = [CLGeocoder new];
  [geocoder geocodeAddressString:searchText completionHandler:^(NSArray<CLPlacemark *> * _Nullable placemarks, NSError * _Nullable error) {
    if (error || placemarks.count == 0) {
      resolve(@[]);
      return;
    }

    NSMutableArray *suggestions = [NSMutableArray array];
    NSMutableSet<NSString *> *seen = [NSMutableSet set];
    NSUInteger limit = MIN(6, placemarks.count);

    for (NSUInteger i = 0; i < limit; i++) {
      CLPlacemark *placemark = placemarks[i];
      CLLocation *location = placemark.location;
      if (!location) {
        continue;
      }

      NSString *address = [self formattedAddressFromPlacemark:placemark fallback:searchText];
      if (address.length == 0 || [seen containsObject:address]) {
        continue;
      }
      [seen addObject:address];

      [suggestions addObject:@{
        @"latitude": @(location.coordinate.latitude),
        @"longitude": @(location.coordinate.longitude),
        @"address": address
      }];
    }

    resolve(suggestions);
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
  options.networkAccessAllowed = YES;

  [[PHImageManager defaultManager] requestImageDataAndOrientationForAsset:asset
                                                                   options:options
                                                             resultHandler:^(NSData * _Nullable data,
                                                                             NSString * _Nullable dataUTI,
                                                                             CGImagePropertyOrientation orientation,
                                                                             NSDictionary * _Nullable info) {
    if (!data) {
      reject(@"IMAGE_LOAD_FAILED", @"No se pudo cargar la imagen", nil);
      return;
    }

    UIImage *fullImage = [UIImage imageWithData:data];
    if (!fullImage) {
      reject(@"IMAGE_DECODE_FAILED", @"No se pudo decodificar la imagen", nil);
      return;
    }

    CGFloat maxDimension = (CGFloat)maxSize.intValue;
    CGFloat width = fullImage.size.width;
    CGFloat height = fullImage.size.height;
    CGFloat scale = MIN(1.0, maxDimension / MAX(width, height));
    CGSize targetSize = CGSizeMake(width * scale, height * scale);

    UIGraphicsBeginImageContextWithOptions(targetSize, YES, 1.0);
    [fullImage drawInRect:CGRectMake(0, 0, targetSize.width, targetSize.height)];
    UIImage *resizedImage = UIGraphicsGetImageFromCurrentImageContext();
    UIGraphicsEndImageContext();

    NSData *imageData = UIImageJPEGRepresentation(resizedImage ?: fullImage, 0.8);
    if (!imageData) {
      reject(@"IMAGE_ENCODE_FAILED", @"No se pudo codificar la imagen", nil);
      return;
    }

    resolve([imageData base64EncodedStringWithOptions:0]);
  }];
}

RCT_REMAP_METHOD(exportImageForSharing,
                 exportImageForSharingForAsset:(NSString *)assetId
                 description:(NSString * _Nullable)description
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
  options.networkAccessAllowed = YES;

  [[PHImageManager defaultManager] requestImageDataAndOrientationForAsset:asset
                                                                   options:options
                                                             resultHandler:^(NSData * _Nullable data,
                                                                             NSString * _Nullable dataUTI,
                                                                             CGImagePropertyOrientation orientation,
                                                                             NSDictionary * _Nullable info) {
    if (!data) {
      reject(@"IMAGE_LOAD_FAILED", @"No se pudo cargar la imagen para compartir", nil);
      return;
    }

    CGImageSourceRef source = CGImageSourceCreateWithData((__bridge CFDataRef)data, NULL);
    if (!source) {
      reject(@"IMAGE_LOAD_FAILED", @"No se pudo leer la imagen para compartir", nil);
      return;
    }

    NSDictionary *originalMetadata = (__bridge_transfer NSDictionary *)CGImageSourceCopyPropertiesAtIndex(source, 0, NULL);
    NSMutableDictionary *mutableMetadata = [originalMetadata mutableCopy] ?: [NSMutableDictionary dictionary];

    NSString *finalDescription = description ?: @"";
    if (finalDescription.length == 0) {
      finalDescription = [self extractImageDescriptionFromMetadata:originalMetadata] ?: @"";
    }

    NSMutableDictionary *iptcDict = [mutableMetadata[(NSString *)kCGImagePropertyIPTCDictionary] mutableCopy] ?: [NSMutableDictionary dictionary];
    if (finalDescription.length > 0) {
      iptcDict[(NSString *)kCGImagePropertyIPTCCaptionAbstract] = finalDescription;
    } else {
      [iptcDict removeObjectForKey:(NSString *)kCGImagePropertyIPTCCaptionAbstract];
    }
    mutableMetadata[(NSString *)kCGImagePropertyIPTCDictionary] = iptcDict;

    NSMutableDictionary *tiffDict = [mutableMetadata[(NSString *)kCGImagePropertyTIFFDictionary] mutableCopy] ?: [NSMutableDictionary dictionary];
    if (finalDescription.length > 0) {
      tiffDict[(NSString *)kCGImagePropertyTIFFImageDescription] = finalDescription;
    } else {
      [tiffDict removeObjectForKey:(NSString *)kCGImagePropertyTIFFImageDescription];
    }
    mutableMetadata[(NSString *)kCGImagePropertyTIFFDictionary] = tiffDict;

    CFStringRef outputType = CGImageSourceGetType(source);
    if (!outputType) {
      outputType = kUTTypeJPEG;
    }
    if (UTTypeConformsTo(outputType, kUTTypePNG)) {
      outputType = CFSTR("public.heic");
    }

    NSString *extension = [self fileExtensionForImageType:outputType];
    NSString *tempFilename = [NSString stringWithFormat:@"fotodesc-share-%@.%@", NSUUID.UUID.UUIDString, extension];
    NSString *tempPath = [NSTemporaryDirectory() stringByAppendingPathComponent:tempFilename];
    NSURL *tempURL = [NSURL fileURLWithPath:tempPath];

    CGImageDestinationRef destination = CGImageDestinationCreateWithURL((__bridge CFURLRef)tempURL, outputType, 1, NULL);
    if (!destination) {
      CFRelease(source);
      reject(@"SHARE_EXPORT_FAILED", @"No se pudo preparar la imagen para compartir", nil);
      return;
    }

    CGImageRef image = CGImageSourceCreateImageAtIndex(source, 0, NULL);
    if (!image) {
      CFRelease(source);
      CFRelease(destination);
      reject(@"SHARE_EXPORT_FAILED", @"No se pudo generar la imagen para compartir", nil);
      return;
    }

    CGImageDestinationAddImage(destination, image, (__bridge CFDictionaryRef)mutableMetadata);
    BOOL finalized = CGImageDestinationFinalize(destination);

    CFRelease(image);
    CFRelease(source);
    CFRelease(destination);

    if (!finalized) {
      reject(@"SHARE_EXPORT_FAILED", @"No se pudo exportar la imagen para compartir", nil);
      return;
    }

    resolve(tempURL.absoluteString);
  }];
}

RCT_REMAP_METHOD(getOriginalImageURLForSharing,
                 getOriginalImageURLForSharingForAsset:(NSString *)assetId
                 resolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(RCTPromiseRejectBlock)reject)
{
  PHAsset *asset = [self assetForId:assetId];
  if (!asset) {
    reject(@"ASSET_NOT_FOUND", @"No se encontró la foto", nil);
    return;
  }

  PHContentEditingInputRequestOptions *options = [PHContentEditingInputRequestOptions new];
  options.networkAccessAllowed = YES;
  options.canHandleAdjustmentData = ^BOOL(PHAdjustmentData * _Nonnull adjustmentData) {
    return YES;
  };

  [asset requestContentEditingInputWithOptions:options
                             completionHandler:^(PHContentEditingInput * _Nullable input, NSDictionary * _Nonnull info) {
    NSURL *fullSizeURL = input.fullSizeImageURL;
    if (!fullSizeURL) {
      NSError *inputError = info[PHContentEditingInputErrorKey];
      if (inputError) {
        reject(@"SHARE_ORIGINAL_FAILED", @"No se pudo obtener el archivo original para compartir", inputError);
      } else {
        reject(@"SHARE_ORIGINAL_FAILED", @"No se pudo obtener el archivo original para compartir", nil);
      }
      return;
    }

    resolve(fullSizeURL.absoluteString);
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
