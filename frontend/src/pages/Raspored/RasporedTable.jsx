import React, { useState } from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, TextField, IconButton, Button, Tooltip, Box } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';

const groupNames = [
  "Grupa A1", "Grupa A2", "Grupa B", "Srednja grupa", "Napredna grupa", "Predolimpijska grupa", "Olimpijska grupa"
];

const lecturerColors = {
  "Emin Mulamimović": "rgba(37, 99, 235, 0.1)", // transparent blue
  "Amar Kurić": "rgba(37, 99, 235, 0.1)",
  "Admir Beširević": "rgba(37, 99, 235, 0.1)",
  "Adisa Bolić": "rgba(37, 99, 235, 0.1)",
  "Adi Hujić": "rgba(37, 99, 235, 0.1)",
  "Imana Alibašić": "rgba(37, 99, 235, 0.1)",
  "Sandro Paradižik": "rgba(37, 99, 235, 0.1)"
};

export default function RasporedTable({ schedule, loading }) {
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState(null);
  const [editingCell, setEditingCell] = useState(null); // { rowIdx, group, field }

  if (loading) return <div>Loading...</div>;

  let lastCycle = null;

  const handleEditToggle = () => {
    if (editMode) {
      // Save changes
      schedule.forEach((row, idx) => {
        if (editData[idx]) {
          schedule[idx] = editData[idx];
        }
      });
      setEditMode(false);
      setEditData(null);
      setEditingCell(null);
    } else {
      // Enter edit mode
      setEditMode(true);
      setEditData(schedule.map(row => JSON.parse(JSON.stringify(row))));
    }
  };

  const handleFieldChange = (rowIdx, group, field, value) => {
    setEditData(prev => {
      const newData = [...prev];
      newData[rowIdx] = {
        ...newData[rowIdx],
        groups: {
          ...newData[rowIdx].groups,
          [group]: {
            ...newData[rowIdx].groups[group],
            [field]: value
          }
        }
      };
      return newData;
    });
  };

  const handleCellDoubleClick = (rowIdx, group, field) => {
    if (!editMode) return;
    setEditingCell({ rowIdx, group, field });
  };

  const handleCellBlur = () => {
    setEditingCell(null);
  };

  const handleCellKeyDown = (e) => {
    if (e.key === 'Enter') {
      setEditingCell(null);
    }
  };

  return (
    <TableContainer component={Paper} sx={{ mt: 2, boxShadow: 'none', border: '1px solid rgba(0, 0, 0, 0.1)' }}>
      <Box sx={{ p: 1, display: 'flex', justifyContent: 'flex-end' }}>
        <IconButton onClick={handleEditToggle} size="small">
          {editMode ? <SaveIcon /> : <EditIcon />}
        </IconButton>
      </Box>
      <Table size="small" sx={{ minWidth: 1200 }}>
        <TableHead>
          <TableRow>
            <TableCell rowSpan={2} sx={{ fontWeight: 'bold', bgcolor: 'rgba(37, 99, 235, 0.05)' }}>Ciklus</TableCell>
            <TableCell rowSpan={2} sx={{ fontWeight: 'bold', bgcolor: 'rgba(37, 99, 235, 0.05)' }}>Sedmica</TableCell>
            <TableCell rowSpan={2} sx={{ fontWeight: 'bold', bgcolor: 'rgba(37, 99, 235, 0.05)' }}>O predavanju</TableCell>
            {groupNames.map(group => (
              <TableCell key={group} colSpan={1} sx={{ fontWeight: 'bold', bgcolor: 'rgba(37, 99, 235, 0.05)', textAlign: 'center' }}>{group}</TableCell>
            ))}
          </TableRow>
          <TableRow>
            {groupNames.map(group => (
              <React.Fragment key={group}></React.Fragment>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {schedule.map((row, idx) => {
            const isNewCycle = row.cycle !== lastCycle;
            lastCycle = row.cycle;
            const rowData = editMode && editData ? editData[idx] : row;
            return (
              <React.Fragment key={row.cycle + '-' + row.row}>
                {isNewCycle && idx !== 0 && (
                  <TableRow>
                    <TableCell colSpan={10} sx={{ bgcolor: 'rgba(37, 99, 235, 0.05)', height: 8, borderBottom: '1px solid rgba(37, 99, 235, 0.2)' }} />
                  </TableRow>
                )}
                {/* Tema row */}
                <TableRow 
                  sx={{ 
                    bgcolor: 'transparent',
                    height: 40,
                    '&:hover': { bgcolor: 'rgba(37, 99, 235, 0.03)' },
                    transition: 'background-color 0.2s'
                  }}
                >
                  <TableCell rowSpan={4} sx={{ fontWeight: 'bold', fontSize: 16, borderLeft: isNewCycle ? '2px solid rgba(37, 99, 235, 0.3)' : undefined }}>{row.cycle}</TableCell>
                  <TableCell rowSpan={4} sx={{ fontWeight: 'bold', fontSize: 16 }}>{row.row}</TableCell>
                  <TableCell sx={{ fontWeight: 'bold', color: '#2563eb' }}>Tema</TableCell>
                  {groupNames.map(group => (
                    <TableCell 
                      key={group} 
                      sx={{ 
                        px: 2,
                        '&:hover': { bgcolor: 'rgba(37, 99, 235, 0.05)' },
                        transition: 'background-color 0.2s'
                      }}
                    >
                      {editMode ? (
                        <TextField
                          value={rowData.groups[group]?.Tema || ""}
                          onChange={e => handleFieldChange(idx, group, "Tema", e.target.value)}
                          size="small"
                          variant="standard"
                          sx={{ '& .MuiInputBase-root': { fontSize: 'inherit' } }}
                        />
                      ) : (
                        rowData.groups[group]?.Tema || ""
                      )}
                    </TableCell>
                  ))}
                </TableRow>
                {/* Datum row */}
                <TableRow 
                  sx={{ 
                    bgcolor: 'transparent',
                    height: 36,
                    '&:hover': { bgcolor: 'rgba(37, 99, 235, 0.03)' },
                    transition: 'background-color 0.2s'
                  }}
                >
                  <TableCell sx={{ fontWeight: 'bold', color: '#2563eb' }}>Datum</TableCell>
                  {groupNames.map(group => (
                    <TableCell 
                      key={group} 
                      sx={{ 
                        px: 2,
                        '&:hover': { bgcolor: 'rgba(37, 99, 235, 0.05)' },
                        transition: 'background-color 0.2s'
                      }}
                    >
                      {editMode ? (
                        <TextField
                          value={rowData.groups[group]?.Datum || ""}
                          onChange={e => handleFieldChange(idx, group, "Datum", e.target.value)}
                          size="small"
                          variant="standard"
                          sx={{ '& .MuiInputBase-root': { fontSize: 'inherit' } }}
                        />
                      ) : (
                        rowData.groups[group]?.Datum || ""
                      )}
                    </TableCell>
                  ))}
                </TableRow>
                {/* Predavač row */}
                <TableRow 
                  sx={{ 
                    bgcolor: 'transparent',
                    height: 36,
                    '&:hover': { bgcolor: 'rgba(37, 99, 235, 0.03)' },
                    transition: 'background-color 0.2s'
                  }}
                >
                  <TableCell sx={{ fontWeight: 'bold', color: '#2563eb' }}>Predavač</TableCell>
                  {groupNames.map(group => (
                    <TableCell
                      key={group}
                      sx={{
                        px: 2,
                        bgcolor: lecturerColors[rowData.groups[group]?.Predavač] || 'transparent',
                        fontWeight: 'bold',
                        '&:hover': { bgcolor: 'rgba(37, 99, 235, 0.1)' },
                        transition: 'background-color 0.2s'
                      }}
                    >
                      {editMode ? (
                        <TextField
                          value={rowData.groups[group]?.Predavač || ""}
                          onChange={e => handleFieldChange(idx, group, "Predavač", e.target.value)}
                          size="small"
                          variant="standard"
                          sx={{ '& .MuiInputBase-root': { fontSize: 'inherit' } }}
                        />
                      ) : (
                        rowData.groups[group]?.Predavač || ""
                      )}
                    </TableCell>
                  ))}
                </TableRow>
                {/* Komentar row */}
                <TableRow 
                  sx={{ 
                    bgcolor: 'transparent',
                    height: 36,
                    '&:hover': { bgcolor: 'rgba(37, 99, 235, 0.03)' },
                    transition: 'background-color 0.2s'
                  }}
                >
                  <TableCell sx={{ fontWeight: 'bold', color: '#2563eb' }}>Komentar</TableCell>
                  {groupNames.map(group => (
                    <TableCell 
                      key={group} 
                      sx={{ 
                        px: 2,
                        '&:hover': { bgcolor: 'rgba(37, 99, 235, 0.05)' },
                        transition: 'background-color 0.2s'
                      }}
                    >
                      {editMode ? (
                        <TextField
                          value={rowData.groups[group]?.comments || ""}
                          onChange={e => handleFieldChange(idx, group, "comments", e.target.value)}
                          size="small"
                          variant="standard"
                          sx={{ '& .MuiInputBase-root': { fontSize: 'inherit' } }}
                        />
                      ) : (
                        rowData.groups[group]?.comments || ""
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              </React.Fragment>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );
} 