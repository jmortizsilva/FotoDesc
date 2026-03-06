import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const OPENAI_API_KEY_STORAGE = '@openai_api_key';

export class OpenAIService {
  private apiKey: string | null = null;

  async loadApiKey(): Promise<string | null> {
    try {
      this.apiKey = await AsyncStorage.getItem(OPENAI_API_KEY_STORAGE);
      return this.apiKey;
    } catch (error) {
      console.error('Error loading API key:', error);
      return null;
    }
  }

  async saveApiKey(key: string): Promise<void> {
    this.apiKey = key;
    await AsyncStorage.setItem(OPENAI_API_KEY_STORAGE, key);
  }

  async generateImageDescription(imageBase64: string): Promise<string> {
    if (!this.apiKey) {
      await this.loadApiKey();
      if (!this.apiKey) {
        throw new Error('API Key de OpenAI no configurada');
      }
    }

    try {
      const response = await axios.post(
        'https://api.openai.com/v1/chat/completions',
        {
          model: 'gpt-4.1-mini',
          messages: [
            {
              role: 'user',
              content: [
                {
                  type: 'text',
                  text: 'Describe esta imagen de forma concisa y accesible para personas con discapacidad visual. Incluye los elementos principales, colores destacados y el contexto. Máximo 2-3 frases.',
                },
                {
                  type: 'image_url',
                  image_url: {
                    url: `data:image/jpeg;base64,${imageBase64}`,
                  },
                },
              ],
            },
          ],
          max_tokens: 300,
        },
        {
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${this.apiKey}`,
          },
        },
      );

      return response.data.choices[0].message.content;
    } catch (error: any) {
      console.error('Error generating description:', error);
      if (error.response?.status === 401) {
        throw new Error('API Key inválida');
      }
      const apiMessage = error.response?.data?.error?.message;
      if (apiMessage) {
        throw new Error(apiMessage);
      }
      throw new Error('Error al generar descripción con IA');
    }
  }

  async testApiKey(): Promise<boolean> {
    try {
      await axios.get('https://api.openai.com/v1/models', {
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
        },
      });
      return true;
    } catch {
      return false;
    }
  }
}

export default new OpenAIService();
