import React, { useState } from 'react';
import { TableCell, IconButton, Tooltip, TextField, Button } from '@mui/material';
import CommentPopover from './CommentPopover';
import LinkIcon from '@mui/icons-material/Link';
import EditIcon from '@mui/icons-material/Edit';

export default function RasporedCell({ entry }) {
  const [editMode, setEditMode] = useState(false);
  const [localEntry, setLocalEntry] = useState(entry);
  const [commentOpen, setCommentOpen] = useState(false);

  const handleEdit = () => setEditMode(true);
  const handleSave = () => {
    // TODO: Save to backend
    setEditMode(false);
  };

  return (
    <>
      <TableCell>
        {editMode ? (
          <TextField value={localEntry.date || ''} onChange={e => setLocalEntry({ ...localEntry, date: e.target.value })} size="small" />
        ) : (
          localEntry.date
        )}
      </TableCell>
      <TableCell>
        {editMode ? (
          <TextField value={localEntry.topic || ''} onChange={e => setLocalEntry({ ...localEntry, topic: e.target.value })} size="small" />
        ) : (
          localEntry.topic
        )}
      </TableCell>
      <TableCell>
        {editMode ? (
          <TextField value={localEntry.lecturer || ''} onChange={e => setLocalEntry({ ...localEntry, lecturer: e.target.value })} size="small" />
        ) : (
          localEntry.lecturer
        )}
      </TableCell>
      <TableCell>
        <Tooltip title="Komentari">
          <IconButton onClick={() => setCommentOpen(true)}>
            💬
          </IconButton>
        </Tooltip>
        <CommentPopover open={commentOpen} onClose={() => setCommentOpen(false)} comments={localEntry.comments} />
      </TableCell>
      <TableCell>
        {localEntry.problemset_id && (
          <Tooltip title="Otvori problemset">
            <IconButton href={`/editor/${localEntry.problemset_id}`}>
              <LinkIcon />
            </IconButton>
          </Tooltip>
        )}
        <Tooltip title="Uredi">
          <IconButton onClick={handleEdit}>
            <EditIcon />
          </IconButton>
        </Tooltip>
        {editMode && (
          <Button onClick={handleSave} size="small">Spremi</Button>
        )}
      </TableCell>
    </>
  );
} 