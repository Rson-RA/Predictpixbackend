import React, { useState, useEffect } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Box from '@mui/material/Box';
import Avatar from '@mui/material/Avatar';
import IconButton from '@mui/material/IconButton';
import PhotoCamera from '@mui/icons-material/PhotoCamera';
import { styled } from '@mui/material/styles';
import { User } from '../types/auth';
import { updateUserAvatar } from '../api/users';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

const Input = styled('input')({
  display: 'none',
});

interface EditUserDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (userData: Partial<User>) => void;
  user: User | null;
}

const EditUserDialog: React.FC<EditUserDialogProps> = ({ open, onClose, onSave, user }) => {
  const [formData, setFormData] = useState<Partial<User>>({
    username: '',
    email: '',
    role: 'user',
    is_active: true,
    avatar_url: null,
    firstname: '',
    lastname: ''
  });
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const getFullAvatarUrl = (avatarUrl: string | null): string | null => {
    if (!avatarUrl) return null;
    if (avatarUrl.startsWith('http')) return avatarUrl;
    return `${BACKEND_URL}${avatarUrl}`;
  };

  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username,
        email: user.email || '',
        role: user.role,
        is_active: user.is_active,
        avatar_url: user.avatar_url || null,
        firstname: user.firstname || '',
        lastname: user.lastname || ''
      });
      setAvatarPreview(getFullAvatarUrl(user.avatar_url || null));
      setAvatarFile(null);
    }
  }, [user]);

  const handleTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSelectChange = (e: SelectChangeEvent) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'is_active' ? value === 'true' : value
    }));
  };

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setAvatarFile(file);
      
      // Create preview URL
      const previewUrl = URL.createObjectURL(file);
      setAvatarPreview(previewUrl);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;
    
    setIsSubmitting(true);
    try {
      // First update user data
      await onSave(formData);
      
      // Then upload avatar if a new file was selected
      if (avatarFile && user) {
        const updatedUser = await updateUserAvatar(user.id, avatarFile);
        
        // Update the avatar preview with the new URL from the response
        if (updatedUser.avatar_url) {
          setAvatarPreview(getFullAvatarUrl(updatedUser.avatar_url));
          
          // Call onSave again to trigger a refresh in the parent component
          await onSave({
            ...formData,
            avatar_url: updatedUser.avatar_url
          });
        }
      }
      
      onClose();
    } catch (error) {
      console.error('Error updating user:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getInitials = (username: string) => {
    return username.slice(0, 2).toUpperCase();
  };

  // Cleanup preview URL when component unmounts or dialog closes
  useEffect(() => {
    return () => {
      if (avatarPreview && !avatarPreview.startsWith('http')) {
        URL.revokeObjectURL(avatarPreview);
      }
    };
  }, [avatarPreview]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{user ? 'Edit User' : 'Add User'}</DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar
                src={avatarPreview || undefined}
                sx={{ width: 64, height: 64 }}
              >
                {formData.username ? getInitials(formData.username) : '?'}
              </Avatar>
              <label htmlFor="avatar-input">
                <Input
                  accept="image/*"
                  id="avatar-input"
                  type="file"
                  onChange={handleAvatarChange}
                />
                <IconButton color="primary" component="span">
                  <PhotoCamera />
                </IconButton>
              </label>
            </Box>
            <TextField
              name="username"
              label="Username"
              value={formData.username}
              onChange={handleTextChange}
              fullWidth
              required
            />
            <TextField
              name="firstname"
              label="First Name"
              value={formData.firstname}
              onChange={handleTextChange}
              fullWidth
            />
            <TextField
              name="lastname"
              label="Last Name"
              value={formData.lastname}
              onChange={handleTextChange}
              fullWidth
            />
            <TextField
              name="email"
              label="Email"
              type="email"
              value={formData.email}
              onChange={handleTextChange}
              fullWidth
              required
            />
            <FormControl fullWidth>
              <InputLabel>Role</InputLabel>
              <Select
                name="role"
                value={formData.role || ''}
                label="Role"
                onChange={handleSelectChange}
              >
                <MenuItem value="user">User</MenuItem>
                <MenuItem value="admin">Admin</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                name="is_active"
                value={formData.is_active?.toString() || 'true'}
                label="Status"
                onChange={handleSelectChange}
              >
                <MenuItem value="true">Active</MenuItem>
                <MenuItem value="false">Inactive</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained" color="primary">
            Save
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default EditUserDialog; 