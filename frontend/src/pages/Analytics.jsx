import { useState, useEffect } from 'react';
import { Grid, Box, Alert, CircularProgress, Paper, Typography } from '@mui/material';
import PageHeader from '../components/common/PageHeader';
import BrandsChart from '../components/charts/BrandsChart';
import ProductsChart from '../components/charts/ProductsChart';
import ZoneChart from '../components/charts/ZoneChart';
import { dashboardService } from '../api/services';

function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const result = await dashboardService.getDashboard();
        setData(result);
        setError(null);
      } catch (err) {
        setError('Failed to load analytics data. Please try again.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
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

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box>
      <PageHeader
        title="Analytics"
        subtitle="Detailed retail performance insights"
      />

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase' }}>
              Top Brand
            </Typography>
            <Typography variant="h4" sx={{ mt: 1, color: 'primary.main' }}>
             {data?.top_brand || 'N/A'}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase' }}>
              Top Product
            </Typography>
            <Typography variant="h5" sx={{ mt: 1, color: 'secondary.main' }}>
              {data?.top_product || 'N/A'}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        <Grid item xs={12} lg={6}>
          <BrandsChart data={data?.top_brands} />
        </Grid>
        <Grid item xs={12} lg={6}>
          <ProductsChart data={data?.top_products} />
        </Grid>
        <Grid item xs={12}>
          <ZoneChart data={data?.zones} />
        </Grid>
      </Grid>
    </Box>
  );
}

export default Analytics;
