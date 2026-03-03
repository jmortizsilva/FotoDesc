// Type definitions for FotoDesc iOS App

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

export interface OpenAIImageMessage {
  role: 'user';
  content: Array<{
    type: 'text' | 'image_url';
    text?: string;
    image_url?: {
      url: string;
    };
  }>;
}

export interface OpenAIResponse {
  choices: Array<{
    message: {
      content: string;
    };
  }>;
}

export type FilterType = 'all' | 'with-description' | 'without-description';

export type RootStackParamList = {
  Gallery: undefined;
  PhotoDetail: {
    photo: PhotoAsset;
  };
  Settings: undefined;
};

declare global {
  namespace ReactNavigation {
    interface RootParamList extends RootStackParamList {}
  }
}
