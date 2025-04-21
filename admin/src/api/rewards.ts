import axios from 'axios';
import { API_URL } from '../config';

export interface Reward {
  id: number;
  user_id: number;
  market_id: number;
  prediction_id: number;
  amount: number;
  status: string;
  created_at: string;
  updated_at: string;
  user: {
    id: number;
    username: string;
    email: string;
  };
  market: {
    id: number;
    title: string;
    description: string;
  };
  prediction: {
    id: number;
    predicted_outcome: string;
    amount: number;
  };
}

export interface RewardFilters {
  user_id?: number;
  market_id?: number;
  prediction_id?: number;
  start_date?: string;
  end_date?: string;
}

export const getRewards = async (filters: RewardFilters = {}): Promise<Reward[]> => {
  const params = new URLSearchParams();
  if (filters.user_id) params.append('user_id', filters.user_id.toString());
  if (filters.market_id) params.append('market_id', filters.market_id.toString());
  if (filters.prediction_id) params.append('prediction_id', filters.prediction_id.toString());
  if (filters.start_date) params.append('start_date', filters.start_date);
  if (filters.end_date) params.append('end_date', filters.end_date);

  const response = await axios.get<Reward[]>(`${API_URL}/rewards?${params.toString()}`);
  return response.data;
};

export const getReward = async (id: number): Promise<Reward> => {
  const response = await axios.get<Reward>(`${API_URL}/rewards/${id}`);
  return response.data;
}; 