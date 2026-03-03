# Instrucciones de Instalación y Configuración

## ⚙️ Configuración del Proyecto en Xcode

### 1. Configurar el Bridging Header

Después de crear el proyecto en Xcode, necesitas configurar el bridging header para Swift:

1. Abre el proyecto en Xcode:
   ```bash
   open ios/FotoDesc.xcworkspace
   ```

2. Selecciona el target **FotoDesc**

3. Ve a **Build Settings** → **Swift Compiler - General**

4. En **Objective-C Bridging Header**, añade:
   ```
   FotoDesc/FotoDesc-Bridging-Header.h
   ```

5. En **Defines Module**, establece a **YES**

### 2. Verificar permisos en Info.plist

El archivo `Info.plist` debe contener:

```xml
<key>NSPhotoLibraryUsageDescription</key>
<string>FotoDesc necesita acceso a tu galería de fotos...</string>

<key>NSPhotoLibraryAddUsageDescription</key>
<string>FotoDesc guarda las descripciones directamente...</string>
```

### 3. Añadir archivos Swift al proyecto

Si los archivos Swift no aparecen en Xcode:

1. Clic derecho en la carpeta **FotoDesc**
2. **Add Files to "FotoDesc"...**
3. Selecciona:
   - `PhotoMetadataManager.swift`
   - `PhotoMetadataManager.m`
4. Asegúrate de marcar **Copy items if needed**

## 📦 Instalación de Dependencias

### Paso 1: Dependencias de Node.js

```bash
# Instalar dependencias
npm install

# O con Yarn
yarn install
```

### Paso 2: CocoaPods (iOS)

```bash
# Navegar a la carpeta iOS
cd ios

# Instalar pods
pod install

# Si hay problemas, intenta:
pod deintegrate
pod install

# Volver a la raíz
cd ..
```

### Paso 3: Verificar instalación

```bash
# Listar archivos de iOS
ls -la ios/

# Deberías ver:
# - FotoDesc.xcworkspace (abre este, no el .xcodeproj)
# - Pods/
# - Podfile.lock
```

## 🚀 Ejecutar la Aplicación

### En Simulador de iOS

```bash
# Ejecutar en simulador por defecto
npm run ios

# Ejecutar en un simulador específico
npm run ios -- --simulator="iPhone 15 Pro"

# Listar simuladores disponibles
xcrun simctl list devices
```

### En Dispositivo Físico

1. Conecta tu iPhone al Mac
2. Abre Xcode: `open ios/FotoDesc.xcworkspace`
3. Selecciona tu dispositivo en la parte superior
4. Configura el **Bundle Identifier** único
5. Configura **Team** en Signing & Capabilities
6. Presiona **Run** (Cmd + R)

## 🔧 Configuración de OpenAI

### Obtener API Key

1. Ve a: https://platform.openai.com/api-keys
2. Crea una cuenta o inicia sesión
3. Crea una nueva API Key
4. Copia la key (comienza con `sk-...`)

### Configurar en la App

**Opción 1: Directamente en la app**
1. Abre FotoDesc en tu dispositivo
2. Toca el icono de ⚙️ (Configuración)
3. Pega tu API Key
4. Toca **Guardar**
5. Toca **Probar** para verificar

**Opción 2: Archivo .env (desarrollo)**
```bash
# Crear archivo .env
cp .env.example .env

# Editar y añadir tu key
OPENAI_API_KEY=sk-tu_key_real_aqui
```

## 🧪 Probar la App

### Verificar Permisos de Fotos

1. Al abrir la app por primera vez, acepta el permiso
2. Si lo rechazaste, ve a:
   - **Configuración** → **Privacidad** → **Fotos** → **FotoDesc**
   - Activa el acceso

### Verificar VoiceOver

1. **Activar VoiceOver:**
   - Configuración → Accesibilidad → VoiceOver → Activar
   - O triple clic en botón lateral (si está configurado)

2. **Probar lectura:**
   - Abre FotoDesc con VoiceOver activo
   - Navega con gestos de un dedo
   - Las fotos con descripción deben ser leídas

3. **Verificar en app Fotos nativa:**
   - Añade descripción a una foto en FotoDesc
   - Cierra FotoDesc
   - Abre la app Fotos de iOS
   - Navega a esa foto con VoiceOver
   - Debe leer: "Imagen: [tu descripción]"

## 🐛 Solución de Problemas Comunes

### Error: "Unable to boot simulator"

```bash
# Reiniciar los simuladores
xcrun simctl shutdown all
xcrun simctl erase all
```

### Error: "Module 'PhotoMetadataManager' not found"

1. Verifica que el bridging header esté configurado
2. Limpia el build:
   ```bash
   cd ios
   xcodebuild clean
   pod deintegrate
   pod install
   cd ..
   npm run ios
   ```

### Error: Metro Bundler no inicia

```bash
# Limpiar caché de Metro
npm start -- --reset-cache

# O manualmente:
watchman watch-del-all
rm -rf node_modules
npm install
```

### Error: "Photos permission denied"

1. Desinstala la app del simulador/dispositivo
2. Reinstala: `npm run ios`
3. Al abrir, acepta los permisos cuando se soliciten

### Las descripciones no se guardan

1. **Verifica permisos:** Configuración → Privacidad → Fotos
2. **Revisa logs en Xcode:**
   - Abre: `open ios/FotoDesc.xcworkspace`
   - Ejecuta y mira la consola para errores
3. **Verifica que la foto esté en el carrete:**
   - Solo las fotos en la biblioteca principal se pueden editar

### OpenAI devuelve error

**Error 401 (Unauthorized):**
- API Key inválida o expirada
- Obtén una nueva en platform.openai.com

**Error 429 (Rate Limit):**
- Has excedido el límite de solicitudes
- Espera unos minutos o revisa tu plan

**Error 500 (Server Error):**
- Problema temporal de OpenAI
- Intenta de nuevo más tarde

## 📊 Verificar Estado del Proyecto

### Estructura de archivos correcta

```bash
# Verificar que existen los archivos clave
ls -la src/App.tsx
ls -la src/screens/
ls -la ios/FotoDesc/PhotoMetadataManager.swift
ls -la ios/Podfile
```

### Dependencias instaladas

```bash
# Verificar node_modules
ls -la node_modules/ | wc -l
# Debería mostrar >100

# Verificar pods
ls -la ios/Pods/ | wc -l
# Debería mostrar >10
```

### Build exitoso

```bash
# Build sin ejecutar
cd ios
xcodebuild -workspace FotoDesc.xcworkspace \
           -scheme FotoDesc \
           -configuration Debug \
           build
```

## 🔄 Actualizar el Proyecto

### Actualizar dependencias de npm

```bash
npm update
```

### Actualizar pods

```bash
cd ios
pod update
cd ..
```

### Actualizar React Native

```bash
# Ver version actual
npm list react-native

# Actualizar a específica
npm install react-native@0.73.x
cd ios && pod install && cd ..
```

## 📱 Preparar para Producción

### 1. Cambiar Bundle ID

En Xcode, cambia el Bundle Identifier:
```
com.tuempresa.fotodesc
```

### 2. Configurar Signing

1. Abre Xcode
2. Selecciona el target **FotoDesc**
3. Ve a **Signing & Capabilities**
4. Selecciona tu **Team**
5. Asegúrate de que **Automatically manage signing** esté activo

### 3. Build de Release

```bash
# Build para dispositivo
cd ios
xcodebuild -workspace FotoDesc.xcworkspace \
           -scheme FotoDesc \
           -configuration Release \
           -destination 'generic/platform=iOS' \
           build
```

### 4. Crear Archive para App Store

1. En Xcode: **Product** → **Archive**
2. Cuando termine, se abrirá el **Organizer**
3. Selecciona el archive
4. Click en **Distribute App**
5. Sigue el asistente para subir a App Store Connect

## 📚 Recursos Adicionales

- [React Native Docs](https://reactnative.dev/)
- [Photos Framework](https://developer.apple.com/documentation/photokit)
- [VoiceOver Programming Guide](https://developer.apple.com/accessibility/ios/)
- [OpenAI Vision API](https://platform.openai.com/docs/guides/vision)

---

**¿Todo configurado?** ¡Ya puedes ejecutar: `npm run ios` 🚀
