import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import PiNetwork from '../api/pi-network';
import type { AuthResult } from '../types/pi-network';
import axios from 'axios';
import { loginWithPi as authLoginPi, loginWithEmail as authLoginEmail, register as authRegister } from '../api/auth';
import { User } from '../types/auth';

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  loginWithEmail: (email: string, password: string) => Promise<void>;
  loginWithPi: () => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const validateToken = async (token: string): Promise<boolean> => {
    try {
      const response = await axios.get(process.env.REACT_APP_API_URL + '/auth/validate', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      return response.status === 200;
    } catch (error) {
      return false;
    }
  };

  // Check for existing session on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('auth_token');
        const userData = localStorage.getItem('user_data');
        
        if (token && userData) {
          // Validate the token
          const isValid = await validateToken(token);
          
          if (isValid) {
            // Set default auth header
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            
            // Parse and set user data
            const parsedUserData = JSON.parse(userData);
            console.log(parsedUserData);
            setUser(parsedUserData);
            setIsAuthenticated(true);
          } else {
            // Token is invalid, clear the session
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_data');
            delete axios.defaults.headers.common['Authorization'];
          }
        }
      } catch (error) {
        console.error('Error checking authentication:', error);
        // Clear potentially corrupted data
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
        delete axios.defaults.headers.common['Authorization'];
        setLoading(false)
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const loginWithEmail = async (email: string, password: string) => {
    try {
      const response = await authLoginEmail({ 
        email, 
        password 
      });

      const userData: User = {
        id: response.id,
        username: response.username,
        email: response.email,
        role: response.role as 'admin' | 'user',
        balance: 0,
        is_active: true,
        created_at: response.created_at,
        updated_at: response.updated_at,
        phone_number: response.phone_number,
        avatar_url: response.avatar_url
      };
      
      localStorage.setItem('auth_token', response.access_token);
      localStorage.setItem('user_data', JSON.stringify(userData));
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.access_token}`;
      setIsAuthenticated(true);
      setUser(userData);
      navigate('/dashboard');
    } catch (error) {
      console.error('Email authentication failed:', error);
      throw error;
    }
  };

  const loginWithPi = async () => {
    try {
      const auth = await PiNetwork.authenticate();
      const response = await authLoginPi({ 
        auth_token: auth.accessToken 
      });

      const userData: User = {
        id: response.id,
        username: response.username,
        email: response.email,
        pi_user_id: auth.user.uid,
        role: response.role as 'admin' | 'user',
        balance: 0,
        is_active: true,
        created_at: response.created_at,
        updated_at: response.updated_at,
        phone_number: response.phone_number,
        avatar_url: response.avatar_url
      };
      
      localStorage.setItem('auth_token', response.access_token);
      localStorage.setItem('user_data', JSON.stringify(userData));
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.access_token}`;
      setIsAuthenticated(true);
      setUser(userData);
      navigate('/dashboard');
    } catch (error) {
      console.error('Pi authentication failed:', error);
      throw error;
    }
  };

  const register = async (email: string, password: string) => {
    try {
      const response = await authRegister({ 
        email, 
        password 
      });

      const userData: User = {
        id: response.id,
        username: response.username,
        email: response.email,
        role: response.role as 'admin' | 'user',
        balance: 0,
        is_active: true,
        created_at: response.created_at,
        updated_at: response.updated_at,
        phone_number: response.phone_number,
        avatar_url: response.avatar_url
      };
      
      localStorage.setItem('auth_token', response.access_token);
      localStorage.setItem('user_data', JSON.stringify(userData));
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.access_token}`;
      setIsAuthenticated(true);
      setUser(userData);
      navigate('/dashboard');
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    delete axios.defaults.headers.common['Authorization'];
    setIsAuthenticated(false);
    setUser(null);
    navigate('/login');
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <AuthContext.Provider value={{ 
      isAuthenticated, 
      user, 
      loginWithPi, 
      loginWithEmail,
      register,
      logout,
      loading 
    }}>
      {children}
    </AuthContext.Provider>
  );
} 