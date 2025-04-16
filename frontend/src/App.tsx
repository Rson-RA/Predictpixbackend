/** @jsxImportSource @emotion/react */
import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider } from './contexts/AuthContext';
import theme from './theme';
import MainLayout from './layouts/MainLayout';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Profile from './pages/Profile';
import Dashboard from './pages/Dashboard';
import Markets from './pages/Markets';
import Users from './pages/Users';
import Predictions from './pages/Predictions';
import Transactions from './pages/Transactions';
import Rewards from './pages/Rewards';
import Referrals from './pages/Referrals';
import ProtectedRoute from './components/ProtectedRoute';

export default function App() {
  useEffect(() => {
    // Initialize Pi SDK with sandbox mode
    window.Pi.init({ version: "2.0", sandbox: true });
  }, []); // Run once when component mounts

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/" element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="markets" element={<Markets />} />
              <Route path="users" element={<Users />} />
              <Route path="predictions" element={<Predictions />} />
              <Route path="transactions" element={<Transactions />} />
              <Route path="rewards" element={<Rewards />} />
              <Route path="referrals" element={<Referrals />} />
              <Route path="profile" element={<Profile />} />
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}
