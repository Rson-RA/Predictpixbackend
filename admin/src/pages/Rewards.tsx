import React, { useEffect, useState } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import FormControl from '@mui/material/FormControl';
import TextField from '@mui/material/TextField';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import { getRewards, Reward, RewardFilters } from '../api/rewards';
import { useAuth } from '../contexts/AuthContext';

const Rewards: React.FC = () => {
  const [rewards, setRewards] = useState<Reward[]>([]);
  const [filters, setFilters] = useState<RewardFilters>({});
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  const fetchRewards = async () => {
    try {
      setLoading(true);
      const data = await getRewards(filters);
      setRewards(data);
    } catch (error) {
      console.error('Error fetching rewards:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRewards();
  }, [filters]);

  const handleFilterChange = (field: keyof RewardFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [field]: value || undefined
    }));
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Rewards
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth>
                <TextField
                  label="User ID"
                  type="number"
                  value={filters.user_id || ''}
                  onChange={(e) => handleFilterChange('user_id', e.target.value ? Number(e.target.value) : undefined)}
                />
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth>
                <TextField
                  label="Market ID"
                  type="number"
                  value={filters.market_id || ''}
                  onChange={(e) => handleFilterChange('market_id', e.target.value ? Number(e.target.value) : undefined)}
                />
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth>
                <TextField
                  label="Prediction ID"
                  type="number"
                  value={filters.prediction_id || ''}
                  onChange={(e) => handleFilterChange('prediction_id', e.target.value ? Number(e.target.value) : undefined)}
                />
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <TextField
                  label="Start Date"
                  type="date"
                  value={filters.start_date || ''}
                  onChange={(e) => handleFilterChange('start_date', e.target.value)}
                  InputLabelProps={{
                    shrink: true,
                  }}
                />
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <TextField
                  label="End Date"
                  type="date"
                  value={filters.end_date || ''}
                  onChange={(e) => handleFilterChange('end_date', e.target.value)}
                  InputLabelProps={{
                    shrink: true,
                  }}
                />
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>User</TableCell>
              <TableCell>Market</TableCell>
              <TableCell>Prediction</TableCell>
              <TableCell>Amount</TableCell>
              <TableCell>Created At</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} align="center">Loading...</TableCell>
              </TableRow>
            ) : rewards.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">No rewards found</TableCell>
              </TableRow>
            ) : (
              rewards.map((reward) => (
                <TableRow key={reward.id}>
                  <TableCell>{reward.id}</TableCell>
                  <TableCell>{reward.user.username}</TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap>
                      {reward.market.title}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      ID: {reward.prediction.id}
                      <br />
                      Outcome: {reward.prediction.predicted_outcome}
                    </Typography>
                  </TableCell>
                  <TableCell>{formatAmount(reward.amount)}</TableCell>
                  <TableCell>
                    {new Date(reward.created_at).toLocaleString()}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default Rewards; 