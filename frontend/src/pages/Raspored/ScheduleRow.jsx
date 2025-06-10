import React from 'react';
import { TableRow, TableCell, TextField, IconButton, Tooltip } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';

const groupNames = [
  "Grupa A1", "Grupa A2", "Grupa B", "Srednja grupa", "Napredna grupa", "Predolimpijska grupa", "Olimpijska grupa"
];

const lecturerColors = {
  "Emin Mulamimović": "rgba(37, 99, 235, 0.1)",
  "Amar Kurić": "rgba(37, 99, 235, 0.1)",
  "Admir Beširević": "rgba(37, 99, 235, 0.1)",
  "Adisa Bolić": "rgba(37, 99, 235, 0.1)",
  "Adi Hujić": "rgba(37, 99, 235, 0.1)",
  "Imana Alibašić": "rgba(37, 99, 235, 0.1)",
  "Sandro Paradižik": "rgba(37, 99, 235, 0.1)"
};

const ScheduleRow = React.memo(({ rowData, isEditing, isNewCycle, onEdit, onSave, onFieldChange }) => {
  const handleFieldChange = (group, field, value) => {
    onFieldChange(group, field, value);
  };

  return (
    <React.Fragment>
      {isNewCycle && (
        <TableRow>
          <TableCell colSpan={11} sx={{ bgcolor: 'rgba(37, 99, 235, 0.05)', height: 8, borderBottom: '1px solid rgba(37, 99, 235, 0.2)' }} />
        </TableRow>
      )}
      {/* Tema row */}
      <TableRow sx={{ '&:hover': { bgcolor: 'rgba(37, 99, 235, 0.03)' } }}>
        <TableCell rowSpan={4} sx={{ fontWeight: 'bold', fontSize: 16, borderLeft: isNewCycle ? '2px solid rgba(37, 99, 235, 0.3)' : undefined }}>{rowData.cycle}</TableCell>
        <TableCell rowSpan={4} sx={{ fontWeight: 'bold', fontSize: 16 }}>{rowData.row}</TableCell>
        <TableCell sx={{ fontWeight: 'bold', color: '#2563eb' }}>Tema</TableCell>
        {groupNames.map(group => (
          <TableCell key={group} sx={{ px: 2, '&:hover': { bgcolor: 'rgba(37, 99, 235, 0.05)' } }}>
            {isEditing ? (
              <TextField
                value={rowData.groups[group]?.Tema || ""}
                onChange={e => handleFieldChange(group, "Tema", e.target.value)}
                size="small" variant="standard" InputProps={{ disableUnderline: true }}
                sx={{ '& .MuiInputBase-root': { fontSize: 'inherit' } }}
              />
            ) : ( rowData.groups[group]?.Tema || "" )}
          </TableCell>
        ))}
        <TableCell rowSpan={4}>
          {isEditing ? (
            <IconButton onClick={onSave} size="small"><SaveIcon /></IconButton>
          ) : (
            <IconButton onClick={onEdit} size="small"><EditIcon /></IconButton>
          )}
        </TableCell>
      </TableRow>
      {/* Datum row */}
      <TableRow sx={{ '&:hover': { bgcolor: 'rgba(37, 99, 235, 0.03)' } }}>
        <TableCell sx={{ fontWeight: 'bold', color: '#2563eb' }}>Datum</TableCell>
        {groupNames.map(group => (
          <TableCell key={group} sx={{ px: 2, '&:hover': { bgcolor: 'rgba(37, 99, 235, 0.05)' } }}>
            {isEditing ? (
              <TextField
                value={rowData.groups[group]?.Datum || ""}
                onChange={e => handleFieldChange(group, "Datum", e.target.value)}
                size="small" variant="standard" InputProps={{ disableUnderline: true }}
                sx={{ '& .MuiInputBase-root': { fontSize: 'inherit' } }}
              />
            ) : ( rowData.groups[group]?.Datum || "" )}
          </TableCell>
        ))}
      </TableRow>
      {/* Predavač row */}
      <TableRow sx={{ '&:hover': { bgcolor: 'rgba(37, 99, 235, 0.03)' } }}>
        <TableCell sx={{ fontWeight: 'bold', color: '#2563eb' }}>Predavač</TableCell>
        {groupNames.map(group => (
          <TableCell key={group} sx={{ px: 2, bgcolor: lecturerColors[rowData.groups[group]?.Predavač] || 'transparent', fontWeight: 'bold', '&:hover': { bgcolor: 'rgba(37, 99, 235, 0.1)' } }}>
            {isEditing ? (
              <TextField
                value={rowData.groups[group]?.Predavač || ""}
                onChange={e => handleFieldChange(group, "Predavač", e.target.value)}
                size="small" variant="standard" InputProps={{ disableUnderline: true }}
                sx={{ '& .MuiInputBase-root': { fontSize: 'inherit' } }}
              />
            ) : ( rowData.groups[group]?.Predavač || "" )}
          </TableCell>
        ))}
      </TableRow>
      {/* Komentar row */}
      <TableRow sx={{ '&:hover': { bgcolor: 'rgba(37, 99, 235, 0.03)' } }}>
        <TableCell sx={{ fontWeight: 'bold', color: '#2563eb' }}>Komentar</TableCell>
        {groupNames.map(group => (
          <TableCell key={group} sx={{ px: 2, '&:hover': { bgcolor: 'rgba(37, 99, 235, 0.05)' } }}>
            {isEditing ? (
              <TextField
                value={rowData.groups[group]?.comments || ""}
                onChange={e => handleFieldChange(group, "comments", e.target.value)}
                size="small" variant="standard" InputProps={{ disableUnderline: true }}
                sx={{ '& .MuiInputBase-root': { fontSize: 'inherit' } }}
              />
            ) : (
              <Tooltip title={<div style={{ padding: '8px 0', lineHeight: '1.5', textAlign: 'left' }}>{rowData.groups[group]?.comments || ""}</div>} arrow placement="top" componentsProps={{ tooltip: { sx: { bgcolor: 'white', color: '#1e293b', fontSize: '0.95rem', padding: '16px', maxWidth: '500px', whiteSpace: 'pre-wrap', boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)', borderRadius: '8px', border: '1px solid rgba(37, 99, 235, 0.1)', '& .MuiTooltip-arrow': { color: 'white' } } } }}>
                <span style={{ cursor: 'pointer', display: 'inline-block', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {rowData.groups[group]?.comments || ""}
                </span>
              </Tooltip>
            )}
          </TableCell>
        ))}
      </TableRow>
    </React.Fragment>
  );
});

export default ScheduleRow; 