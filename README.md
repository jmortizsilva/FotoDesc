# FotoDesc iOS - React Native

Aplicación iOS para añadir descripciones accesibles a fotos, guardándolas en metadatos EXIF (campo ImageDescription) para que VoiceOver las lea automáticamente.

## 📋 Características

- ✅ **Visualización de galería** del iPhone con indicadores visuales
- ✅ **Lectura automática con VoiceOver** en app Fotos nativa y en FotoDesc
- ✅ **Edición manual** de descripciones accesibles
- ✅ **Generación automática** con OpenAI Vision API
- ✅ **Guardado en metadatos EXIF** (campo ImageDescription)
- ✅ **Filtrado** de fotos (todas/con descripción/sin descripción)
- ✅ **Eliminación** de fotos desde la app
- ✅ **100% accesible** con VoiceOver

## 🏗️ Arquitectura

### Frontend (React Native)
- **React Navigation** para navegación entre pantallas
- **TypeScript** para type-safety
- Componentes optimizados para accesibilidad

### Backend (Módulo Nativo iOS)
- **Swift** con Photos Framework
- Bridge a React Native via Objective-C
- Lectura/escritura de `PHAsset.accessibilityDescription`

### Servicios
- **OpenAI Vision API** para generación automática de descripciones
- **AsyncStorage** para configuración local

## 📦 Estructura del Proyecto

```
FotoDesc/
├── src/
│   ├── App.tsx                           # Navegación principal
│   ├── screens/
│   │   ├── GalleryScreen.tsx            # Grid de fotos
│   │   ├── PhotoDetailScreen.tsx        # Detalle y edición
│   │   └── SettingsScreen.tsx           # Configuración API
│   ├── modules/
│   │   └── PhotoMetadataManager.ts      # Interface del módulo nativo
│   └── services/
│       └── OpenAIService.ts             # Cliente de OpenAI
├── ios/
│   ├── FotoDesc/
│   │   ├── PhotoMetadataManager.swift   # Módulo nativo
│   │   ├── PhotoMetadataManager.m       # Bridge Obj-C
│   │   └── Info.plist                   # Permisos de fotos
│   └── Podfile                          # Dependencias CocoaPods
├── package.json
└── tsconfig.json
```

## 🚀 Instalación

### Requisitos previos
- Node.js 18+
- Xcode 14+
- CocoaPods instalado
- Cuenta de OpenAI con API Key (opcional, solo para IA)

### Pasos de instalación

1. **Instalar dependencias de Node:**
```bash
npm install
```

2. **Instalar pods de iOS:**
```bash
cd ios
pod install
cd ..
```

3. **Configurar API Key de OpenAI (opcional):**
```bash
cp .env.example .env
# Editar .env y añadir tu API Key
```

4. **Ejecutar en simulador/dispositivo iOS:**
```bash
npm run ios
```

## 🔧 Configuración

### Permisos de iOS

La app solicita permisos de lectura/escritura a la galería de fotos. Los textos descriptivos están en `ios/FotoDesc/Info.plist`:

- `NSPhotoLibraryUsageDescription`
- `NSPhotoLibraryAddUsageDescription`

### API de OpenAI

Para usar la generación automática:

1. Obtén una API Key en: https://platform.openai.com/api-keys
2. En la app, ve a **Configuración** (⚙️)
3. Pega tu API Key y presiona **Guardar**
4. Prueba la conexión con el botón **Probar**

## 📱 Uso

### Añadir descripción manual

1. Abre la app
2. Selecciona una foto
3. Escribe la descripción en el campo
4. Presiona **Guardar**
5. ✅ VoiceOver ya leerá esta descripción en Fotos nativa

### Generar con IA

1. Selecciona una foto sin descripción
2. Presiona **🤖 Generar con IA**
3. Revisa la descripción generada
4. Edita si es necesario
5. Presiona **Guardar**

### Eliminar foto

1. Selecciona una foto
2. Presiona **🗑️ Eliminar foto**
3. Confirma la eliminación

## 🎯 Campo EXIF Utilizado

La app guarda las descripciones en:

- **Campo EXIF:** `ImageDescription` (Tag 0x010E)
- **API de iOS:** `PHAsset.accessibilityDescription`
- **Resultado:** VoiceOver lee automáticamente en toda la app Fotos

⚠️ **No se usa:** `UserComment` ni otros campos de metadatos

## ♿ Accesibilidad

### Características de accesibilidad implementadas:

- ✅ Todos los elementos con `accessibilityLabel`
- ✅ Roles semánticos (`button`, `imagebutton`, etc.)
- ✅ Estados accesibles (`selected`, `disabled`)
- ✅ Navegación por gestos de VoiceOver
- ✅ Feedback auditivo en operaciones críticas
- ✅ Elementos decorativos ocultos con `accessibilityElementsHidden`

### Pruebas con VoiceOver:

1. Activa VoiceOver: Configuración → Accesibilidad → VoiceOver
2. Abre FotoDesc
3. Navega con gestos de un dedo
4. Todas las fotos con descripción las verbalizará VoiceOver

## 🔍 Cómo Funciona Técnicamente

### Flujo de guardado de descripción:

```
Usuario escribe descripción
    ↓
React Native (JavaScript)
    ↓
RCTBridge
    ↓
PhotoMetadataManager.swift
    ↓
PHPhotoLibrary.performChanges()
    ↓
PHAssetChangeRequest.accessibilityDescription = "..."
    ↓
iOS guarda en metadatos EXIF
    ↓
✅ Descripción disponible en toda la app Fotos
```

### Flujo de generación con IA:

```
Usuario presiona "Generar con IA"
    ↓
PhotoMetadataManager obtiene imagen en base64
    ↓
OpenAIService envía a Vision API
    ↓
OpenAI devuelve descripción
    ↓
Se muestra en campo de texto
    ↓
Usuario revisa/edita
    ↓
Guarda → se escribe en EXIF
```

## 🧪 Testing

### Verificar que las descripciones funcionan:

1. Añade descripción a una foto en FotoDesc
2. Cierra FotoDesc completamente
3. Abre la app **Fotos** nativa de iOS
4. Activa VoiceOver
5. Navega a esa foto
6. **Resultado esperado:** VoiceOver dice "Imagen: [tu descripción]"

## 📝 Dependencias Principales

```json
{
  "react-native": "0.73.2",
  "@react-navigation/native": "^6.1.9",
  "@react-native-async-storage/async-storage": "^1.21.0",
  "axios": "^1.6.5"
}
```

## 🛠️ Desarrollo

### Estructura de módulos nativos:

- `PhotoMetadataManager.swift`: Lógica Swift
- `PhotoMetadataManager.m`: Bridge Objective-C
- `FotoDesc-Bridging-Header.h`: Header para Swift-ObjC

### Añadir nuevas funciones al módulo:

1. Añade método en `.swift`
2. Expón en `.m` con `RCT_EXTERN_METHOD`
3. Actualiza interface TypeScript en `PhotoMetadataManager.ts`
4. Úsalo desde React Native

## 🐛 Troubleshooting

### "No se encontró el módulo PhotoMetadataManager"
```bash
cd ios
pod install
cd ..
npm run ios
```

### "Permission denied" al acceder a fotos
- Verifica que Info.plist tenga los permisos
- Reinstala la app en el simulador
- Revisa en Configuración → Privacidad → Fotos

### La descripción no se guarda
- Verifica permisos de escritura
- Revisa logs de Xcode para errores de PHPhotoLibrary
- Asegúrate de que la foto esté en la galería principal

### OpenAI devuelve error 401
- Verifica que la API Key sea válida
- Prueba la conexión en Configuración
- Revisa que tengas créditos en tu cuenta OpenAI

## 📄 Licencia

Este proyecto es de código abierto para fines educativos y de accesibilidad.

## 👨‍💻 Autor

Desarrollado para mejorar la accesibilidad de las fotos en iOS mediante descripciones en metadatos EXIF.

## 🙏 Agradecimientos

- A Ramón Corominas por la idea original de FotoDesc Windows
- A la comunidad de accesibilidad de iOS
- A OpenAI por la API Vision

---

**¿Preguntas o sugerencias?** Abre un issue en el repositorio.
