import React, { useState } from 'react';
import { Popover, Box, Typography, TextField, Button } from '@mui/material';

export default function CommentPopover({ open, onClose, comments }) {
  const [newComment, setNewComment] = useState('');

  const handleAddComment = () => {
    // TODO: Save comment to backend
    setNewComment('');
    onClose();
  };

  return (
    <Popover open={open} onClose={onClose} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
      <Box sx={{ p: 2, minWidth: 250 }}>
        <Typography variant="subtitle1">Komentari</Typography>
        <Box sx={{ mb: 2 }}>{comments || 'Nema komentara.'}</Box>
        <TextField
          label="Novi komentar"
          value={newComment}
          onChange={e => setNewComment(e.target.value)}
          fullWidth
          multiline
          rows={2}
        />
        <Button onClick={handleAddComment} sx={{ mt: 1 }} variant="contained" size="small">Dodaj</Button>
      </Box>
    </Popover>
  );
} 