import api from './config';

export interface ReferralData {
  referral_code: string;
  referral_url: string;
  referral_earnings: number;
  total_referrals: number;
  referred_by: {
    id: number;
    username: string;
    email: string;
  } | null;
}

export interface ReferralTransaction {
  id: number;
  amount: number;
  created_at: string;
  referred_user: {
    id: number;
    username: string;
    email: string;
  };
}

export interface ReferralStats {
  total_referrals: number;
  total_earnings: number;
  recent_referrals: ReferralTransaction[];
}

// Get current user's referral information
export const getMyReferral = async (): Promise<ReferralData> => {
  const response = await api.get<ReferralData>('/referral/my-referral');
  return response.data;
};

// Get referral statistics
export const getReferralStats = async (): Promise<ReferralStats> => {
  const response = await api.get<ReferralStats>('/referral/stats');
  return response.data;
};

// Get referral transactions
export const getReferralTransactions = async (params?: {
  skip?: number;
  limit?: number;
}): Promise<ReferralTransaction[]> => {
  const response = await api.get<ReferralTransaction[]>('/referral/transactions', { params });
  return response.data;
}; 