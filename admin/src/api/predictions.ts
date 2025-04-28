import api from './config';
import { API_URL } from '../config';

export interface Prediction {
  id: number;
  user_id: number;
  market_id: number;
  amount: number;
  predicted_outcome: string;
  status: string;
  created_at: string;
  updated_at: string;
  creator: {
    id: number;
    username: string;
  };
  market: {
    id: number;
    title: string;
    description: string;
    status: string;
  };
}

export interface PredictionCreate {
  user_id: number;
  market_id: number;
  amount: number;
  predicted_outcome: string;
}

export interface PredictionFilters {
  user_id?: number;
  market_id?: number;
  status?: string;
}

export const getPredictions = async (filters: PredictionFilters = {}): Promise<Prediction[]> => {
  const params = new URLSearchParams();
  if (filters.user_id) params.append('user_id', filters.user_id.toString());
  if (filters.market_id) params.append('market_id', filters.market_id.toString());
  if (filters.status) params.append('status', filters.status);

  const response = await api.get<Prediction[]>(`/predictions?${params.toString()}`);
  console.log(response);
  return response.data;
};

export const getPrediction = async (id: number): Promise<Prediction> => {
  const response = await api.get<Prediction>(`/predictions/${id}`);
  return response.data;
};

export const createPrediction = async (data: PredictionCreate): Promise<Prediction> => {
  const response = await api.post<Prediction>(`/predictions`, data);
  return response.data;
};

export const deletePrediction = async (id: number): Promise<void> => {
  await api.delete(`/predictions/${id}`);
};

export const updatePredictionStatus = async (id: number, status: string): Promise<Prediction> => {
  const response = await api.put<Prediction>(`/predictions/${id}/status?status=${status}`);
  return response.data;
}; 