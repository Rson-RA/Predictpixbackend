import axios from 'axios';
import { API_URL } from '../config';

export interface Transaction {
  id: number;
  user_id: number;
  amount: number;
  status: string;
  transaction_type: string;
  created_at: string;
  updated_at: string;
  user: {
    id: number;
    username: string;
    email: string;
  };
}

export interface TransactionFilters {
  user_id?: number;
  status?: string;
  start_date?: string;
  end_date?: string;
}

export const getTransactions = async (filters: TransactionFilters = {}): Promise<Transaction[]> => {
  const params = new URLSearchParams();
  if (filters.user_id) params.append('user_id', filters.user_id.toString());
  if (filters.status) params.append('status', filters.status);
  if (filters.start_date) params.append('start_date', filters.start_date);
  if (filters.end_date) params.append('end_date', filters.end_date);

  const response = await axios.get<Transaction[]>(`${API_URL}/transactions?${params.toString()}`);
  return response.data;
};

export const getTransaction = async (id: number): Promise<Transaction> => {
  const response = await axios.get<Transaction>(`${API_URL}/transactions/${id}`);
  return response.data;
}; 