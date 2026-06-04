import { Box, Paper, Typography, alpha } from '@mui/material';
import { TrendingUp, TrendingDown } from '@mui/icons-material';

function KPICard({ title, value, subtitle, icon, trend, trendValue, color = 'primary' }) {
  const isPositive = trend === 'up';

  return (
    <Paper
      sx={{
        p: 3,
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: (theme) => `0 8px 25px ${alpha(theme.palette[color].main, 0.25)}`,
        },
      }}
    >
      {/* Background Gradient */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          right: 0,
          width: 120,
          height: 120,
          background: (theme) =>
            `radial-gradient(circle at top right, ${alpha(theme.palette[color].main, 0.15)}, transparent 70%)`,
        }}
      />

      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <Box sx={{ flex: 1 }}>
          <Typography
            variant="caption"
            sx={{
              color: 'text.secondary',
              textTransform: 'uppercase',
              fontWeight: 600,
              letterSpacing: '0.5px',
            }}
          >
            {title}
          </Typography>

          <Typography
            variant="h3"
            sx={{
              mt: 1,
              fontWeight: 700,
              color: `${color}.main`,
              lineHeight: 1.2,
            }}
          >
            {value}
          </Typography>

          {subtitle && (
            <Typography variant="body2" sx={{ mt: 0.5, color: 'text.secondary' }}>
              {subtitle}
            </Typography>
          )}

          {trend && trendValue && (
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1.5, gap: 0.5 }}>
              {isPositive ? (
                <TrendingUp sx={{ fontSize: 18, color: 'success.main' }} />
              ) : (
                <TrendingDown sx={{ fontSize: 18, color: 'error.main' }} />
              )}
              <Typography
                variant="body2"
                sx={{
                  fontWeight: 600,
                  color: isPositive ? 'success.main' : 'error.main',
                }}
              >
                {trendValue}
              </Typography>
            </Box>
          )}
        </Box>

        {icon && (
          <Box
            sx={{
              p: 1.5,
              borderRadius: 2,
              backgroundColor: (theme) => alpha(theme.palette[color].main, 0.15),
              color: `${color}.main`,
            }}
          >
            {icon}
          </Box>
        )}
      </Box>
    </Paper>
  );
}

export default KPICard;
