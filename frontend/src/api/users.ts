import api from './config';
import { User } from '../types/auth';

export interface UserUpdateData {
  username?: string;
  email?: string;
  password?: string;
  role?: string;
  is_active?: boolean;
  avatar_url?: string | null;
}

// Get all users
export const getUsers = async (params?: {
  skip?: number;
  limit?: number;
  search?: string;
}): Promise<User[]> => {
  const response = await api.get<User[]>('/users', { params });
  return response.data;
};

// Get a single user
export const getUser = async (id: number): Promise<User> => {
  const response = await api.get<User>(`/users/${id}`);
  return response.data;
};

// Update a user
export const updateUser = async (id: number, data: UserUpdateData): Promise<User> => {
  const response = await api.patch<User>(`/users/${id}`, data);
  return response.data;
};

// Update user avatar with file upload
export const updateUserAvatar = async (id: number, file: File): Promise<User> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post<User>(`/users/${id}/avatar`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
  return response.data;
};

export const deleteUserAvatar = async (id: number): Promise<User> => {
  const response = await api.delete<User>(`/users/${id}/avatar`);
  return response.data;
}; 