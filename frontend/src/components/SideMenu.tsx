import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import DashboardIcon from '@mui/icons-material/Dashboard';
import BarChartIcon from '@mui/icons-material/BarChart';
import WidgetsIcon from '@mui/icons-material/Widgets';
import ViewQuiltIcon from '@mui/icons-material/ViewQuilt';
import InfoIcon from '@mui/icons-material/Info';
import StoreIcon from '@mui/icons-material/Store';
import PersonIcon from '@mui/icons-material/Person';
import ShareIcon from '@mui/icons-material/Share';
import { styled } from '@mui/material/styles';

const SideMenuWrapper = styled(Box)(({ theme }) => ({
  width: 240,
  backgroundColor: '#1a2236',
  height: '100vh',
  color: 'white',
  padding: theme.spacing(2, 0),
}));

const MenuLink = styled(Link)(({ theme }) => ({
  textDecoration: 'none',
  color: 'white',
  width: '100%',
  '&:hover': {
    color: theme.palette.primary.main,
  },
}));

const MenuItem = styled(ListItem)<{ active?: boolean }>(({ theme, active }) => ({
  padding: theme.spacing(1.5, 2),
  margin: theme.spacing(0.5, 2),
  borderRadius: theme.spacing(1),
  backgroundColor: active ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
  '&:hover': {
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
  },
}));

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  { text: 'Users', icon: <PersonIcon />, path: '/users' },
  { text: 'Markets', icon: <StoreIcon />, path: '/markets' },
  { text: 'Predictions', icon: <WidgetsIcon />, path: '/predictions' },
  { text: 'Transactions', icon: <ViewQuiltIcon />, path: '/transactions' },
  { text: 'Rewards', icon: <ViewQuiltIcon />, path: '/rewards' },
  { text: 'Referrals', icon: <ShareIcon />, path: '/referrals' },
  // { text: 'About', icon: <InfoIcon />, path: '/about' },
];

const SideMenu = () => {
  const location = useLocation();

  return (
    <SideMenuWrapper>
      <Box sx={{ p: 2, mb: 2 }}>
        <img src="/logo.png" alt="Spur Logo" style={{ width: 100 }} />
      </Box>
      <List>
        {menuItems.map((item) => (
          <MenuLink to={item.path} key={item.text}>
            <MenuItem active={location.pathname === item.path}>
              <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </MenuItem>
          </MenuLink>
        ))}
      </List>
    </SideMenuWrapper>
  );
};

export default SideMenu; 