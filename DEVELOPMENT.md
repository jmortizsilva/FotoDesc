# Guía de Desarrollo y Testing

## 🧑‍💻 Entorno de Desarrollo

### Requisitos

- **macOS** 12.0 o superior (Monterey+)
- **Xcode** 14.0 o superior
- **Node.js** 18.0 o superior
- **CocoaPods** 1.11.0 o superior
- **Watchman** (recomendado)

### Configuración del Editor

#### VS Code (Recomendado)

Extensiones recomendadas:

```json
{
  "recommendations": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "msjsdiag.vscode-react-native"
  ]
}
```

#### Configuración de workspace

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

## 🧪 Testing

### Testing Manual con VoiceOver

#### Test 1: Navegación en Galería

```
Pasos:
1. Activa VoiceOver: Triple clic en botón lateral
2. Abre FotoDesc
3. Navega con gestos de un dedo por la galería

Resultado esperado:
- Cada foto debe verbalizar su descripción si existe
- Las fotos sin descripción deben indicarlo
- Los filtros deben ser navegables y su estado sea anunciado
```

#### Test 2: Añadir Descripción

```
Pasos:
1. Con VoiceOver activo, selecciona una foto
2. Enfoca el campo de texto
3. Doble tap para editar
4. Escribe una descripción usando dictado o teclado
5. Navega al botón "Guardar"
6. Doble tap

Resultado esperado:
- El campo debe anunciar "Campo de descripción"
- El botón debe anunciar "Guardar descripción"
- Debe haber feedback de confirmación
```

#### Test 3: Verificación en App Fotos Nativa

```
Pasos:
1. Añade descripción a una foto en FotoDesc
2. Fuerza cerrar FotoDesc (deslizar hacia arriba)
3. Abre app Fotos de iOS
4. Navega a la misma foto con VoiceOver

Resultado esperado:
- VoiceOver debe leer: "Imagen: [tu descripción]"
- La descripción debe persistir incluso después de reiniciar
```

#### Test 4: Generación con IA

```
Pasos:
1. Configura API Key en Settings
2. Selecciona foto sin descripción
3. Toca "Generar con IA"
4. Espera respuesta

Resultado esperado:
- Indicador de carga debe ser accesible
- Descripción generada debe aparecer en el campo
- Debe poder editarse antes de guardar
```

#### Test 5: Eliminación de Foto

```
Pasos:
1. Selecciona una foto
2. Toca "Eliminar foto"
3. Confirma eliminación

Resultado esperado:
- Debe haber alerta de confirmación accesible
- La foto debe eliminarse de la galería del sistema
- Debe regresar a la pantalla anterior
```

### Testing de Módulo Nativo

#### Test de Permisos

```swift
// En Xcode, añade test unitario:

func testPhotoLibraryPermission() {
    let expectation = self.expectation(description: "Permission")
    
    PhotoMetadataManager().requestPhotoLibraryPermission { granted in
        XCTAssertTrue(granted, "Permission should be granted")
        expectation.fulfill()
    } rejecter: { _, _, _ in
        XCTFail("Permission request failed")
    }
    
    waitForExpectations(timeout: 5)
}
```

#### Test de Lectura de Fotos

```swift
func testGetAllPhotos() {
    let expectation = self.expectation(description: "Fetch photos")
    
    PhotoMetadataManager().getAllPhotos { photos in
        XCTAssertNotNil(photos)
        XCTAssertTrue((photos as? [[String: Any]])?.count ?? 0 > 0)
        expectation.fulfill()
    } rejecter: { _, _, _ in
        XCTFail("Failed to fetch photos")
    }
    
    waitForExpectations(timeout: 10)
}
```

#### Test de Guardado de Descripción

```swift
func testSetImageDescription() {
    let expectation = self.expectation(description: "Set description")
    let testAssetId = "test-asset-id" // Reemplazar con ID real
    let testDescription = "Test description for accessibility"
    
    PhotoMetadataManager().setImageDescription(
        testAssetId,
        description: testDescription
    ) { success in
        XCTAssertTrue(success as? Bool ?? false)
        expectation.fulfill()
    } rejecter: { _, _, _ in
        XCTFail("Failed to set description")
    }
    
    waitForExpectations(timeout: 5)
}
```

## 🐛 Debugging

### Debug de React Native

#### Habilitar Debug Menu

En el simulador: `Cmd + D`
En dispositivo físico: Agitar el dispositivo

Opciones útiles:
- **Enable Fast Refresh**: Auto-reload al guardar
- **Show Performance Monitor**: Ver FPS y uso de memoria
- **Debug**: Abre Chrome DevTools

#### Logs

```bash
# Ver logs de React Native
npm start

# Ver logs nativos de iOS (en otra terminal)
npx react-native log-ios
```

### Debug de Swift

#### Breakpoints en Xcode

1. Abre: `open ios/FotoDesc.xcworkspace`
2. Abre `PhotoMetadataManager.swift`
3. Click en el número de línea para añadir breakpoint
4. Ejecuta la app desde Xcode (Cmd + R)
5. Cuando llegue al breakpoint, inspecciona variables

#### Print Debugging

```swift
// En PhotoMetadataManager.swift
func setImageDescription(...) {
    print("🔍 DEBUG: assetId = \(assetId)")
    print("🔍 DEBUG: description = \(description)")
    
    // Tu código...
    
    print("✅ DEBUG: Description saved successfully")
}
```

#### Logs en consola de Xcode

Con la app corriendo desde Xcode, verás todos los logs en la parte inferior.

Filtrar logs:
- Escribe "FotoDesc" en el campo de búsqueda
- O "🔍" si usas emojis en tus logs

### Debug de OpenAI API

#### Interceptar requests

```typescript
// En OpenAIService.ts
async generateImageDescription(imageBase64: string): Promise<string> {
  console.log('📤 Sending request to OpenAI...');
  console.log('📏 Image size:', imageBase64.length, 'characters');
  
  try {
    const response = await axios.post(...);
    console.log('📥 OpenAI response:', response.data);
    return response.data.choices[0].message.content;
  } catch (error: any) {
    console.error('❌ OpenAI error:', error.response?.data || error.message);
    throw error;
  }
}
```

#### Probar API independientemente

```bash
# Test directo con curl
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4-vision-preview",
    "messages": [{
      "role": "user",
      "content": [{
        "type": "text",
        "text": "Describe esta imagen"
      }]
    }],
    "max_tokens": 300
  }'
```

## 📊 Performance

### Analizar Performance con Instruments

1. En Xcode: **Product** → **Profile** (Cmd + I)
2. Selecciona template:
   - **Time Profiler**: Para CPU
   - **Allocations**: Para memoria
   - **Leaks**: Para memory leaks
3. Ejecuta la app y usa normalmente
4. Detén y analiza resultados

### Optimizar carga de imágenes

La app usa `PHImageManager` con opciones optimizadas:

```swift
let options = PHImageRequestOptions()
options.deliveryMode = .fastFormat  // Para thumbnails
options.resizeMode = .fast
```

Para imágenes grandes (envío a IA):

```swift
options.deliveryMode = .highQualityFormat
options.resizeMode = .exact
let targetSize = CGSize(width: 1024, height: 1024) // Límite para API
```

## 🔄 Workflow de Desarrollo

### Feature Branch

```bash
# Crear rama para nueva feature
git checkout -b feature/nombre-feature

# Desarrollar y commit
git add .
git commit -m "feat: descripción de la feature"

# Push
git push origin feature/nombre-feature
```

### Commits Semánticos

Usar [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Nueva funcionalidad
- `fix:` Corrección de bug
- `docs:` Documentación
- `style:` Formato, no afecta código
- `refactor:` Refactorización
- `test:` Tests
- `chore:` Tareas de mantenimiento

Ejemplos:
```
feat: añadir filtro de fotos por fecha
fix: corregir crash al eliminar foto sin descripción
docs: actualizar README con instrucciones de VoiceOver
```

## 🚀 Build y Deploy

### Build de Debug

```bash
npm run ios
```

### Build de Release (local)

```bash
# Desde línea de comandos
npx react-native run-ios --configuration Release

# O desde Xcode:
# 1. Selecciona scheme "FotoDesc"
# 2. Edit Scheme → Run → Build Configuration → Release
# 3. Cmd + R
```

### Preparar para TestFlight

1. **Incrementar versión:**
   - En Xcode: Target → General → Version & Build

2. **Archive:**
   - Product → Archive
   - Espera a que termine

3. **Validar:**
   - En Organizer, click "Validate App"
   - Espera validación

4. **Distribuir:**
   - Click "Distribute App"
   - Selecciona "App Store Connect"
   - Sigue el asistente

## 📝 Checklist antes de Release

- [ ] Todas las features funcionan correctamente
- [ ] Testing con VoiceOver completo
- [ ] Verificar descripciones en app Fotos nativa
- [ ] API de OpenAI funciona (con key válida)
- [ ] Sin memory leaks (verificado con Instruments)
- [ ] README actualizado
- [ ] Versión incrementada en Info.plist
- [ ] Screenshots actualizados para App Store
- [ ] Descripción de App Store traducida
- [ ] Privacy policy actualizada

## 🎯 Próximas Mejoras

### Features planeadas:

1. **Búsqueda de fotos** por descripción
2. **Edición batch** de múltiples fotos
3. **Historial** de descripciones generadas con IA
4. **Exportar** fotos con descripciones a formato accesible
5. **Compartir** descripciones entre dispositivos (iCloud)
6. **Soporte para videos** (añadir descripciones a videos)
7. **Integración con Shortcuts** de iOS
8. **Widget** para estadísticas de fotos descritas

### Mejoras técnicas:

1. **Caché de thumbnails** para mejor performance
2. **Sincronización en background** con iCloud
3. **Tests unitarios** completos
4. **CI/CD** con GitHub Actions
5. **Localization** a múltiples idiomas

---

**¿Encontraste un bug?** Abre un issue con:
- Pasos para reproducir
- Resultado esperado vs actual
- Logs relevantes
- Versión de iOS y dispositivo
