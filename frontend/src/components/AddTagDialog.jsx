import React, { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Grid,
  Box,
} from "@mui/material";
import axios from "axios";

const BOJE = ["#E57373", "#64B5F6", "#81C784", "#FFD54F", "#BA68C8", "#90A4AE"];

export default function AddTagDialog({ open, onClose, onTagAdded }) {
  const [tagName, setTagName] = useState("");
  const [selectedColor, setSelectedColor] = useState(BOJE[0]);
  const [saving, setSaving] = useState(false);

  const handleSubmit = () => {
    if (!tagName.trim()) return;
    setSaving(true);

    axios
      .post("http://localhost:8000/tags", {
        name: tagName,
        color: selectedColor,
      })
      .then(() => {
        setTagName("");
        setSelectedColor(BOJE[0]);
        onTagAdded?.();
        onClose();
      })
      .catch((err) => {
        console.error("Greška prilikom snimanja taga:", err);
      })
      .finally(() => setSaving(false));
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth>
      <DialogTitle>Dodaj novi tag</DialogTitle>
      <DialogContent>
        <TextField
          label="Ime taga"
          fullWidth
          value={tagName}
          onChange={(e) => setTagName(e.target.value)}
          sx={{ marginBottom: 3, marginTop: 1 }}
        />

        <Grid container spacing={1}>
          {BOJE.map((boja, idx) => (
            <Grid item key={idx}>
              <Box
                sx={{
                  width: 32,
                  height: 32,
                  borderRadius: "50%",
                  backgroundColor: boja,
                  cursor: "pointer",
                  border: selectedColor === boja ? "3px solid black" : "1px solid #ccc",
                }}
                onClick={() => setSelectedColor(boja)}
              />
            </Grid>
          ))}
        </Grid>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Otkaži</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={saving || !tagName.trim()}
        >
          Spasi
        </Button>
      </DialogActions>
    </Dialog>
  );
}
