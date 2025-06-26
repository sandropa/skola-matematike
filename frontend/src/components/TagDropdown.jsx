import React, { useEffect, useState } from "react";
import axios from "axios";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Autocomplete,
  TextField,
  Chip,
  Button,
  CircularProgress
} from "@mui/material";

export default function TagDropdown({ open, onClose, lectureId, onSaved }) {
  const [allTags, setAllTags] = useState([]);
  const [selectedTags, setSelectedTags] = useState([]);
  const [loading, setLoading] = useState(false);

  
  useEffect(() => {
    if (open) {
      axios.get("http://localhost:8000/tags")
        .then(res => setAllTags(res.data));

      axios.get(`http://localhost:8000/lecture-tags/${lectureId}`)
        .then(res => setSelectedTags(res.data)); // očekuješ listu stringova
    }
  }, [open, lectureId]);

  const handleSave = () => {
    setLoading(true);
    axios.patch(`http://localhost:8000/lecture-tags/${lectureId}`, selectedTags)
      .then(() => {
        setLoading(false);
        onSaved();
        onClose();
      });
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth>
      <DialogTitle>Dodijeli tagove</DialogTitle>
      <DialogContent>
        <Autocomplete
          multiple
          options={allTags.map(t => t.name)}
          value={selectedTags}
          onChange={(e, newValue) => setSelectedTags(newValue)}
          renderTags={(value, getTagProps) =>
            value.map((option, index) => (
              <Chip label={option} {...getTagProps({ index })} key={index} />
            ))
          }
          renderInput={(params) => <TextField {...params} label="Tagovi" />}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>Otkaži</Button>
        <Button variant="contained" onClick={handleSave} disabled={loading}>
          {loading ? <CircularProgress size={20} /> : "Spasi"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
