import api from './config';

export interface Market {
  id: number;
  title: string;
  description: string;
  end_time: string;
  resolution_time: string;
  status: 'pending' | 'active' | 'closed' | 'settled' | 'cancelled';
  total_pool: number;
  yes_pool: number;
  no_pool: number;
  correct_outcome?: string;
  creator_fee_percentage: number;
  platform_fee_percentage: number;
  creator: {
    id: number;
    username: string;
  };
  created_at: string;
  updated_at: string;
}

export interface CreateMarketData {
  title: string;
  description: string;
  end_time: string;
  resolution_time: string;
  creator_fee_percentage: number;
  platform_fee_percentage: number;
}

export interface UpdateMarketData extends Partial<CreateMarketData> {
  status?: 'pending' | 'active' | 'closed' | 'settled' | 'cancelled';
}

// Get all markets
export const getMarkets = async (): Promise<Market[]> => {
  const response = await api.get<Market[]>('/markets');
  return response.data;
};

// Get a single market
export const getMarket = async (id: number): Promise<Market> => {
  const response = await api.get<Market>(`/markets/${id}`);
  return response.data;
};

// Create a new market
export const createMarket = async (data: CreateMarketData): Promise<Market> => {
  const response = await api.post<Market>('/markets/create', data);
  return response.data;
};

// Update a market
export const updateMarket = async (id: number, data: UpdateMarketData): Promise<Market> => {
  const response = await api.patch<Market>(`/markets/${id}`, data);
  return response.data;
};

// Delete a market
export const deleteMarket = async (id: number): Promise<{ status: string; message: string }> => {
  const response = await api.delete<{ status: string; message: string }>(`/markets/${id}`);
  return response.data;
};

// Approve a market
export const approveMarket = async (id: number): Promise<Market> => {
  const response = await api.post<Market>(`/markets/${id}/approve`);
  return response.data;
};

// Reject a market
export const rejectMarket = async (id: number, reason: string): Promise<Market> => {
  const response = await api.post<Market>(`/markets/${id}/reject`, { reason });
  return response.data;
}; 