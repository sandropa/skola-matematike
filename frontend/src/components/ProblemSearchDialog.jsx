import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  CircularProgress,
  Alert,
  IconButton,
  Drawer,
  useMediaQuery
} from '@mui/material';
import { Search, Plus, FileText, FileDown, User, Settings, Copy, Check } from 'lucide-react';
import { User as UserIcon, Settings as SettingsIcon } from 'lucide-react';
import LocalOfferIcon from '@mui/icons-material/LocalOffer';
import MenuIcon from "@mui/icons-material/Menu";

const API_BASE_URL = "http://localhost:8000";

export default function ProblemSearchDialog({ open, onClose, onProblemSelect }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copiedId, setCopiedId] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const isMobile = useMediaQuery('(max-width:900px)');

  const handleDrawerOpen = () => setDrawerOpen(true);
  const handleDrawerClose = () => setDrawerOpen(false);

  const handleSearch = async () => {
    if (!searchTerm.trim()) {
      // Load all problems when search is empty
      setLoading(true);
      try {
        const response = await fetch(`${API_BASE_URL}/problems/with-lecture`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setProblems(data);
      } catch (err) {
        console.error('Error loading problems:', err);
        setError('Greška pri učitavanju zadataka');
      } finally {
        setLoading(false);
      }
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/problems/search/${encodeURIComponent(searchTerm.trim())}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setProblems(data);
    } catch (err) {
      console.error('Error searching problems:', err);
      setError('Greška pri pretraživanju zadataka');
    } finally {
      setLoading(false);
    }
  };

  const handleProblemSelect = (problem) => {
    onProblemSelect(problem);
    onClose();
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 1000);
    });
  };

  const filtriraniZadaci = problems.filter((problem) =>
    problem.latex_text.toLowerCase().includes(searchTerm.toLowerCase())
  );

  useEffect(() => {
    if (open) {
      setSearchTerm('');
      setProblems([]);
      setError(null);
      // Load all problems when dialog opens
      handleSearch();
    }
  }, [open]);

  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      maxWidth="xl"
      fullWidth
      PaperProps={{
        sx: { 
          height: '90vh',
          maxHeight: '90vh',
          borderRadius: 2
        }
      }}
    >
      <DialogTitle sx={{ p: 0, m: 0 }}>
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          p: 2,
          borderBottom: '1px solid #e0e0e0',
          bgcolor: '#f7f9fb'
        }}>
          <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#1e6ca6' }}>
            Dodaj zadatak
          </Typography>
          <Button onClick={onClose} variant="outlined" size="small">
            Zatvori
          </Button>
        </Box>
      </DialogTitle>
      
      <DialogContent sx={{ p: 0, m: 0 }}>
        <div style={{
          display: 'flex',
          flexDirection: 'row',
          height: 'calc(90vh - 80px)'
        }}>
          {/* Hamburger dugme za male ekrane */}
          {isMobile && !drawerOpen && (
            <IconButton
              color="primary"
              aria-label="open sidebar"
              onClick={handleDrawerOpen}
              sx={{
                position: "fixed",
                top: 72,
                left: 16,
                zIndex: 2000,
                background: "white",
                boxShadow: 1,
                borderRadius: 2
              }}
            >
              <MenuIcon />
            </IconButton>
          )}

          {/* Drawer za sidebar */}
          <Drawer
            anchor="left"
            open={drawerOpen}
            onClose={handleDrawerClose}
            sx={{ display: { md: "none" } }}
          >
            <div style={{ width: 260, padding: 24 }}>
              <div style={{
                display: 'flex',
                gap: '1.2rem',
                paddingTop: '2rem',
                justifyContent: 'center'
              }}>
                <UserIcon style={{
                  width: '28px',
                  height: '28px',
                  color: '#666',
                  cursor: 'pointer'
                }} />
                <SettingsIcon style={{
                  width: '28px',
                  height: '28px',
                  color: '#666',
                  cursor: 'pointer'
                }} />
              </div>
            </div>
          </Drawer>


          {/* Main content */}
          <div style={{
            flex: 1,
            padding: '2rem',
            overflowY: 'auto',
            backgroundColor: '#f7f9fb'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '1rem'
            }}>
              <div style={{
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                maxWidth: '400px',
                width: '100%'
              }}>
                <Search style={{
                  position: 'absolute',
                  left: '12px',
                  pointerEvents: 'none',
                  color: '#888',
                  width: '18px',
                  height: '18px'
                }} />
                <input
                  type="text"
                  placeholder="Pretraga zadataka..."
                  style={{
                    padding: '12px 12px 12px 40px',
                    border: '1px solid #ccc',
                    borderRadius: '10px',
                    fontSize: '15px',
                    width: '100%',
                    maxWidth: '400px',
                    backgroundColor: 'white'
                  }}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={handleKeyPress}
                />
              </div>
            </div>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            <div style={{
              width: '100%',
              overflowX: 'auto',
              backgroundColor: 'transparent',
              paddingBottom: '1px'
            }}>
              <table style={{
                width: '100%',
                borderCollapse: 'collapse',
                minWidth: '600px',
                marginTop: '1rem',
                backgroundColor: '#fff',
                border: '1px solid #e0e0e0',
                borderRadius: '12px',
                overflow: 'hidden'
              }}>
                <thead>
                  <tr>
                    <th style={{
                      padding: '0.75rem 1rem',
                      textAlign: 'left',
                      fontSize: '15px',
                      verticalAlign: 'middle',
                      backgroundColor: '#f0f2f5',
                      color: '#1e6ca6',
                      fontWeight: '600',
                      whiteSpace: 'nowrap',
                      borderBottom: '1px solid #e0e0e0'
                    }}>Tekst zadatka</th>
                    <th style={{
                      padding: '0.75rem 1rem',
                      textAlign: 'left',
                      fontSize: '15px',
                      verticalAlign: 'middle',
                      backgroundColor: '#f0f2f5',
                      color: '#1e6ca6',
                      fontWeight: '600',
                      whiteSpace: 'nowrap',
                      borderBottom: '1px solid #e0e0e0'
                    }}>Kategorija</th>
                    <th style={{
                      padding: '0.75rem 1rem',
                      textAlign: 'left',
                      fontSize: '15px',
                      verticalAlign: 'middle',
                      backgroundColor: '#f0f2f5',
                      color: '#1e6ca6',
                      fontWeight: '600',
                      whiteSpace: 'nowrap',
                      borderBottom: '1px solid #e0e0e0'
                    }}>Predavanje</th>
                    <th style={{
                      padding: '0.75rem 1rem',
                      textAlign: 'left',
                      fontSize: '15px',
                      verticalAlign: 'middle',
                      backgroundColor: '#f0f2f5',
                      color: '#1e6ca6',
                      fontWeight: '600',
                      whiteSpace: 'nowrap',
                      borderBottom: '1px solid #e0e0e0'
                    }}>Akcije</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={4} style={{ textAlign: 'center', padding: '2rem' }}>
                        <CircularProgress />
                        <Typography sx={{ mt: 1 }}>Učitavanje zadataka...</Typography>
                      </td>
                    </tr>
                  ) : filtriraniZadaci.length === 0 ? (
                    <tr>
                      <td colSpan={4} style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
                        {searchTerm ? `Nema rezultata za "${searchTerm}"` : 'Nema dostupnih zadataka'}
                      </td>
                    </tr>
                  ) : (
                    filtriraniZadaci.map((problem, index) => (
                      <tr key={index} style={{
                        borderBottom: '1px solid #e0e0e0'
                      }}>
                        <td style={{
                          padding: '0.75rem 1rem',
                          textAlign: 'left',
                          fontSize: '15px',
                          verticalAlign: 'middle',
                          fontFamily: 'monospace',
                          fontSize: '14px'
                        }}>
                          {problem.latex_text}
                        </td>
                        <td style={{
                          padding: '0.75rem 1rem',
                          textAlign: 'left',
                          fontSize: '15px',
                          verticalAlign: 'middle'
                        }}>
                          {problem.category || 'N/A'}
                        </td>
                        <td style={{
                          padding: '0.75rem 1rem',
                          textAlign: 'left',
                          fontSize: '15px',
                          verticalAlign: 'middle'
                        }}>
                          {problem.lecture_title || "Nepoznato"}
                        </td>
                        <td style={{
                          padding: '0.75rem 1rem',
                          textAlign: 'left',
                          fontSize: '15px',
                          verticalAlign: 'middle'
                        }}>
                          <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '1rem'
                          }}>
                            <button
                              type="button"
                              onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                copyToClipboard(problem.latex_text, problem.id);
                              }}
                              style={{
                                background: 'transparent',
                                border: 'none',
                                cursor: 'pointer',
                                padding: '4px',
                                borderRadius: '4px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                              }}
                              title="Kopiraj"
                            >
                              {copiedId === problem.id ? (
                                <Check size={18} strokeWidth={2} />
                              ) : (
                                <Copy size={18} strokeWidth={2} />
                              )}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
} 