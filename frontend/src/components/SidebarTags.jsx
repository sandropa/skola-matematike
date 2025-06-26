import React, { useEffect, useState } from "react";
import axios from "axios";
import { Chip, Stack, Typography, Divider, Box } from "@mui/material";

function Sidebar({ onTagClick }) {
  const [tagovi, setTagovi] = useState([]);
  const fetchTags = () => {
  axios
    .get("http://localhost:8000/tags")
    .then(res => setTagovi(res.data))
    .catch(err => {
      console.error("Greška prilikom dohvaćanja tagova:", err);
    });
};

  useEffect(() => {
  fetchTags();
}, []);

  return (
    <Box sx={{ width: 250, padding: 2 }}>
      <Typography variant="h6" gutterBottom>
        Tagovi
      </Typography>

      <Divider sx={{ mb: 2 }} />

      <Stack direction="column" spacing={1}>
        {tagovi.map(tag => (
          <Chip
            key={tag.id}
            label={tag.name}
            onClick={() => onTagClick(tag.id)}
            sx={{
              backgroundColor: tag.color,
              color: "#fff",
              fontWeight: "bold",
              width: "fit-content",
              
              cursor: "pointer"
            }}
          />
        ))}
      </Stack>
    </Box>
  );
}

export default Sidebar;
