import React, { useState } from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, TextField, IconButton, Button, Tooltip } from '@mui/material';
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
  const [editIdx, setEditIdx] = useState(null);
  const [editRow, setEditRow] = useState(null);
  const [editingCell, setEditingCell] = useState(null); // { rowIdx, group, field }

  if (loading) return <div>Loading...</div>;

  let lastCycle = null;

  const handleEdit = (idx, row) => {
    setEditIdx(idx);
    setEditRow(JSON.parse(JSON.stringify(row))); // deep copy
  };

  const handleSave = (idx) => {
    schedule[idx] = editRow;
    setEditIdx(null);
    setEditRow(null);
    setEditingCell(null);
  };

  const handleFieldChange = (group, field, value) => {
    setEditRow({
      ...editRow,
      groups: {
        ...editRow.groups,
        [group]: {
          ...editRow.groups[group],
          [field]: value
        }
      }
    });
  };

  const handleCellDoubleClick = (rowIdx, group, field) => {
    setEditIdx(rowIdx);
    setEditRow(JSON.parse(JSON.stringify(schedule[rowIdx])));
    setEditingCell({ rowIdx, group, field });
  };

  const handleCellBlur = () => {
    setEditingCell(null);
  };

  const handleCellKeyDown = (e, idx) => {
    if (e.key === 'Enter') {
      handleSave(idx);
    }
  };

  return (
    <TableContainer component={Paper} sx={{ mt: 2, boxShadow: 'none', border: '1px solid rgba(0, 0, 0, 0.1)' }}>
      <Table size="small" sx={{ minWidth: 1200 }}>
        <TableHead>
          <TableRow>
            <TableCell rowSpan={2} sx={{ fontWeight: 'bold', bgcolor: 'rgba(37, 99, 235, 0.05)' }}>Ciklus</TableCell>
            <TableCell rowSpan={2} sx={{ fontWeight: 'bold', bgcolor: 'rgba(37, 99, 235, 0.05)' }}>Sedmica</TableCell>
            <TableCell rowSpan={2} sx={{ fontWeight: 'bold', bgcolor: 'rgba(37, 99, 235, 0.05)' }}>O predavanju</TableCell>
            {groupNames.map(group => (
              <TableCell key={group} colSpan={1} sx={{ fontWeight: 'bold', bgcolor: 'rgba(37, 99, 235, 0.05)', textAlign: 'center' }}>{group}</TableCell>
            ))}
            <TableCell rowSpan={2} sx={{ fontWeight: 'bold', bgcolor: 'rgba(37, 99, 235, 0.05)' }}></TableCell>
          </TableRow>
          <TableRow>
            {groupNames.map(group => (
              <React.Fragment key={group}></React.Fragment>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {schedule.map((row, idx) => {
            const isEditing = editIdx === idx;
            const isNewCycle = row.cycle !== lastCycle;
            lastCycle = row.cycle;
            const rowData = isEditing ? editRow : row;
            return (
              <React.Fragment key={row.cycle + '-' + row.row}>
                {isNewCycle && idx !== 0 && (
                  <TableRow>
                    <TableCell colSpan={11} sx={{ bgcolor: 'rgba(37, 99, 235, 0.05)', height: 8, borderBottom: '1px solid rgba(37, 99, 235, 0.2)' }} />
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
                      onDoubleClick={() => handleCellDoubleClick(idx, group, 'Tema')}
                    >
                      {editingCell && editingCell.rowIdx === idx && editingCell.group === group && editingCell.field === 'Tema' ? (
                        <TextField
                          autoFocus
                          value={rowData.groups[group]?.Tema || ""}
                          onChange={e => handleFieldChange(group, "Tema", e.target.value)}
                          size="small"
                          variant="standard"
                          onBlur={handleCellBlur}
                          onKeyDown={e => handleCellKeyDown(e, idx)}
                          sx={{ '& .MuiInputBase-root': { fontSize: 'inherit' } }}
                        />
                      ) : (
                        rowData.groups[group]?.Tema || ""
                      )}
                    </TableCell>
                  ))}
                  <TableCell rowSpan={4}>
                    {isEditing ? (
                      <IconButton onClick={() => handleSave(idx)} size="small"><SaveIcon /></IconButton>
                    ) : (
                      <IconButton onClick={() => handleEdit(idx, row)} size="small"><EditIcon /></IconButton>
                    )}
                  </TableCell>
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
                      onDoubleClick={() => handleCellDoubleClick(idx, group, 'Datum')}
                    >
                      {editingCell && editingCell.rowIdx === idx && editingCell.group === group && editingCell.field === 'Datum' ? (
                        <TextField
                          autoFocus
                          value={rowData.groups[group]?.Datum || ""}
                          onChange={e => handleFieldChange(group, "Datum", e.target.value)}
                          size="small"
                          variant="standard"
                          onBlur={handleCellBlur}
                          onKeyDown={e => handleCellKeyDown(e, idx)}
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
                      onDoubleClick={() => handleCellDoubleClick(idx, group, 'Predavač')}
                    >
                      {editingCell && editingCell.rowIdx === idx && editingCell.group === group && editingCell.field === 'Predavač' ? (
                        <TextField
                          autoFocus
                          value={rowData.groups[group]?.Predavač || ""}
                          onChange={e => handleFieldChange(group, "Predavač", e.target.value)}
                          size="small"
                          variant="standard"
                          onBlur={handleCellBlur}
                          onKeyDown={e => handleCellKeyDown(e, idx)}
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
                      onDoubleClick={() => handleCellDoubleClick(idx, group, 'comments')}
                    >
                      {editingCell && editingCell.rowIdx === idx && editingCell.group === group && editingCell.field === 'comments' ? (
                        <TextField
                          autoFocus
                          value={rowData.groups[group]?.comments || ""}
                          onChange={e => handleFieldChange(group, "comments", e.target.value)}
                          size="small"
                          variant="standard"
                          onBlur={handleCellBlur}
                          onKeyDown={e => handleCellKeyDown(e, idx)}
                          sx={{ '& .MuiInputBase-root': { fontSize: 'inherit' } }}
                        />
                      ) : (
                        <Tooltip 
                          title={
                            <div style={{ 
                              padding: '8px 0',
                              lineHeight: '1.5',
                              textAlign: 'left'
                            }}>
                              {rowData.groups[group]?.comments || ""}
                            </div>
                          }
                          arrow
                          placement="top"
                          componentsProps={{
                            tooltip: {
                              sx: {
                                bgcolor: 'white',
                                color: '#1e293b',
                                fontSize: '0.95rem',
                                padding: '16px',
                                maxWidth: '500px',
                                whiteSpace: 'pre-wrap',
                                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
                                borderRadius: '8px',
                                border: '1px solid rgba(37, 99, 235, 0.1)',
                                '& .MuiTooltip-arrow': {
                                  color: 'white'
                                }
                              }
                            }
                          }}
                        >
                          <span style={{ 
                            cursor: 'pointer',
                            display: 'inline-block',
                            maxWidth: '200px',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}>
                            {rowData.groups[group]?.comments || ""}
                          </span>
                        </Tooltip>
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