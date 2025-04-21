import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { styled } from '@mui/material/styles';

interface StatCardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  change?: {
    value: number;
    text: string;
  };
  backgroundColor?: string;
  textColor?: string;
}

const CardWrapper = styled(Box)<{ bgcolor?: string }>(({ theme, bgcolor }) => ({
  padding: theme.spacing(3),
  borderRadius: theme.spacing(1),
  backgroundColor: bgcolor || theme.palette.primary.main,
  color: 'white',
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(1),
}));

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon,
  change,
  backgroundColor,
  textColor = 'white',
}) => {
  return (
    <CardWrapper bgcolor={backgroundColor}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="subtitle2" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
          {title}
        </Typography>
        {icon && (
          <Box sx={{ color: textColor }}>
            {icon}
          </Box>
        )}
      </Box>
      <Typography variant="h4" component="div" sx={{ color: textColor }}>
        {value}
      </Typography>
      {change && (
        <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
          {change.value >= 0 ? '+' : ''}{change.value}% {change.text}
        </Typography>
      )}
    </CardWrapper>
  );
};

export default StatCard; 