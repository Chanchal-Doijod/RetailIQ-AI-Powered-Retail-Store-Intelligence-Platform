import { Box, Typography, alpha } from '@mui/material';

function StatusIndicator({ label, value, status = 'success', icon }) {
  const statusColors = {
    success: 'success.main',
    warning: 'warning.main',
    error: 'error.main',
    info: 'info.main',
  };

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 2,
        p: 2,
        borderRadius: 2,
        backgroundColor: (theme) => alpha(theme.palette[status].main, 0.08),
        border: (theme) => `1px solid ${alpha(theme.palette[status].main, 0.2)}`,
      }}
    >
      {icon && (
        <Box
          sx={{
            color: statusColors[status],
            display: 'flex',
            alignItems: 'center',
          }}
        >
          {icon}
        </Box>
      )}
      <Box sx={{ flex: 1 }}>
        <Typography variant="caption" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="h6" sx={{ color: statusColors[status] }}>
          {value}
        </Typography>
      </Box>
    </Box>
  );
}

export default StatusIndicator;
