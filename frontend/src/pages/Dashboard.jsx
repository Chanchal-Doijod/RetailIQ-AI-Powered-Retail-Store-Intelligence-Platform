import { useState, useEffect } from 'react';
import { Grid, Box, Alert, CircularProgress } from '@mui/material';
import {
  AttachMoney,
  Receipt,
  People,
  TrendingUp,
  AccessTime,
} from '@mui/icons-material';
import PageHeader from '../components/common/PageHeader';
import KPICard from '../components/common/KPICard';
import BrandsChart from '../components/charts/BrandsChart';
import ZoneChart from '../components/charts/ZoneChart';
import ConversionFunnel from '../components/charts/ConversionFunnel';
import { fetchAllDashboardData } from '../api/services';

function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const result = await fetchAllDashboardData();
        setData(result);
        setError(null);
      } catch (err) {
        setError('Failed to load dashboard data. Please try again.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '50vh',
        }}
      >
        <CircularProgress size={48} />
      </Box>
    );
  }

  if (error && !data) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  const { dashboard } = data || {};

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value || 0);
  };

  const formatTime = (seconds) => {
    if (!seconds) return '0s';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  return (
    <Box>
      <PageHeader
        title="Dashboard"
        subtitle="Real-time store performance metrics"
        status="Live"
      />

      {/* KPI Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={4} lg={2.4}>
          <KPICard
            title="Revenue"
            value={formatCurrency(dashboard?.revenue)}
            subtitle="Total sales"
            icon={<AttachMoney />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2.4}>
          <KPICard
            title="Transactions"
            value={dashboard?.transactions?.toLocaleString() || '0'}
            subtitle="Completed orders"
            icon={<Receipt />}
            color="secondary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2.4}>
          <KPICard
            title="Footfall"
            value={dashboard?.footfall?.toLocaleString() || '0'}
            subtitle="Store visitors"
            icon={<People />}
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2.4}>
          <KPICard
            title="Conversion Rate"
            value={`${dashboard?.conversion_rate || 0}%`}
            subtitle="Visitors to buyers"
            icon={<TrendingUp />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2.4}>
          <KPICard
            title="Staff"
            value={dashboard?.staff ?? 0}
            subtitle="Detected staff"
            icon={<AccessTime />}
            color="warning"
          />
        </Grid>
         <Grid item xs={12} sm={6} md={4} lg={2.4}>
          <KPICard
  title="Avg Dwell Time"
  value={formatTime(
    dashboard?.dwell?.avg_dwell_seconds
  )}
  subtitle="Average visitor dwell"
  icon={<AccessTime />}
  color="warning"
/>
        </Grid>
      </Grid>
      

      {/* Charts Row */}
      <Grid container spacing={3}>
        <Grid item xs={12} lg={4}>
          <ConversionFunnel data={dashboard?.funnel} />
        </Grid>
        <Grid item xs={12} lg={4}>
          <BrandsChart data={dashboard?.top_brands} />
        </Grid>
        <Grid item xs={12} lg={4}>
          <ZoneChart data={dashboard?.zones} />
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard;
