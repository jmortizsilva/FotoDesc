const {getDefaultConfig, mergeConfig} = require('@react-native/metro-config');

/**
 * Metro config that extends React Native defaults.
 * Keeping defaults avoids asset pipeline regressions in CI/EAS builds.
 */
const defaultConfig = getDefaultConfig(__dirname);

const config = {
  transformer: {
    getTransformOptions: async () => ({
      transform: {
        experimentalImportSupport: false,
        inlineRequires: true,
      },
    }),
  },
};

module.exports = mergeConfig(defaultConfig, config);
