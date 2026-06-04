import { Paper, Typography, Box, alpha } from '@mui/material';
import {
  Store,
  RemoveRedEye,
  ShoppingCart,
  ArrowDownward,
} from '@mui/icons-material';

function ConversionFunnel({ data }) {
  const funnelSteps = [
    {
      label: 'Store Entries',
      value: data?.stages?.entered_store || 0,
      icon: <Store />,
      color: '#6366f1',
    },
    {
      label: 'Zone Browsing',
      value: data?.stages?.browsed_zone || 0,
      icon: <RemoveRedEye />,
      color: '#8b5cf6',
    },
    {
      label: 'Reached Billing',
      value: data?.stages?.reached_billing || 0,
      icon: <ShoppingCart />,
      color: '#f59e0b',
    },
    {
      label: 'Converted',
      value: data?.stages?.converted || 0,
      icon: <ShoppingCart />,
      color: '#10b981',
    },
  ];

  const maxValue = Math.max(...funnelSteps.map((s) => s.value), 1);

  const entryToBrowse =
    data?.stages?.entered_store > 0
      ? (
          (data.stages.browsed_zone / data.stages.entered_store) *
          100
        ).toFixed(0)
      : 0;

  const browseToBilling =
    data?.stages?.browsed_zone > 0
      ? (
          (data.stages.reached_billing / data.stages.browsed_zone) *
          100
        ).toFixed(0)
      : 0;

  const billingToConversion =
    data?.stages?.reached_billing > 0
      ? (
          (data.stages.converted / data.stages.reached_billing) *
          100
        ).toFixed(0)
      : 0;

  return (
    <Paper sx={{ p: 3, height: '100%' }}>
      <Typography variant="h5" sx={{ mb: 3 }}>
        Conversion Funnel
      </Typography>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {funnelSteps.map((step, index) => (
          <Box key={step.label}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                mb: 1,
              }}
            >
              <Box
                sx={{
                  p: 1,
                  borderRadius: 1.5,
                  backgroundColor: alpha(step.color, 0.15),
                  color: step.color,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {step.icon}
              </Box>

              <Box sx={{ flex: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  {step.label}
                </Typography>

                <Typography
                  variant="h4"
                  sx={{
                    color: step.color,
                    fontWeight: 700,
                  }}
                >
                  {step.value.toLocaleString()}
                </Typography>
              </Box>
            </Box>

            <Box
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: alpha(step.color, 0.1),
                overflow: 'hidden',
              }}
            >
              <Box
                sx={{
                  height: '100%',
                  width: `${(step.value / maxValue) * 100}%`,
                  backgroundColor: step.color,
                  borderRadius: 4,
                  transition: 'width 0.5s ease-in-out',
                }}
              />
            </Box>

            {index < funnelSteps.length - 1 && (
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'center',
                  py: 1,
                  color: 'text.secondary',
                }}
              >
                <ArrowDownward fontSize="small" />
              </Box>
            )}
          </Box>
        ))}
      </Box>

      <Box
        sx={{
          mt: 3,
          pt: 2,
          borderTop: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{
            mb: 1,
            display: 'block',
          }}
        >
          Conversion Rates
        </Typography>

        <Box sx={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Entry → Browse
            </Typography>
            <Typography variant="h6" color="primary.main">
              {entryToBrowse}%
            </Typography>
          </Box>

          <Box>
            <Typography variant="body2" color="text.secondary">
              Browse → Billing
            </Typography>
            <Typography variant="h6" color="warning.main">
              {browseToBilling}%
            </Typography>
          </Box>

          <Box>
            <Typography variant="body2" color="text.secondary">
              Billing → Purchase
            </Typography>
            <Typography variant="h6" color="success.main">
              {billingToConversion}%
            </Typography>
          </Box>
        </Box>
      </Box>
    </Paper>
  );
}

export default ConversionFunnel;