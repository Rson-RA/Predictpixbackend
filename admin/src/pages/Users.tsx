import React, { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import EditIcon from '@mui/icons-material/Edit';
import PersonIcon from '@mui/icons-material/Person';
import Avatar from '@mui/material/Avatar';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import EditUserDialog from '../components/EditUserDialog';
import { User } from '../types/auth';
import * as usersApi from '../api/users';
import { getFullAvatarUrl } from '../utils/avatar';

const Users = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await usersApi.getUsers();
      setUsers(data);
    } catch (err) {
      setError('Failed to load users. Please try again later.');
      console.error('Error fetching users:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleEditClick = (user: User) => {
    setSelectedUser(user);
    setIsEditDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setSelectedUser(null);
    setIsEditDialogOpen(false);
  };

  const handleSaveUser = async (userData: Partial<User>) => {
    if (!selectedUser) return;

    try {
      setError(null);
      const updateData: usersApi.UserUpdateData = {
        username: userData.username,
        email: userData.email || undefined,
        role: userData.role,
        is_active: userData.is_active,
        firstname: userData.firstname || undefined,
        lastname: userData.lastname || undefined
      };

      // Update user data
      const updatedUser = await usersApi.updateUser(selectedUser.id, updateData);
      
      // Refresh the users list to get the latest data including avatar changes
      await fetchUsers();
      
      handleCloseDialog();
    } catch (err) {
      setError('Failed to update user. Please try again.');
      console.error('Error updating user:', err);
    }
  };

  const getStatusChipColor = (isActive: boolean) => {
    return isActive ? 'success' : 'error';
  };

  const getRoleChipColor = (role: User['role']) => {
    return role === 'admin' ? 'primary' : 'default';
  };

  const getInitials = (username: string) => {
    return username.slice(0, 2).toUpperCase();
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
        <PersonIcon sx={{ fontSize: 30, color: 'primary.main' }} />
        <Typography variant="h4" component="h1">
          Users
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Avatar</TableCell>
              <TableCell>Username</TableCell>
              <TableCell>First Name</TableCell>
              <TableCell>Last Name</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Balance</TableCell>
              <TableCell>Created At</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell>
                  <Avatar
                    src={user.avatar_url ? getFullAvatarUrl(user.avatar_url) : undefined}
                    sx={{ width: 40, height: 40 }}
                  >
                    {getInitials(user.username)}
                  </Avatar>
                </TableCell>
                <TableCell>{user.username}</TableCell>
                <TableCell>{user.firstname || '-'}</TableCell>
                <TableCell>{user.lastname || '-'}</TableCell>
                <TableCell>{user.email}</TableCell>
                <TableCell>
                  <Chip
                    label={user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                    color={getRoleChipColor(user.role)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={user.is_active ? 'Active' : 'Inactive'}
                    color={getStatusChipColor(user.is_active)}
                    size="small"
                  />
                </TableCell>
                <TableCell>{user.balance}</TableCell>
                <TableCell>{new Date(user.created_at).toLocaleDateString()}</TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => handleEditClick(user)}
                    color="primary"
                  >
                    <EditIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <EditUserDialog
        open={isEditDialogOpen}
        onClose={handleCloseDialog}
        onSave={handleSaveUser}
        user={selectedUser}
      />
    </Box>
  );
};

export default Users; 