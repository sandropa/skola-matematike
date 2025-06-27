import React from 'react';
import { Box, Typography, Button, Paper, Container } from '@mui/material';
import { Home, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <Container maxWidth="md">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: '#f5f5f5'
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            textAlign: 'center',
            borderRadius: 2,
            maxWidth: 500,
            width: '100%'
          }}
        >
          <Typography
            variant="h1"
            sx={{
              fontSize: '6rem',
              fontWeight: 'bold',
              color: 'primary.main',
              mb: 2
            }}
          >
            404
          </Typography>
          
          <Typography
            variant="h4"
            sx={{
              mb: 2,
              color: 'text.primary'
            }}
          >
            Stranica nije pronađena
          </Typography>
          
          <Typography
            variant="body1"
            sx={{
              mb: 4,
              color: 'text.secondary',
              lineHeight: 1.6
            }}
          >
            Stranica koju tražite ne postoji ili je premještena. 
            Provjerite URL adresu ili se vratite na početnu stranicu.
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              startIcon={<Home size={20} />}
              onClick={() => navigate('/pocetna')}
              sx={{ minWidth: 140 }}
            >
              Početna stranica
            </Button>
            
            <Button
              variant="outlined"
              startIcon={<ArrowLeft size={20} />}
              onClick={() => navigate(-1)}
              sx={{ minWidth: 140 }}
            >
              Nazad
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
} 