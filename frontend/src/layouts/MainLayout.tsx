import React from 'react';
import { Outlet } from 'react-router-dom';
import Box from '@mui/material/Box';
import { styled } from '@mui/material/styles';
import SideMenu from '../components/SideMenu';
import Header from '../components/Header';

const LayoutRoot = styled(Box)({
  display: 'flex',
  minHeight: '100vh',
  overflow: 'hidden',
  width: '100%'
});

const LayoutContent = styled(Box)(({ theme }) => ({
  flexGrow: 1,
  overflow: 'auto',
  minHeight: '100vh',
  paddingTop: `calc(${theme.spacing(8)} + ${theme.spacing(2)})`, // Account for header height
  paddingBottom: theme.spacing(2),
  paddingLeft: theme.spacing(2),
  paddingRight: theme.spacing(2),
  backgroundColor: '#f5f6fa',
}));

const MainLayout: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  return (
    <LayoutRoot>
      <Header />
      <SideMenu />
      <LayoutContent>
        {children || <Outlet />}
      </LayoutContent>
    </LayoutRoot>
  );
};

export default MainLayout; 