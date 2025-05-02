import React, { useEffect, useState, FC } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Chip from '@mui/material/Chip';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import { 
  getPredictions, 
  createPrediction, 
  deletePrediction, 
  updatePredictionStatus as updatePredictionStatusApi,
  PredictionFilters,
  PredictionCreate,
  Prediction
 } from '../api/predictions';
import { useAuth } from '../contexts/AuthContext';
import { useSnackbar } from 'notistack';

const Predictions = () => {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [filters, setFilters] = useState<PredictionFilters>({});
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [newPrediction, setNewPrediction] = useState<PredictionCreate>({
    user_id: 0,
    market_id: 0,
    amount: 0,
    predicted_outcome: '',
  });
  const { user } = useAuth();
  const { enqueueSnackbar } = useSnackbar();

  const fetchPredictions = async () => {
    try {
      setLoading(true);
      const data = await getPredictions(filters);
      setPredictions(data);
    } catch (error) {
      enqueueSnackbar('Error fetching predictions', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPredictions();
  }, [filters]);

  const handleFilterChange = (field: keyof PredictionFilters, value: string | number | undefined) => {
    setFilters(prev => ({
      ...prev,
      [field]: value || undefined
    }));
  };

  const handleCreatePrediction = async () => {
    try {
      await createPrediction(newPrediction);
      setOpenDialog(false);
      await fetchPredictions();
      // Reset form
      setNewPrediction({
        user_id: 0,
        market_id: 0,
        amount: 0,
        predicted_outcome: '',
      });
      enqueueSnackbar('Prediction created successfully', { variant: 'success' });
    } catch (error) {
      enqueueSnackbar('Error creating prediction', { variant: 'error' });
    }
  };

  const handleDeletePrediction = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this prediction?')) {
      try {
        await deletePrediction(id);
        await fetchPredictions();
        enqueueSnackbar('Prediction deleted successfully', { variant: 'success' });
      } catch (error) {
        enqueueSnackbar('Error deleting prediction', { variant: 'error' });
      }
    }
  };

  const getStatusColor = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'pending':
        return '#ffa726';
      case 'won':
        return '#66bb6a';
      case 'lost':
        return '#ef5350';
      default:
        return '#90a4ae';
    }
  };

  // Function to update prediction status
  const updatePredictionStatus = async (predictionId: number, status: string) => {
    try {
      const updatedPrediction = await updatePredictionStatusApi(predictionId, status);
      // Refresh predictions list after successful update
      await fetchPredictions();
      return updatedPrediction;
    } catch (error) {
      enqueueSnackbar('Error updating prediction status', { variant: 'error' });
      throw error;
    }
  };

  // Handle status change in the UI
  const handleStatusChange = async (predictionId: number, newStatus: string) => {
    try {
      await updatePredictionStatus(predictionId, newStatus);
      enqueueSnackbar('Prediction status updated successfully', { variant: 'success' });
    } catch (error) {
      enqueueSnackbar('Failed to update prediction status', { variant: 'error' });
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Card>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={3}>
              <Typography variant="h5" component="h2">
                Predictions
              </Typography>
            </Grid>
            <Grid item xs={12} md={7}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <FormControl fullWidth>
                    <InputLabel>Status</InputLabel>
                    <Select
                      value={filters.status || ''}
                      onChange={(e) => handleFilterChange('status', e.target.value)}
                    >
                      <MenuItem value="">All</MenuItem>
                      <MenuItem value="pending">Pending</MenuItem>
                      <MenuItem value="won">Won</MenuItem>
                      <MenuItem value="lost">Lost</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="User ID"
                    type="number"
                    value={filters.user_id || ''}
                    onChange={(e) => handleFilterChange('user_id', parseInt(e.target.value) || undefined)}
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Market ID"
                    type="number"
                    value={filters.market_id || ''}
                    onChange={(e) => handleFilterChange('market_id', parseInt(e.target.value) || undefined)}
                  />
                </Grid>
              </Grid>
            </Grid>
            <Grid item xs={12} md={2}>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setOpenDialog(true)}
                fullWidth
              >
                New Prediction
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {loading ? (
        <Typography sx={{ mt: 2 }}>Loading...</Typography>
      ) : predictions.length === 0 ? (
        <Typography sx={{ mt: 2 }}>No predictions found</Typography>
      ) : (
        <TableContainer component={Paper} sx={{ mt: 2 }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>User ID</TableCell>
                <TableCell>Market ID</TableCell>
                <TableCell>Amount</TableCell>
                <TableCell>Predicted Outcome</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {predictions.map((prediction) => (
                <TableRow key={prediction.id}>
                  <TableCell>{prediction.id}</TableCell>
                  <TableCell>{prediction.creator.username}</TableCell>
                  <TableCell>{prediction.market_id}</TableCell>
                  <TableCell>{prediction.amount}</TableCell>
                  <TableCell>{prediction.predicted_outcome}</TableCell>
                  <TableCell>
                    <FormControl>
                      <Select
                        value={prediction.status}
                        onChange={(e) => handleStatusChange(prediction.id, e.target.value)}
                        size="small"
                        sx={{
                          backgroundColor: getStatusColor(prediction.status),
                          color: '#fff',
                          '& .MuiSelect-icon': { color: '#fff' }
                        }}
                      >
                        <MenuItem value="active">Active</MenuItem>
                        <MenuItem value="pending">Pending</MenuItem>
                        <MenuItem value="won">Won</MenuItem>
                        <MenuItem value="lost">Lost</MenuItem>
                      </Select>
                    </FormControl>
                  </TableCell>
                  <TableCell>
                    <IconButton
                      onClick={() => handleDeletePrediction(prediction.id)}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>Create New Prediction</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="User ID"
                type="number"
                value={newPrediction.user_id}
                onChange={(e) => setNewPrediction(prev => ({ ...prev, user_id: parseInt(e.target.value) || 0 }))}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Market ID"
                type="number"
                value={newPrediction.market_id}
                onChange={(e) => setNewPrediction(prev => ({ ...prev, market_id: parseInt(e.target.value) || 0 }))}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Amount"
                type="number"
                value={newPrediction.amount}
                onChange={(e) => setNewPrediction(prev => ({ ...prev, amount: parseFloat(e.target.value) || 0 }))}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Predicted Outcome"
                value={newPrediction.predicted_outcome}
                onChange={(e) => setNewPrediction(prev => ({ ...prev, predicted_outcome: e.target.value }))}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleCreatePrediction} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Predictions;