import api from './config';

interface PiLoginCredentials {
  auth_token: string;
}

interface EmailLoginCredentials {
  email: string;
  password: string;
}

interface RegisterCredentials {
  email: string;
  password: string;
  username?: string;
}

interface LoginResponse {
  user_id: number;
  access_token: string;
  token_type: string;
  username: string;
  email: string | null;
  phone_number: string | null;
  role: string;
  created_at: string;
  updated_at: string;
  avatar_url: string | null;
  first_name: string | null;
  last_name: string | null;
}

export const register = async (credentials: RegisterCredentials): Promise<LoginResponse> => {
  const response = await api.post<LoginResponse>('/auth/register', credentials);
  return response.data;
};

export const loginWithPi = async (credentials: PiLoginCredentials): Promise<LoginResponse> => {
  const response = await api.post<LoginResponse>('/auth/login', credentials);
  return response.data;
};

export const loginWithEmail = async (credentials: EmailLoginCredentials): Promise<LoginResponse> => {
  const response = await api.post<LoginResponse>('/auth/email/login', credentials);
  return response.data;
};

export const logout = async (): Promise<void> => {
  await api.post('/api/auth/logout');
  localStorage.removeItem('token');
}; 