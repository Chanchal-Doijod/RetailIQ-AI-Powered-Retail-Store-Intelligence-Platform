import { useState, useEffect } from 'react';
import {
  Grid,
  Box,
  Alert,
  CircularProgress,
  Paper,
  Typography,
  Chip,
  alpha,
} from '@mui/material';
import {
  People,
  Badge,
  Timeline,
  CheckCircle,
  Warning,
  Memory,
  Videocam,
  Storage,
} from '@mui/icons-material';
import PageHeader from '../components/common/PageHeader';
import StatusIndicator from '../components/common/StatusIndicator';
import { diagnosticsService } from '../api/services';

function Diagnostics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const result = await diagnosticsService.getDiagnostics();
        setData(result);
        setError(null);
      } catch (err) {
        setError('Failed to load diagnostics data.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
    const interval = setInterval(loadData, 5000); // Refresh every 5s
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

  // System components status (simulated based on data presence)
  const systemComponents = [
    {
      name: 'YOLOv8 Detection',
      status: data ? 'operational' : 'error',
      description: 'Real-time object detection',
    },
    {
      name: 'ByteTrack',
      status: data ? 'operational' : 'error',
      description: 'Multi-object tracking',
    },
    {
      name: 'ReID Module',
      status: data ? 'operational' : 'warning',
      description: 'Person re-identification',
    },
    {
      name: 'Zone Analytics',
      status: data ? 'operational' : 'error',
      description: 'Area-based analytics',
    },
    {
      name: 'POS Integration',
      status: data?.events_generated > 0 ? 'operational' : 'warning',
      description: 'Transaction data sync',
    },
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'operational':
        return 'success';
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'info';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'operational':
        return <CheckCircle fontSize="small" />;
      case 'warning':
        return <Warning fontSize="small" />;
      default:
        return <Warning fontSize="small" />;
    }
  };

  return (
    <Box>
      <PageHeader
        title="Diagnostics"
        subtitle="System health and monitoring"
      />

      {error && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          {error} Showing last known data.
        </Alert>
      )}

      {/* Detection Metrics */}
      <Typography variant="h5" sx={{ mb: 2 }}>
        Detection Metrics
      </Typography>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={4}>
          <StatusIndicator
            label="Customers Detected"
            value={data?.customer_count?.toLocaleString() || '0'}
            status="success"
            icon={<People />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <StatusIndicator
            label="Staff Detected"
            value={data?.staff_count?.toLocaleString() || '0'}
            status="info"
            icon={<Badge />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <StatusIndicator
            label="Events Generated"
            value={data?.events_generated?.toLocaleString() || '0'}
            status={data?.events_generated > 0 ? 'success' : 'warning'}
            icon={<Timeline />}
          />
        </Grid>
      </Grid>

      {/* System Components */}
      <Typography variant="h5" sx={{ mb: 2 }}>
        System Components
      </Typography>
      <Paper sx={{ mb: 4 }}>
        {systemComponents.map((component, index) => (
          <Box
            key={component.name}
            sx={{
              p: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom:
                index < systemComponents.length - 1 ? '1px solid' : 'none',
              borderColor: 'divider',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box
                sx={{
                  p: 1,
                  borderRadius: 1,
                  backgroundColor: (theme) =>
                    alpha(theme.palette[getStatusColor(component.status)].main, 0.1),
                  color: `${getStatusColor(component.status)}.main`,
                }}
              >
                {component.name.includes('YOLO') ? (
                  <Videocam />
                ) : component.name.includes('Track') ? (
                  <Timeline />
                ) : component.name.includes('ReID') ? (
                  <People />
                ) : component.name.includes('Zone') ? (
                  <Memory />
                ) : (
                  <Storage />
                )}
              </Box>
              <Box>
                <Typography variant="body1" fontWeight={500}>
                  {component.name}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {component.description}
                </Typography>
              </Box>
            </Box>
            <Chip
              size="small"
              icon={getStatusIcon(component.status)}
              label={component.status.charAt(0).toUpperCase() + component.status.slice(1)}
              color={getStatusColor(component.status)}
              sx={{ fontWeight: 500 }}
            />
          </Box>
        ))}
      </Paper>

      {/* System Info */}
      <Typography variant="h5" sx={{ mb: 2 }}>
        System Information
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Backend Status
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  API Server
                </Typography>
                <Chip
                  size="small"
                  label={data ? 'Connected' : 'Disconnected'}
                  color={data ? 'success' : 'error'}
                />
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  Framework
                </Typography>
                <Typography variant="body2">FastAPI</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  Detection Model
                </Typography>
                <Typography variant="body2">YOLOv8</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  Tracking
                </Typography>
                <Typography variant="body2">ByteTrack</Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Pipeline Configuration
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  Zone Analytics
                </Typography>
                <Chip size="small" label="Enabled" color="success" />
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  Dwell Analytics
                </Typography>
                <Chip size="small" label="Enabled" color="success" />
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  POS Integration
                </Typography>
                <Chip size="small" label="Active" color="success" />
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  ReID
                </Typography>
                <Chip size="small" label="Enabled" color="success" />
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Diagnostics;
