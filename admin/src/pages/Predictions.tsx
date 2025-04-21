import React, { useEffect, useState } from 'react';
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
import { getPredictions, Prediction, PredictionFilters, createPrediction, deletePrediction, PredictionCreate } from '../api/predictions';
import { useAuth } from '../contexts/AuthContext';

const Predictions: React.FC = () => {
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

  const fetchPredictions = async () => {
    try {
      setLoading(true);
      const data = await getPredictions(filters);
      setPredictions(data);
    } catch (error) {
      console.error('Error fetching predictions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPredictions();
  }, [filters]);

  const handleFilterChange = (field: keyof PredictionFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [field]: value || undefined
    }));
  };

  const handleCreatePrediction = async () => {
    try {
      await createPrediction(newPrediction);
      setOpenDialog(false);
      fetchPredictions();
      // Reset form
      setNewPrediction({
        user_id: 0,
        market_id: 0,
        amount: 0,
        predicted_outcome: '',
      });
    } catch (error) {
      console.error('Error creating prediction:', error);
    }
  };

  const handleDeletePrediction = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this prediction?')) {
      try {
        await deletePrediction(id);
        fetchPredictions();
      } catch (error) {
        console.error('Error deleting prediction:', error);
      }
    }
  };

  const getStatusColor = (status: string) => {
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

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Predictions
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => setOpenDialog(true)}
        >
          Add Prediction
        </Button>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel id="status-label">Status</InputLabel>
                <Select
                  labelId="status-label"
                  value={filters.status || ''}
                  label="Status"
                  onChange={(e: SelectChangeEvent) => handleFilterChange('status', e.target.value)}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="won">Won</MenuItem>
                  <MenuItem value="lost">Lost</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <TextField
                  label="Market ID"
                  type="number"
                  value={filters.market_id || ''}
                  onChange={(e) => handleFilterChange('market_id', e.target.value ? Number(e.target.value) : undefined)}
                />
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <TextField
                  label="User ID"
                  type="number"
                  value={filters.user_id || ''}
                  onChange={(e) => handleFilterChange('user_id', e.target.value ? Number(e.target.value) : undefined)}
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
              <TableCell>Market</TableCell>
              <TableCell>Amount</TableCell>
              <TableCell>Predicted Outcome</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created At</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} align="center">Loading...</TableCell>
              </TableRow>
            ) : predictions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">No predictions found</TableCell>
              </TableRow>
            ) : (
              predictions.map((prediction) => (
                <TableRow key={prediction.id}>
                  <TableCell>{prediction.id}</TableCell>
                  <TableCell>{prediction.market.title}</TableCell>
                  <TableCell>{prediction.amount}</TableCell>
                  <TableCell>{prediction.predicted_outcome}</TableCell>
                  <TableCell>
                    <Chip
                      label={prediction.status}
                      sx={{
                        backgroundColor: getStatusColor(prediction.status),
                        color: 'white',
                      }}
                    />
                  </TableCell>
                  <TableCell>
                    {new Date(prediction.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <IconButton
                      color="error"
                      onClick={() => handleDeletePrediction(prediction.id)}
                      size="small"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Prediction</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="User ID"
                type="number"
                value={newPrediction.user_id}
                onChange={(e) => setNewPrediction(prev => ({ ...prev, user_id: Number(e.target.value) }))}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Market ID"
                type="number"
                value={newPrediction.market_id}
                onChange={(e) => setNewPrediction(prev => ({ ...prev, market_id: Number(e.target.value) }))}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Amount"
                type="number"
                value={newPrediction.amount}
                onChange={(e) => setNewPrediction(prev => ({ ...prev, amount: Number(e.target.value) }))}
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
          <Button onClick={handleCreatePrediction} variant="contained" color="primary">
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Predictions;