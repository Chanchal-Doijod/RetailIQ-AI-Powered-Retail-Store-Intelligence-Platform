import { Box, Typography, Chip } from '@mui/material';
import { Circle as CircleIcon } from '@mui/icons-material';

function PageHeader({ title, subtitle, status }) {
  return (
    <Box sx={{ mb: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 0.5 }}>
        <Typography variant="h2" component="h1">
          {title}
        </Typography>
        {status && (
          <Chip
            size="small"
            icon={<CircleIcon sx={{ fontSize: '10px !important' }} />}
            label={status}
            color="success"
            sx={{
              fontWeight: 500,
              '& .MuiChip-icon': {
                color: 'inherit',
              },
            }}
          />
        )}
      </Box>
      {subtitle && (
        <Typography variant="body1" color="text.secondary">
          {subtitle}
        </Typography>
      )}
    </Box>
  );
}

export default PageHeader;
