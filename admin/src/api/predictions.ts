import axios from 'axios';
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

  const response = await axios.get<Prediction[]>(`${API_URL}/predictions?${params.toString()}`);
  return response.data;
};

export const getPrediction = async (id: number): Promise<Prediction> => {
  const response = await axios.get<Prediction>(`${API_URL}/predictions/${id}`);
  return response.data;
};

export const createPrediction = async (data: PredictionCreate): Promise<Prediction> => {
  const response = await axios.post<Prediction>(`${API_URL}/predictions`, data);
  return response.data;
};

export const deletePrediction = async (id: number): Promise<void> => {
  await axios.delete(`${API_URL}/predictions/${id}`);
}; 