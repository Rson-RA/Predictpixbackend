import React, { useState } from 'react';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import ButtonGroup from '@mui/material/ButtonGroup';
import Button from '@mui/material/Button';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import CheckIcon from '@mui/icons-material/Check';
import { useTheme } from '@mui/material/styles';

const Dashboard = () => {
  const theme = useTheme();
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('24h');

  // Mock data - replace with real API calls
  const stats = {
    totalMarkets: 156,
    activeMarkets: 42,
    totalVolume: 25420,
    todayVolume: 1245,
    successRate: 78,
  };

  const topMarkets = [
    {
      id: 1,
      title: "Will BTC reach $100k by end of 2024?",
      volume: 5240,
      yesPool: 3240,
      noPool: 2000,
      endTime: "2024-12-31",
      status: "active",
    },
    {
      id: 2,
      title: "Will Ethereum 2.0 launch in Q2?",
      volume: 3150,
      yesPool: 2150,
      noPool: 1000,
      endTime: "2024-06-30",
      status: "active",
    },
    {
      id: 3,
      title: "Will Pi Network reach mainnet in 2024?",
      volume: 2840,
      yesPool: 1540,
      noPool: 1300,
      endTime: "2024-12-31",
      status: "active",
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'pending':
        return 'warning';
      case 'closed':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Grid container spacing={3}>
        {/* Market Statistics */}
        <Grid item xs={12}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="h5" gutterBottom>
              Market Analysis
            </Typography>
            <ButtonGroup size="small" sx={{ mb: 3 }}>
              <Button 
                variant={timeRange === '24h' ? 'contained' : 'outlined'}
                onClick={() => setTimeRange('24h')}
              >
                24H
              </Button>
              <Button 
                variant={timeRange === '7d' ? 'contained' : 'outlined'}
                onClick={() => setTimeRange('7d')}
              >
                7D
              </Button>
              <Button 
                variant={timeRange === '30d' ? 'contained' : 'outlined'}
                onClick={() => setTimeRange('30d')}
              >
                30D
              </Button>
            </ButtonGroup>
          </Box>
        </Grid>

        {/* Stats Cards */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Markets
              </Typography>
              <Typography variant="h4">
                {stats.totalMarkets}
              </Typography>
              <Typography variant="body2" color="success.main" sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <TrendingUpIcon fontSize="small" sx={{ mr: 0.5 }} />
                +12% from last month
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Markets
              </Typography>
              <Typography variant="h4">
                {stats.activeMarkets}
              </Typography>
              <Typography variant="body2" color="success.main" sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <ShowChartIcon fontSize="small" sx={{ mr: 0.5 }} />
                Currently Live
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Volume (π)
              </Typography>
              <Typography variant="h4">
                {stats.totalVolume.toLocaleString()}
              </Typography>
              <Typography variant="body2" color="success.main" sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <TrendingUpIcon fontSize="small" sx={{ mr: 0.5 }} />
                +5% from last week
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Success Rate
              </Typography>
              <Typography variant="h4">
                {stats.successRate}%
              </Typography>
              <Typography variant="body2" color="success.main" sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <CheckIcon fontSize="small" sx={{ mr: 0.5 }} />
                Resolved Markets
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Top Markets Table */}
        <Grid item xs={12}>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Market</TableCell>
                  <TableCell align="right">Volume (π)</TableCell>
                  <TableCell align="right">Yes Pool</TableCell>
                  <TableCell align="right">No Pool</TableCell>
                  <TableCell align="right">End Date</TableCell>
                  <TableCell align="right">Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {topMarkets.map((market) => (
                  <TableRow key={market.id}>
                    <TableCell component="th" scope="row">
                      {market.title}
                    </TableCell>
                    <TableCell align="right">{market.volume.toLocaleString()}</TableCell>
                    <TableCell align="right">
                      <Box>
                        <Typography variant="body2">
                          {market.yesPool.toLocaleString()} π
                        </Typography>
                        <LinearProgress 
                          variant="determinate" 
                          value={(market.yesPool / (market.yesPool + market.noPool)) * 100}
                          sx={{ 
                            height: 4,
                            backgroundColor: theme.palette.grey[200],
                            '& .MuiLinearProgress-bar': {
                              backgroundColor: theme.palette.success.main,
                            }
                          }}
                        />
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Box>
                        <Typography variant="body2">
                          {market.noPool.toLocaleString()} π
                        </Typography>
                        <LinearProgress 
                          variant="determinate" 
                          value={(market.noPool / (market.yesPool + market.noPool)) * 100}
                          sx={{ 
                            height: 4,
                            backgroundColor: theme.palette.grey[200],
                            '& .MuiLinearProgress-bar': {
                              backgroundColor: theme.palette.error.main,
                            }
                          }}
                        />
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                        <AccessTimeIcon fontSize="small" sx={{ mr: 0.5, color: 'text.secondary' }} />
                        {new Date(market.endTime).toLocaleDateString()}
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Chip 
                        label={market.status} 
                        color={getStatusColor(market.status) as any}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard; 