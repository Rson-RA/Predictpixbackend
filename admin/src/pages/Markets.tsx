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
import StoreIcon from '@mui/icons-material/Store';
import AddIcon from '@mui/icons-material/Add';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import { Market as MarketType, getMarkets, createMarket, approveMarket, rejectMarket, deleteMarket } from '../api/markets';
import { useAuth } from '../contexts/AuthContext';
import CheckIcon from '@mui/icons-material/Check';
import CloseIcon from '@mui/icons-material/Close';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import DeleteIcon from '@mui/icons-material/Delete';

interface CreateMarketFormData {
  title: string;
  description: string;
  end_time: string;
  resolution_time: string;
  creator_fee_percentage: number;
  platform_fee_percentage: number;
}

const initialFormData: CreateMarketFormData = {
  title: '',
  description: '',
  end_time: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16), // 1 week from now
  resolution_time: new Date(Date.now() + 8 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16), // 1 week + 1 day from now
  creator_fee_percentage: 1.0,
  platform_fee_percentage: 2.0,
};

const Markets = () => {
  const { user } = useAuth();
  const [markets, setMarkets] = useState<MarketType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [openRejectDialog, setOpenRejectDialog] = useState(false);
  const [selectedMarketId, setSelectedMarketId] = useState<number | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [formData, setFormData] = useState<CreateMarketFormData>(initialFormData);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [marketToDelete, setMarketToDelete] = useState<number | null>(null);

  useEffect(() => {
    fetchMarkets();
  }, []);

  const extractErrorMessage = (err: any): string => {
    // Handle validation error object with type, loc, msg, input, url
    if (err.response?.data && typeof err.response.data === 'object') {
      if (Array.isArray(err.response.data)) {
        // Handle array of validation errors
        return err.response.data.map((error: any) => error.msg || error.message).join(', ');
      } else if (err.response.data.msg) {
        // Handle single validation error
        return err.response.data.msg;
      } else if (err.response.data.detail) {
        return err.response.data.detail;
      } else if (err.response.data.message) {
        return err.response.data.message;
      }
    }
    
    // Fallback to error message or default
    return err.message || 'An unexpected error occurred';
  };

  const fetchMarkets = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('Fetching markets...');
      const data = await getMarkets();
      console.log('Markets fetched successfully:', data);
      setMarkets(data);
    } catch (err: any) {
      console.error('Detailed error fetching markets:', err);
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof CreateMarketFormData) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    let value: string | number = event.target.value;
    
    if (field.includes('percentage')) {
      const numValue = parseFloat(value);
      // Validate percentage range
      if (numValue < 0) value = 0;
      if (numValue > 5) value = 5;
      value = Number(numValue.toFixed(1)); // Limit to one decimal place
    }
    
    setFormData({ ...formData, [field]: value });
  };

  const convertToUTC = (dateStr: string): Date => {
    const localDate = new Date(dateStr);
    return new Date(
      Date.UTC(
        localDate.getFullYear(),
        localDate.getMonth(),
        localDate.getDate(),
        localDate.getHours(),
        localDate.getMinutes()
      )
    );
  };

  const validateForm = (): string | null => {
    if (!formData.title.trim()) {
      return 'Title is required.';
    }
    if (!formData.description.trim()) {
      return 'Description is required.';
    }
    if (!formData.end_time) {
      return 'End time is required.';
    }
    if (!formData.resolution_time) {
      return 'Resolution time is required.';
    }
    
    // Convert dates to UTC for comparison
    const endTime = convertToUTC(formData.end_time);
    const resolutionTime = convertToUTC(formData.resolution_time);
    const now = new Date();
    const utcNow = new Date(
      Date.UTC(
        now.getUTCFullYear(),
        now.getUTCMonth(),
        now.getUTCDate(),
        now.getUTCHours(),
        now.getUTCMinutes()
      )
    );

    if (endTime <= utcNow) {
      return 'End time must be in the future.';
    }
    if (resolutionTime <= endTime) {
      return 'Resolution time must be after end time.';
    }
    if (formData.creator_fee_percentage < 0 || formData.creator_fee_percentage > 5) {
      return 'Creator fee must be between 0% and 5%.';
    }
    if (formData.platform_fee_percentage < 0 || formData.platform_fee_percentage > 5) {
      return 'Platform fee must be between 0% and 5%.';
    }

    return null;
  };

  const handleCreateMarket = async () => {
    try {
      setError(null);
      
      // Validate form
      const validationError = validateForm();
      if (validationError) {
        setError(validationError);
        return;
      }

      // Convert local datetime-local string to UTC ISO string with timezone
      const endTime = new Date(formData.end_time);
      const resolutionTime = new Date(formData.resolution_time);

      // Ensure dates are in UTC and properly formatted for the backend
      const marketData = {
        title: formData.title.trim(),
        description: formData.description.trim(),
        end_time: new Date(
          Date.UTC(
            endTime.getFullYear(),
            endTime.getMonth(),
            endTime.getDate(),
            endTime.getHours(),
            endTime.getMinutes(),
            0  // seconds
          )
        ).toISOString(),
        resolution_time: new Date(
          Date.UTC(
            resolutionTime.getFullYear(),
            resolutionTime.getMonth(),
            resolutionTime.getDate(),
            resolutionTime.getHours(),
            resolutionTime.getMinutes(),
            0  // seconds
          )
        ).toISOString(),
        creator_fee_percentage: Number(formData.creator_fee_percentage.toFixed(1)),
        platform_fee_percentage: Number(formData.platform_fee_percentage.toFixed(1))
      };

      console.log('Sending market data:', marketData);
      await createMarket(marketData);
      setOpenDialog(false);
      setFormData(initialFormData);
      fetchMarkets();
    } catch (err: any) {
      console.error('Error creating market:', err);
      // Extract validation error message
      if (err.response?.status === 422) {
        const validationErrors = err.response.data?.detail || [];
        if (Array.isArray(validationErrors)) {
          setError(validationErrors.map(error => error.msg).join(', '));
        } else {
          setError(validationErrors.msg || 'Validation error occurred');
        }
      } else {
        setError(extractErrorMessage(err));
      }
    }
  };

  const getStatusChipColor = (status: MarketType['status']): 'success' | 'error' | 'warning' | 'default' => {
    switch (status) {
      case 'active':
        return 'success';
      case 'cancelled':
        return 'error';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatUTCDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return new Date(
      Date.UTC(
        date.getUTCFullYear(),
        date.getUTCMonth(),
        date.getUTCDate(),
        date.getUTCHours(),
        date.getUTCMinutes()
      )
    ).toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZoneName: 'short'
    });
  };

  const handleApproveMarket = async (marketId: number) => {
    try {
      setError(null);
      await approveMarket(marketId);
      fetchMarkets(); // Refresh the markets list
    } catch (err: any) {
      console.error('Error approving market:', err);
      setError(extractErrorMessage(err));
    }
  };

  const handleRejectClick = (marketId: number) => {
    setSelectedMarketId(marketId);
    setOpenRejectDialog(true);
  };

  const handleRejectMarket = async () => {
    if (!selectedMarketId || !rejectReason.trim()) return;

    try {
      setError(null);
      await rejectMarket(selectedMarketId, rejectReason);
      setOpenRejectDialog(false);
      setRejectReason('');
      setSelectedMarketId(null);
      fetchMarkets(); // Refresh the markets list
    } catch (err: any) {
      console.error('Error rejecting market:', err);
      setError(extractErrorMessage(err));
    }
  };

  const handleDeleteClick = (marketId: number) => {
    setMarketToDelete(marketId);
    setIsDeleteDialogOpen(true);
  };

  const handleDeleteMarket = async () => {
    if (!marketToDelete) return;

    try {
      setError(null);
      await deleteMarket(marketToDelete);
      setIsDeleteDialogOpen(false);
      setMarketToDelete(null);
      fetchMarkets(); // Refresh the markets list
    } catch (err: any) {
      console.error('Error deleting market:', err);
      setError(extractErrorMessage(err));
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <StoreIcon sx={{ fontSize: 30, color: 'primary.main' }} />
          <Typography variant="h4" component="h1">
            Markets
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpenDialog(true)}
        >
          Create Market
        </Button>
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
              <TableCell>Title</TableCell>
              <TableCell>Creator</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>End Time</TableCell>
              <TableCell>Total Pool</TableCell>
              {user?.role === 'admin' && <TableCell align="right">Actions</TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {markets.map((market) => (
              <TableRow key={market.id}>
                <TableCell>{market.title}</TableCell>
                <TableCell>{market.creator.username}</TableCell>
                <TableCell>
                  <Chip
                    label={market.status}
                    color={getStatusChipColor(market.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>{formatUTCDate(market.end_time)}</TableCell>
                <TableCell>{market.total_pool}</TableCell>
                {user?.role === 'admin' && (
                  <TableCell align="right">
                    {market.status === 'pending' && (
                      <>
                        <Tooltip title="Approve Market">
                          <IconButton
                            color="success"
                            onClick={() => handleApproveMarket(market.id)}
                          >
                            <CheckIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Reject Market">
                          <IconButton
                            color="error"
                            onClick={() => handleRejectClick(market.id)}
                          >
                            <CloseIcon />
                          </IconButton>
                        </Tooltip>
                      </>
                    )}
                    <Tooltip title="Delete Market">
                      <IconButton
                        color="error"
                        onClick={() => handleDeleteClick(market.id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Market</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              label="Title"
              value={formData.title}
              onChange={handleInputChange('title')}
              fullWidth
              required
              error={!formData.title.trim()}
              helperText={!formData.title.trim() ? 'Title is required' : ''}
            />
            <TextField
              label="Description"
              value={formData.description}
              onChange={handleInputChange('description')}
              fullWidth
              multiline
              rows={4}
              required
              error={!formData.description.trim()}
              helperText={!formData.description.trim() ? 'Description is required' : ''}
            />
            <TextField
              label="End Time"
              type="datetime-local"
              value={formData.end_time}
              onChange={handleInputChange('end_time')}
              fullWidth
              required
              InputLabelProps={{ shrink: true }}
              error={new Date(formData.end_time) <= new Date()}
              helperText={new Date(formData.end_time) <= new Date() ? 'End time must be in the future' : ''}
            />
            <TextField
              label="Resolution Time"
              type="datetime-local"
              value={formData.resolution_time}
              onChange={handleInputChange('resolution_time')}
              fullWidth
              required
              InputLabelProps={{ shrink: true }}
              error={new Date(formData.resolution_time) <= new Date(formData.end_time)}
              helperText={new Date(formData.resolution_time) <= new Date(formData.end_time) ? 'Resolution time must be after end time' : ''}
            />
            <TextField
              label="Creator Fee Percentage"
              type="number"
              value={formData.creator_fee_percentage}
              onChange={handleInputChange('creator_fee_percentage')}
              inputProps={{ min: 0, max: 5, step: 0.1 }}
              fullWidth
              required
              error={formData.creator_fee_percentage < 0 || formData.creator_fee_percentage > 5}
              helperText={formData.creator_fee_percentage < 0 || formData.creator_fee_percentage > 5 ? 'Fee must be between 0% and 5%' : ''}
            />
            <TextField
              label="Platform Fee Percentage"
              type="number"
              value={formData.platform_fee_percentage}
              onChange={handleInputChange('platform_fee_percentage')}
              inputProps={{ min: 0, max: 5, step: 0.1 }}
              fullWidth
              required
              error={formData.platform_fee_percentage < 0 || formData.platform_fee_percentage > 5}
              helperText={formData.platform_fee_percentage < 0 || formData.platform_fee_percentage > 5 ? 'Fee must be between 0% and 5%' : ''}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateMarket} 
            variant="contained" 
            color="primary"
            disabled={validateForm() !== null}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openRejectDialog} onClose={() => setOpenRejectDialog(false)}>
        <DialogTitle>Reject Market</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Reason for rejection"
            type="text"
            fullWidth
            multiline
            rows={3}
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenRejectDialog(false)}>Cancel</Button>
          <Button onClick={handleRejectMarket} color="error" variant="contained">
            Reject
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={isDeleteDialogOpen} onClose={() => setIsDeleteDialogOpen(false)}>
        <DialogTitle>Delete Market</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this market? This action cannot be undone and will delete all related predictions and rewards.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteMarket} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Markets; 