import React, { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import IconButton from '@mui/material/IconButton';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import ShareIcon from '@mui/icons-material/Share';
import MonetizationOnIcon from '@mui/icons-material/MonetizationOn';
import PeopleIcon from '@mui/icons-material/People';
import { useAuth } from '../contexts/AuthContext';
import * as referralApi from '../api/referral';

interface ReferralData {
  referral_code: string;
  referral_url: string;
  referral_earnings: number;
  total_referrals: number;
  referred_by: any | null;
}

interface ReferralTransaction {
  id: number;
  amount: number;
  created_at: string;
  referred_user: {
    username: string;
    email: string;
  };
}

const Referrals: React.FC = () => {
  const [referralData, setReferralData] = useState<ReferralData | null>(null);
  const [transactions, setTransactions] = useState<ReferralTransaction[]>([]);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const { user } = useAuth();

  useEffect(() => {
    fetchReferralData();
    fetchTransactions();
  }, []);

  const fetchReferralData = async () => {
    try {
      const data = await referralApi.getMyReferral();
      setReferralData(data);
    } catch (error) {
      console.error('Error fetching referral data:', error);
    }
  };

  const fetchTransactions = async () => {
    try {
      const data = await referralApi.getReferralTransactions();
      setTransactions(data);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    }
  };

  const copyToClipboard = (text: string, message: string) => {
    navigator.clipboard.writeText(text);
    setSnackbarMessage(message);
    setSnackbarOpen(true);
  };

  const handleShare = async () => {
    if (!referralData) return;

    try {
      await navigator.share({
        title: 'Join me on PredictPix!',
        text: 'Use my referral code to sign up and earn rewards!',
        url: referralData.referral_url
      });
    } catch (error) {
      console.error('Error sharing:', error);
    }
  };

  if (!referralData) {
    return <Box>Loading...</Box>;
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Referral Program
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <MonetizationOnIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Total Pi Rewards</Typography>
              </Box>
              <Typography variant="h4">
                ${referralData.referral_earnings?.toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PeopleIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Total Referrals</Typography>
              </Box>
              <Typography variant="h4">{referralData.total_referrals}</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Your Referral Code
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              <Typography variant="h5" component="code" sx={{ fontFamily: 'monospace' }}>
                {referralData.referral_code}
              </Typography>
              <IconButton
                onClick={() => copyToClipboard(
                  referralData.referral_code,
                  'Referral code copied to clipboard!'
                )}
              >
                <ContentCopyIcon />
              </IconButton>
            </Box>

            <Typography variant="h6" gutterBottom>
              Referral Link
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography
                variant="body1"
                sx={{
                  fontFamily: 'monospace',
                  bgcolor: 'grey.100',
                  p: 1,
                  borderRadius: 1,
                  flex: 1,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}
              >
                {referralData.referral_url}
              </Typography>
              <IconButton
                onClick={() => copyToClipboard(
                  referralData.referral_url,
                  'Referral link copied to clipboard!'
                )}
              >
                <ContentCopyIcon />
              </IconButton>
              <IconButton onClick={handleShare}>
                <ShareIcon />
              </IconButton>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>
            Recent Referrals
          </Typography>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>Referred User</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell align="right">Amount</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {transactions.map((tx) => (
                  <TableRow key={tx.id}>
                    <TableCell>
                      {new Date(tx.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>{tx.referred_user.username}</TableCell>
                    <TableCell>{tx.referred_user.email}</TableCell>
                    <TableCell align="right">${tx.amount?.toFixed(2)}</TableCell>
                  </TableRow>
                ))}
                {transactions.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} align="center">
                      No referrals yet
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>
      </Grid>

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
      >
        <Alert severity="success" onClose={() => setSnackbarOpen(false)}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Referrals; 