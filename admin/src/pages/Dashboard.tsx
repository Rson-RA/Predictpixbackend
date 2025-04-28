import React, { useState, useEffect } from 'react';
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
import { getMarkets, Market } from '../api/markets';

const Dashboard = () => {
  const theme = useTheme();
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('24h');
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(true);

  // Stats state
  const [stats, setStats] = useState({
    totalMarkets: 0,
    activeMarkets: 0,
    totalVolume: 0,
    todayVolume: 0,
    successRate: 0,
  });
  const [topMarkets, setTopMarkets] = useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const data = await getMarkets();
        setMarkets(data);
        // Compute stats
        const totalMarkets = data.length;
        const activeMarkets = data.filter(m => m.status === 'active').length;
        const totalVolume = data.reduce((sum, m) => sum + m.total_pool, 0);
        // For todayVolume, filter by created_at (today)
        const today = new Date();
        const todayVolume = data.filter(m => {
          const created = new Date(m.created_at);
          return created.getFullYear() === today.getFullYear() &&
            created.getMonth() === today.getMonth() &&
            created.getDate() === today.getDate();
        }).reduce((sum, m) => sum + m.total_pool, 0);
        // Success rate: percent of closed/settled/closed+active
        const resolvedMarkets = data.filter(m => m.status === 'closed' || m.status === 'settled').length;
        const successRate = totalMarkets > 0 ? Math.round((resolvedMarkets / totalMarkets) * 100) : 0;
        setStats({ totalMarkets, activeMarkets, totalVolume, todayVolume, successRate });
        // Top markets by volume
        const sorted = [...data].sort((a, b) => b.total_pool - a.total_pool).slice(0, 3);
        setTopMarkets(sorted.map(m => ({
          id: m.id,
          title: m.title,
          volume: m.total_pool,
          yesPool: m.yes_pool,
          noPool: m.no_pool,
          endTime: m.end_time,
          status: m.status,
        })));
      } catch (e) {
        // handle error
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [timeRange]);

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