export interface User {
  id: number;
  username: string;
  email: string | null;
  pi_user_id?: string;
  role: 'admin' | 'user';
  balance: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  phone_number?: string | null;
  avatar_url?: string | null;
}

export interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  loginWithPi: () => Promise<void>;
  loginWithEmail: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
} 