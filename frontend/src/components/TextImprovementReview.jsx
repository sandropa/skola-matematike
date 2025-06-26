import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  IconButton,
  Paper,
} from '@mui/material';
import { Check, X } from 'lucide-react';

export default function TextImprovementReview({ open, onClose, originalText, improvedText, onAccept, onReject }) {
  // Split texts into lines for comparison
  const originalLines = originalText.split('\n');
  const improvedLines = improvedText.split('\n');

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          minHeight: '60vh',
          maxHeight: '80vh',
        },
      }}
    >
      <DialogTitle>
        Review Changes
        <Typography variant="subtitle2" color="text.secondary">
          Review the suggested changes and choose to accept or reject them
        </Typography>
      </DialogTitle>
      <DialogContent dividers>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {originalLines.map((line, index) => {
            const improvedLine = improvedLines[index] || '';
            const hasChanges = line !== improvedLine;

            return (
              <Paper
                key={index}
                elevation={1}
                sx={{
                  p: 2,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 1,
                  bgcolor: hasChanges ? 'rgba(0, 0, 0, 0.02)' : 'transparent',
                }}
              >
                {hasChanges ? (
                  <>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography
                        variant="body2"
                        sx={{
                          textDecoration: 'line-through',
                          color: 'text.secondary',
                          flex: 1,
                        }}
                      >
                        {line}
                      </Typography>
                      <IconButton
                        size="small"
                        onClick={() => onReject(index)}
                        sx={{ color: 'error.main' }}
                      >
                        <X size={16} />
                      </IconButton>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography
                        variant="body2"
                        sx={{
                          color: 'success.main',
                          flex: 1,
                        }}
                      >
                        {improvedLine}
                      </Typography>
                      <IconButton
                        size="small"
                        onClick={() => onAccept(index)}
                        sx={{ color: 'success.main' }}
                      >
                        <Check size={16} />
                      </IconButton>
                    </Box>
                  </>
                ) : (
                  <Typography variant="body2">{line}</Typography>
                )}
              </Paper>
            );
          })}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="inherit">
          Cancel
        </Button>
        <Button
          onClick={() => {
            onAccept('all');
            onClose();
          }}
          color="success"
          variant="contained"
        >
          Accept All
        </Button>
        <Button
          onClick={() => {
            onReject('all');
            onClose();
          }}
          color="error"
          variant="outlined"
        >
          Reject All
        </Button>
      </DialogActions>
    </Dialog>
  );
} 